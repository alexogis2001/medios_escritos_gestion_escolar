from pathlib import Path
import pandas as pd

# 1. Definir rutas de origen y destino
ruta_origen = Path(r'C:\Users\alexg\Downloads\medios_escritos_gestion_escolar-main\Backend_Calixta\Calixta_Download')
ruta_destino = Path(
    r'C:\Users\alexg\Downloads\medios_escritos_gestion_escolar-main\Backend_Calixta\Calixta_Clean_Data'
)

# Crea la carpeta de destino automáticamente si aún no existe
ruta_destino.mkdir(parents=True, exist_ok=True)

# Busca automáticamente el respaldo más reciente en la carpeta de origen
archivos = sorted(ruta_origen.glob('respaldo_mensajes_*.csv'))
if not archivos:
  raise FileNotFoundError(
      f'No se encontró ningún archivo respaldo_mensajes_*.csv en {ruta_origen}'
  )

archivo_entrada = archivos[-1]
print(f'Procesando archivo: {archivo_entrada.name}')

# 2. Cargar la data limpia (forzamos texto en Chat/Autor/IDs para evitar notación científica)
df = pd.read_csv(
    archivo_entrada,
    dtype={
        'Chat': str,
        'Autor': str,
        'CHAT_ID': str,
        'CONTACT_ID': str,
    },
)

# Limpieza preventiva: eliminar encabezados repetidos si se pegaron cortes de archivo
df = df[df['CHAT_ID'] != 'CHAT_ID'].copy()

# 3. Equivalente a =CONTAR.SI($I$2:I2, I2) y filtrar solo los "1"
df_primer_mensaje = df.drop_duplicates(subset=['CHAT_ID'], keep='first').copy()

# 4. Replicar la estructura exacta de columnas de "Primer_mensaje_calixta"
df_primer_mensaje[''] = ''  # Columna L (vacía)
df_primer_mensaje[' '] = ''  # Columna M (vacía)

# Equivalente a =DIA(D2)
fechas = pd.to_datetime(
    df_primer_mensaje['Fecha'], format='%d/%m/%Y %H:%M:%S', errors='coerce'
)
df_primer_mensaje['Dia'] = fechas.dt.day

# Equivalente a =CONTAR.SI(...) ya filtrado en 1
df_primer_mensaje['Primer Mensaje'] = 1

# Equivalente a =E2
df_primer_mensaje['Primer Mensaje V2'] = df_primer_mensaje['Mensaje']

# 5. Exportar respetando exactamente las 16 columnas y su orden
columnas_finales = [
    'Canal',
    'Chat',
    'Contacto',
    'Fecha',
    'Mensaje',
    'Tipo',
    'Formato',
    'Autor',
    'CHAT_ID',
    'CONTACT_ID',
    'UUID',
    '',
    ' ',
    'Dia',
    'Primer Mensaje',
    'Primer Mensaje V2',
]

# Extrae la fecha del archivo original para nombrar la salida (ej. Primer_mensaje_calixta_2026-11-25.csv)
fecha_archivo = archivo_entrada.stem.replace('respaldo_mensajes_', '')
archivo_salida = ruta_destino / f'Primer_mensaje_calixta_{fecha_archivo}.csv'

df_primer_mensaje[columnas_finales].to_csv(
    archivo_salida, index=False, encoding='utf-8-sig'
)

print(f'Listo: {len(df):,} filas reducidas a {len(df_primer_mensaje):,} chats únicos.')
print(f'Archivo guardado en: {archivo_salida}')