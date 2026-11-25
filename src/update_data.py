from pathlib import Path
import json
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
RAW_DIR = ASSETS_DIR / "raw"

# 1. Nombres de tus archivos CSV descargados (ajústalos si cambia el número entre paréntesis)
CSV_CALIXTA = RAW_DIR / "Funnel Prospección Upselling Noviembre 2026 - Matriz Calixta.csv"
CSV_ATOM = RAW_DIR / "Funnel Prospección Upselling Noviembre 2026 - Matriz Atom.csv"


def _buscar_csv(ruta, clave):
    """Si el nombre exacto no existe (acentos, '(1)', etc.), busca en raw/ por palabra clave."""
    ruta = Path(ruta)
    if ruta.exists():
        return ruta
    candidatos = sorted(ruta.parent.glob(f"*{clave}*.csv"))
    return candidatos[0] if candidatos else ruta


VENTA_VACIA = ("", "vacio", "vacío", "no", "0", "false", "n/a", "#n/a", "sin dato", "sin datos")


def limpiar(val, default=""):
    if pd.isna(val):
        return default
    s = str(val).strip()
    return default if s in ("", "nan", "NaN", "#N/A") else s


def hhmmss_a_seg(val):
    s = limpiar(val)
    if not s or ":" not in s:
        return 0
    try:
        partes = [int(float(p)) for p in s.split(":")]
    except ValueError:
        return 0
    if len(partes) == 3:
        return partes[0] * 3600 + partes[1] * 60 + partes[2]
    if len(partes) == 2:
        return partes[0] * 60 + partes[1]
    return 0


def min_a_seg(val):
    s = limpiar(val).lower().replace("min", "").strip()
    try:
        return round(float(s) * 60)
    except ValueError:
        return 0


def procesar_calixta(csv_path=CSV_CALIXTA, assets_dir=ASSETS_DIR):
    """Procesa el CSV de Calixta y genera data.js y orig_calixta.js."""
    df_cal = pd.read_csv(_buscar_csv(csv_path, "Calixta"), dtype=str)

    # Filtrar filas válidas del área Upselling con chat_id
    df_cal_val = df_cal[
        df_cal["chat_id"].notna()
        & (df_cal["chat_id"].str.strip() != "")
        & (df_cal["AREA"].fillna("").str.strip().str.upper() == "UPSELLING")
    ].copy()

    rows_calixta = []
    for _, r in df_cal_val.iterrows():
        sup = limpiar(r.get("Supervisor"), "Sin supervisor")
        ag = limpiar(r.get("Agente"), "Sin agente")
        canal = limpiar(r.get("Canal"), "Sin canal")
        estatus = limpiar(r.get("Estatus"), "Sin estatus")
        dia = str(int(float(limpiar(r.get("Dia"), "0"))))
        area = limpiar(r.get("AREA"), "Upselling").title()

        res = limpiar(r.get("Resultado"), "Vacio")
        mat = limpiar(r.get("ID Externo"), "Vacio")
        etiq = limpiar(r.get("Etiquetas"), "")

        sin_tipif = 1 if res in ("", "Vacio") else 0
        sin_mat = 1 if mat in ("", "Vacio") else 0
        sin_etiq = 1 if etiq in ("", "Vacio") else 0

        chat_id = int(float(limpiar(r.get("chat_id"), "0")))
        fecha_ini = limpiar(r.get("Fecha de inicio"))
        contacto = limpiar(r.get("Contacto"), "SIN DATOS")
        razon = limpiar(r.get("Razón de cierre"))
        if not razon:
            razon = "Abierto (sin cierre)" if estatus == "Abierto" else "Vacio"

        # En Calixta la columna "Venta" trae la matrícula de la venta (no "Sí/No"):
        # un chat cuenta como venta si esa celda tiene cualquier valor real.
        venta_raw = limpiar(r.get("Venta")).lower()
        con_venta = 0 if venta_raw in VENTA_VACIA else 1

        score_raw = limpiar(r.get("Score"))
        try:
            score = int(float(score_raw)) if score_raw else -1
        except ValueError:
            score = -1

        msj_c = int(float(limpiar(r.get("Mensajes del contacto"), "0")))
        msj_a = int(float(limpiar(r.get("Mensajes del agente"), "0")))
        p_resp = hhmmss_a_seg(r.get("Primer respuesta"))
        t_aten = hhmmss_a_seg(r.get("Tiempo de atención"))
        primer_msj = limpiar(r.get("Primer mensaje_V2"))

        rows_calixta.append([
            sup, ag, canal, estatus, dia, area,
            sin_tipif, sin_mat, sin_etiq,
            chat_id, fecha_ini, contacto, res, razon,
            con_venta, score, msj_c, msj_a, p_resp, t_aten,
            etiq, primer_msj
        ])

    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    with open(assets_dir / "data.js", "w", encoding="utf-8") as f:
        f.write("const DS={calixta:" + json.dumps(rows_calixta, ensure_ascii=False, separators=(",", ":")) + "};")

    df_cal_orig = df_cal[df_cal["chat_id"].notna() & (df_cal["chat_id"].str.strip() != "")].fillna("")
    orig_cal_obj = {"h": list(df_cal_orig.columns), "r": df_cal_orig.values.tolist()}
    with open(assets_dir / "orig_calixta.js", "w", encoding="utf-8") as f:
        f.write("ORIG.calixta=" + json.dumps(orig_cal_obj, ensure_ascii=False, separators=(",", ":")) + ";")

    return rows_calixta


def procesar_atom(csv_path=CSV_ATOM, assets_dir=ASSETS_DIR):
    """Procesa el CSV de Atom y genera data_atom.js y orig_atom.js."""
    df_atom = pd.read_csv(_buscar_csv(csv_path, "Atom"), dtype=str)
    df_atom_val = df_atom[df_atom["URL"].notna() & (df_atom["URL"].str.strip() != "")].copy()

    rows_atom = []
    for _, r in df_atom_val.iterrows():
        sup = limpiar(r.get("supervisor"), "Sin supervisor")
        ag = limpiar(r.get("Agente"), "Sin agente")
        canal = limpiar(r.get("Canal"), "Sin canal")
        estatus = limpiar(r.get("Ultimo estado"), "Cerrado").capitalize()
        dia = str(int(float(limpiar(r.get("Dia"), "0"))))
        grupo = limpiar(r.get("Grupo"), "Sin grupo")

        tipif = limpiar(r.get("Tipificacion"), "No tipificado")
        mat = limpiar(r.get("matricula"))

        sin_tipif = 1 if tipif in ("", "Sistema", "No tipificado") else 0
        sin_mat = 1 if not mat else 0
        sin_etiq = 0  # Atom no usa etiquetas en el tablero

        url = limpiar(r.get("URL"))
        chat_id = url.split("/conversations/")[-1] if "/conversations/" in url else url

        f_ini = limpiar(r.get("Fecha de inicio"))
        hora = limpiar(r.get("Hora"))
        fecha_ini = f"{f_ini} {hora}".strip()

        contacto = limpiar(r.get("Nombre del cliente"), "SIN DATOS")
        razon = limpiar(r.get("Categoría de atencion"), "Vacio")

        venta_raw = limpiar(r.get("Es venta")).lower()
        con_venta = 1 if venta_raw in ("si", "sí", "1", "true") else 0

        p_resp = min_a_seg(r.get("Tiempo de primer respuesta"))
        t_aten = min_a_seg(r.get("Tiempo de atencion"))

        pm_raw = limpiar(r.get("Primer mensaje"))
        if contacto and contacto != "SIN DATOS":
            pm_raw = pm_raw.replace(contacto, "{nombre}")
        pm_clean = re.sub(r"\s+", " ", pm_raw.replace("*", "")).strip()[:220]

        rows_atom.append([
            sup, ag, canal, estatus, dia, grupo,
            sin_tipif, sin_mat, sin_etiq,
            chat_id, fecha_ini, contacto, tipif, razon,
            con_venta, -1, 0, 0, p_resp, t_aten,
            "", pm_clean
        ])

    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    with open(assets_dir / "data_atom.js", "w", encoding="utf-8") as f:
        f.write("DS.atom=" + json.dumps(rows_atom, ensure_ascii=False, separators=(",", ":")) + ";")

    df_atom_orig = df_atom_val.fillna("")
    orig_atom_obj = {"h": list(df_atom_orig.columns), "r": df_atom_orig.values.tolist()}
    with open(assets_dir / "orig_atom.js", "w", encoding="utf-8") as f:
        f.write("ORIG.atom=" + json.dumps(orig_atom_obj, ensure_ascii=False, separators=(",", ":")) + ";")

    return rows_atom


def main():
    rows_calixta = procesar_calixta()
    rows_atom = procesar_atom()
    print(f"Listo: {len(rows_calixta)} chats de Calixta y {len(rows_atom)} chats de Atom generados.")


if __name__ == "__main__":
    main()
