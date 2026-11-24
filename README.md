# Funnel Prospección Upselling · Tablero de Calidad de Captura

Tablero web interactivo para monitorear la calidad de captura (tipificación, matrícula y etiquetas) y métricas generales de atención en **Matriz Calixta** y **Matriz Atom**.

## Estructura del proyecto

```text
medios_escritos_gestion_escolar/
├── .gitignore
├── README.md
├── requirements.txt
├── index.html                  # Punto de entrada del tablero web
├── src/                        # Código fuente (Python + Frontend)
│   ├── update_data.py          # Script ETL para procesar CSV hacia assets/*.js
│   ├── app.js                  # Lógica de filtros, tablas, gráficas y exportación Excel
│   └── styles.css              # Estilos visuales del tablero
├── assets/                     # Datos procesados que consume el navegador
│   ├── data.js
│   ├── data_atom.js
│   ├── orig_calixta.js
│   ├── orig_atom.js
│   └── raw/                    # Archivos CSV crudos descargados (ignorados en Git)
│       ├── Funnel Prospección Upselling Noviembre 2026 - Matriz Calixta.csv
│       └── Funnel Prospección Upselling Noviembre 2026 - Matriz Atom.csv
└── tests/                      # Pruebas automatizadas
    └── test_update_data.py
```

## Cómo visualizar el tablero

1. Abre `index.html` directamente en tu navegador (o sírvelo localmente con `python -m http.server 8000` y entra a `http://localhost:8000`).
2. Usa los botones superiores (**Matriz Calixta** / **Matriz Atom**) y las pestañas (**Calidad de captura** / **Análisis general**) para explorar los datos.

## Cómo actualizar los datos

1. Instala las dependencias (si aún no las tienes):
   ```bash
   pip install -r requirements.txt
   ```
2. Coloca las nuevas descargas CSV dentro de `assets/raw/` conservando los nombres esperados (o ajusta `CSV_CALIXTA` y `CSV_ATOM` al inicio de `src/update_data.py`).
3. Ejecuta el script de actualización desde cualquier carpeta:
   ```bash
   python src/update_data.py
   ```
   Esto regenerará automáticamente `assets/data.js`, `assets/orig_calixta.js`, `assets/data_atom.js` y `assets/orig_atom.js`.

## Ejecutar pruebas

```bash
python -m unittest discover -s tests -v
```
