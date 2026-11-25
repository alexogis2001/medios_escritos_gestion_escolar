# Funnel Prospección Upselling · Tablero de Calidad de Captura

Tablero web interactivo para monitorear la calidad de captura (tipificación, matrícula y etiquetas) y métricas generales de atención en **Matriz Calixta** y **Matriz Atom**.

## Estructura del proyecto

```text
medios_escritos_gestion_escolar/
├── .gitignore
├── README.md
├── requirements.txt
├── index.html                  # Punto de entrada del tablero web (incluye la pantalla de login)
├── crear_usuario.html          # Herramienta para generar usuarios nuevos desde el navegador
├── src/                        # Código fuente (Python + Frontend)
│   ├── update_data.py          # Script ETL para procesar CSV hacia assets/*.js
│   ├── app.js                  # Lógica de filtros, tablas, gráficas, exportación Excel y login
│   ├── auth.js                 # Verificación de contraseñas (SHA-256) y bloqueo por intentos
│   ├── usuarios.js             # Lista de usuarios (contraseñas guardadas como hash con sal)
│   ├── crear_usuario.py        # Crear, listar, eliminar usuarios y cambiar contraseñas
│   └── styles.css              # Estilos visuales del tablero y del login
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

## Acceso y usuarios

- Para entrar al tablero se escribe solo el **usuario**. La **contraseña** se pide al hacer clic en **Análisis general**. Cada supervisor ve únicamente sus propios chats (en Calixta y Atom, según le correspondan). El usuario `admin` ve toda la información.
- Las contraseñas **ya no están en texto plano**: `src/usuarios.js` guarda una sal y un hash SHA-256. Las contraseñas que ya usaban los supervisores siguen siendo las mismas.
- Tras 5 contraseñas incorrectas se bloquea el intento 30 segundos. La sesión (y la contraseña ya validada) dura mientras la pestaña esté abierta; **Cerrar sesión** la termina.

### Crear un usuario nuevo

**Opción A: desde el navegador.** Abre `crear_usuario.html`, llena el formulario (el supervisor se elige de una lista tomada de los datos) y pega la línea que genera en `src/usuarios.js`, antes de `// <<< USUARIOS`.

**Opción B: desde la terminal.**

```bash
python src/crear_usuario.py crear                      # pregunta todo paso a paso
python src/crear_usuario.py crear -u ana -n "Ana Pérez Ruiz" -s "PEREZ RUIZ ANA"
python src/crear_usuario.py crear -u direccion -n "Dirección" --admin   # acceso total
python src/crear_usuario.py clave -u ana               # cambiar contraseña
python src/crear_usuario.py eliminar -u ana
python src/crear_usuario.py listar
```

El nombre del supervisor (`--sup`) debe coincidir exactamente con el de los datos. Una coordinadora que debe ver a varios supervisores se da de alta con `-s "NOMBRE 1,NOMBRE 2,..."` (separados por coma); en `src/usuarios.js` su campo `sup` queda como lista. Después de crear o cambiar usuarios, sube `src/usuarios.js` a tu página.

> Nota: es un tablero estático, así que el filtrado ocurre en el navegador. Los hashes evitan que las contraseñas se lean a simple vista, y el login evita que la vista muestre datos ajenos, pero no protegen los archivos `assets/*.js`, que pueden consultarse directamente. Para una protección real se necesita un servidor.

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
