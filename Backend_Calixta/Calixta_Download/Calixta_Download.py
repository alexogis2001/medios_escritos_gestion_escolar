from datetime import datetime, timedelta
import html
import os
import re
import time
import uuid
import zipfile
import requests

# Credenciales (puedes usar variables de entorno o ponerlas aquí localmente)
USUARIO = os.getenv("CALIXTA_USER", "Alexis-Garcia")
PASSWORD = os.getenv("CALIXTA_PASS", "Alexis-Garcia123")

BASE_URL = "https://utelvars.calixtachat.com"
CARPETA_DESCARGAS = r"C:\Users\alexg\Downloads\medios_escritos_gestion_escolar-main\Backend_Calixta\Calixta_Download"


def obtener_fechas_dia_vencido():
    """Devuelve (primer_dia_mes, ayer) en formato YYYY-MM-DD."""
    hoy = datetime.now()
    ayer = hoy - timedelta(days=1)
    primer_dia_mes = ayer.replace(day=1)
    return primer_dia_mes.strftime("%Y-%m-%d"), ayer.strftime("%Y-%m-%d")


def iniciar_sesion():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Origin": BASE_URL,
    })

    resp_login_page = session.get(f"{BASE_URL}/login")
    match_token = re.search(
        r'name="_token"\s+value="([^"]+)"', resp_login_page.text
    ) or re.search(
        r'meta name="csrf-token" content="([^"]+)"', resp_login_page.text
    )
    csrf_login = match_token.group(1) if match_token else ""

    session.post(
        f"{BASE_URL}/login",
        data={
            "_token": csrf_login,
            "username": USUARIO,
            "email": USUARIO,
            "password": PASSWORD,
        },
    )

    resp_panel = session.get(f"{BASE_URL}/panel/reports")
    if "/login" in resp_panel.url:
        raise RuntimeError(
            "No se pudo iniciar sesión. Verifica tus credenciales."
        )

    match_csrf = re.search(
        r'meta name="csrf-token" content="([^"]+)"', resp_panel.text
    )
    csrf_token = match_csrf.group(1) if match_csrf else ""

    # Detectar automáticamente el value interno de "Respaldos de mensajes"
    match_gen = re.search(
        r'value="([^"]+)"[^>]*>\s*Respaldos de mensajes', resp_panel.text
    )
    if not match_gen:
        match_gen = re.search(r'"(roz_messages[^"]*)"', resp_panel.text)
    gen_mensajes = match_gen.group(1) if match_gen else "roz_messages"

    return session, csrf_token, gen_mensajes


def extraer_y_unificar_csv(ruta_zip, ruta_csv_final):
    """Extrae todos los CSVs del ZIP y los une en un solo CSV sin repetir encabezados."""
    if not zipfile.is_zipfile(ruta_zip):
        os.replace(ruta_zip, ruta_csv_final)
        return 1

    carpeta_temp = ruta_zip + "_temp"
    os.makedirs(carpeta_temp, exist_ok=True)

    with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
        zip_ref.extractall(carpeta_temp)

    # Buscar todos los .csv extraídos (incluso si vienen dentro de subcarpetas)
    archivos_csv = []
    for root, _, files in os.walk(carpeta_temp):
        for f in sorted(files):
            if f.lower().endswith(".csv"):
                archivos_csv.append(os.path.join(root, f))

    with open(ruta_csv_final, "w", encoding="utf-8-sig", newline="") as f_out:
        for idx, ruta_parte in enumerate(archivos_csv):
            with open(
                ruta_parte, "r", encoding="utf-8-sig", errors="replace"
            ) as f_in:
                for num_linea, linea in enumerate(f_in):
                    # Omitir la fila de encabezado a partir del segundo archivo
                    if idx > 0 and num_linea == 0:
                        continue
                    f_out.write(linea)

    # Limpiar archivos y carpeta temporal
    for root, dirs, files in os.walk(carpeta_temp, topdown=False):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in dirs:
            os.rmdir(os.path.join(root, d))
    os.rmdir(carpeta_temp)
    os.remove(ruta_zip)

    return len(archivos_csv)


def descargar_un_reporte(session, csrf_token, config, fecha_inicio, fecha_fin):
    prefijo = config["prefijo_archivo"]
    generator = config["generator"]
    print(f"\n--- Procesando: {prefijo} ({generator}) ---")

    headers_api = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": f"{BASE_URL}/panel/reports",
        "X-CSRF-TOKEN": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "X-App-Version": "2.0.207",
    }

    report_uuid = str(uuid.uuid4())
    payload = {
        "generator": generator,
        "channel_id": "",
        "date_from": fecha_inicio,
        "date_from__time": "00:00",
        "date_to": fecha_fin,
        "date_to__time": "23:59",
        "format": "csv",
        "uuid": report_uuid,
    }
    payload.update(config.get("extra_params", {}))

    resp = session.post(
        f"{BASE_URL}/api/v1/reports",
        headers=headers_api,
        data=payload,
        timeout=60,
    )
    resp.raise_for_status()
    report_uuid = resp.json().get("uuid", report_uuid)
    print(f"Encolado (UUID: {report_uuid}). Esperando generación...")

    url_s3 = None
    patron_s3 = re.compile(
        rf'(https://auronixchat-production-reports\.s3[^\s"\'<>]+{re.escape(report_uuid)}\.zip[^\s"\'<>]*)'
    )

    for intento in range(1, 61):
        time.sleep(3)
        resp_lista = session.get(f"{BASE_URL}/panel/reports", timeout=30)
        html_limpio = html.unescape(resp_lista.text).replace("\\/", "/")
        match_url = patron_s3.search(html_limpio)
        if match_url:
            url_s3 = match_url.group(1)
            break

    if not url_s3:
        raise TimeoutError(f"El reporte {prefijo} tardó más de 3 minutos.")

    print("Descargando desde S3...")
    archivo_resp = requests.get(url_s3, timeout=180)
    archivo_resp.raise_for_status()

    ruta_zip = os.path.join(CARPETA_DESCARGAS, f"{prefijo}_{fecha_fin}.zip")
    ruta_csv_final = os.path.join(
        CARPETA_DESCARGAS, f"{prefijo}_{fecha_fin}.csv"
    )

    with open(ruta_zip, "wb") as f:
        f.write(archivo_resp.content)

    total_partes = extraer_y_unificar_csv(ruta_zip, ruta_csv_final)
    print(
        f"¡Listo! {total_partes} archivo(s) del ZIP unificados en: {ruta_csv_final}"
    )


if __name__ == "__main__":
    os.makedirs(CARPETA_DESCARGAS, exist_ok=True)
    f_ini, f_fin = obtener_fechas_dia_vencido()
    print(
        f"Iniciando sesión (Rango a día vencido: {f_ini} 00:00 -> {f_fin} 23:59)..."
    )

    sesion, token, gen_respaldo_mensajes = iniciar_sesion()

    reportes = [
        {
            "prefijo_archivo": "detalle_chats",
            "generator": "roz_chats_stats",
            "extra_params": {
                "date_type": "created",
                "time_format": "1",
            },
        },
        {
            "prefijo_archivo": "respaldo_mensajes",
            "generator": gen_respaldo_mensajes,
            "extra_params": {},
        },
    ]

    for reporte in reportes:
        descargar_un_reporte(sesion, token, reporte, f_ini, f_fin)