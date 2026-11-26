from pathlib import Path
import numpy as np
import pandas as pd

# ==========================================
# 1. DEFINICIÓN DE RUTAS
# ==========================================
ruta_base = Path(r'C:\Users\alexg\Downloads\medios_escritos_gestion_escolar-main\Backend_Calixta')
ruta_download = ruta_base / 'Calixta_Download'
ruta_clean = ruta_base / 'Calixta_Clean_Data'
ruta_destino = Path(
    r'C:\Users\alexg\Downloads\medios_escritos_gestion_escolar-main\assets\raw'
)

# Crea la carpeta destino si no existe
ruta_destino.mkdir(parents=True, exist_ok=True)

# Toma automáticamente el detalle_chats más reciente (o puedes fijar el nombre exacto)
archivos_detalle = sorted(ruta_download.glob('detalle_chats_*.csv'))
if not archivos_detalle:
  raise FileNotFoundError(
      f'No se encontró detalle_chats_*.csv en {ruta_download}'
  )
archivo_detalle = archivos_detalle[-1]

# Extrae la fecha del archivo (ej. 2026-11-25) para empatar con Primer_mensaje_calixta
fecha_corte = archivo_detalle.stem.replace('detalle_chats_', '')
archivo_primer_msg = ruta_clean / f'Primer_mensaje_calixta_{fecha_corte}.csv'

archivo_ssb = ruta_base / 'Calixta_Atom_Agentes_Noviembre_2026 - SSB.csv'
archivo_plantilla = (
    ruta_base / 'Calixta_Atom_Agentes_Noviembre_2026 - Plantilla.csv'
)
archivo_salida = (
    ruta_destino
    / 'Funnel Prospección Upselling Noviembre 2026 - Matriz Calixta.csv'
)

print(f'Procesando corte: {fecha_corte}')

# ==========================================
# 2. CARGA DE DATOS (TODO COMO TEXTO PARA NO PERDER CEROS NI TELÉFONOS)
# ==========================================
df_detalle = pd.read_csv(archivo_detalle, dtype=str)
df_ssb = pd.read_csv(archivo_ssb, dtype=str)
df_plantilla = pd.read_csv(archivo_plantilla, dtype=str)
df_primer = pd.read_csv(archivo_primer_msg, dtype=str)

# Limpieza preventiva de encabezados repetidos si existieran
df_detalle = df_detalle[df_detalle['chat_id'] != 'chat_id'].copy()
df_primer = df_primer[df_primer['CHAT_ID'] != 'CHAT_ID'].copy()

# ==========================================
# 3. TRANSFORMACIONES Y RELLENO DE VACÍOS
# ==========================================
# Rellenar celdas vacías con "Vacio" en ID Externo, Resultado y Etiquetas
for col in ['ID Externo', 'Resultado', 'Etiquetas']:
  df_detalle[col] = df_detalle[col].fillna('').str.strip()
  df_detalle.loc[df_detalle[col] == '', col] = 'Vacio'

# Columna D: 10 digitos -> =DERECHA(C2, 10)
df_detalle['10 digitos'] = df_detalle['Teléfono'].fillna('').str.strip().str[-10:]

# Columna Q: Dia -> =DIA(P2)
fechas_inicio = pd.to_datetime(
    df_detalle['Fecha de inicio'], format='%d/%m/%Y %H:%M:%S', errors='coerce'
)
df_detalle['Dia'] = fechas_inicio.dt.day.astype('Int64').astype(str)
df_detalle.loc[df_detalle['Dia'] == '<NA>', 'Dia'] = ''

# ==========================================
# 4. CRUCES (BUSCARV E INDICE/COINCIDIR)
# ==========================================

# --- Cruce 1: Venta -> =BUSCARV(G2, SSB!D:D, 1, 0) ---
# Creamos llave limpia sin ceros a la izquierda para evitar falsos negativos
matriculas_ssb = set(
    df_ssb['MATRICULA'].dropna().str.strip().str.lstrip('0')
) - {''}

id_externo_limpio = (
    df_detalle['ID Externo'].str.strip().str.lstrip('0')
)
df_detalle['Venta'] = np.where(
    (df_detalle['ID Externo'] != 'Vacio')
    & (id_externo_limpio.isin(matriculas_ssb)),
    id_externo_limpio,  # Devuelve la matrícula sin ceros igual que en tu Matriz final
    '',
)

# --- Cruce 2: Nombre y Supervisor -> =BUSCARV(L2, Plantilla!A:Q, 3/17, 0) ---
plantilla_unica = (
    df_plantilla[['USUARIOCALIXTA', 'NOMBRE', 'SUPERVISOR']]
    .dropna(subset=['USUARIOCALIXTA'])
    .drop_duplicates(subset=['USUARIOCALIXTA'], keep='first')
    .rename(columns={'NOMBRE': 'Nombre', 'SUPERVISOR': 'Supervisor'})
)

df_detalle['Agente_key'] = df_detalle['Agente'].fillna('').str.strip()
plantilla_unica['USUARIOCALIXTA'] = plantilla_unica[
    'USUARIOCALIXTA'
].str.strip()

df_merged = df_detalle.merge(
    plantilla_unica, left_on='Agente_key', right_on='USUARIOCALIXTA', how='left'
)

# --- Cruce 3: AREA -> =SI(ESBLANCO(M2), "", SI(ESNOD(HALLAR("#N/A", M2)), "GESTION ESCOLAR", "UPSELLING")) ---
# Si encontró Nombre en Plantilla -> UPSELLING; si no encontró (NaN / #N/A) -> GESTION ESCOLAR
df_merged['AREA'] = np.where(
    df_merged['Nombre'].notna() & (df_merged['Nombre'].str.strip() != ''),
    'UPSELLING',
    'GESTION ESCOLAR',
)

# --- Cruce 4: Primer mensaje_V2 -> INDICE/COINCIDIR por (chat_id + Dia) ---
df_primer['CHAT_ID_key'] = df_primer['CHAT_ID'].fillna('').str.strip()
df_primer['Dia_key'] = df_primer['Dia'].fillna('').str.strip()

# COINCIDIR(..., 0) en Excel siempre toma la primera coincidencia
primer_unico = df_primer[
    ['CHAT_ID_key', 'Dia_key', 'Primer Mensaje V2']
].drop_duplicates(subset=['CHAT_ID_key', 'Dia_key'], keep='first')

df_merged['chat_id_key'] = df_merged['chat_id'].fillna('').str.strip()

df_merged = df_merged.merge(
    primer_unico,
    left_on=['chat_id_key', 'Dia'],
    right_on=['CHAT_ID_key', 'Dia_key'],
    how='left',
)

# Si chat_id o Dia estaban vacíos, dejamos Primer Mensaje V2 vacío
condicion_vacio = (df_merged['chat_id_key'] == '') | (df_merged['Dia'] == '')
df_merged.loc[condicion_vacio, 'Primer Mensaje V2'] = ''
df_merged = df_merged.rename(
    columns={'Primer Mensaje V2': 'Primer mensaje_V2'}
)

# ==========================================
# 5. ORDENAMIENTO FINAL DE LAS 36 COLUMNAS Y EXPORTACIÓN
# ==========================================
columnas_matriz = [
    'Canal',
    'Chat',
    'Teléfono',
    '10 digitos',
    'Venta',
    'Contacto',
    'ID Externo',
    'Estatus',
    'Bandeja',
    'Resultado',
    'Razón de cierre',
    'Agente',
    'Nombre',
    'Supervisor',
    'Propietario',
    'Fecha de inicio',
    'Dia',
    'Fecha de asignación',
    'Fecha de cierre',
    'Fecha de último mensaje',
    'Score',
    'Duración',
    'Tiempo asignado',
    'Tiempo de atención',
    'Primer respuesta',
    'Respuesta promedio',
    'Mensajes del contacto',
    'Mensajes del agente',
    'Mensajes del sistema',
    'Etiquetas',
    'Comentarios',
    'chat_id',
    'contact_id',
    'session',
    'Primer mensaje_V2',
    'AREA',
]

df_final = df_merged[columnas_matriz].copy()
df_final.to_csv(archivo_salida, index=False, encoding='utf-8-sig')

print(f'¡Proceso terminado! Total de registros: {len(df_final):,}')
print(
    f"Ventas detectadas: {(df_final['Venta'] != '').sum():,} | "
    f"UPSELLING: {(df_final['AREA'] == 'UPSELLING').sum():,} | "
    f"GESTION ESCOLAR: {(df_final['AREA'] == 'GESTION ESCOLAR').sum():,}"
)
print(f'Archivo guardado en: {archivo_salida}')