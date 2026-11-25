import json
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd

# Agregar src/ al path para importar update_data
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from update_data import (  # noqa: E402
    limpiar,
    hhmmss_a_seg,
    min_a_seg,
    procesar_calixta,
    procesar_atom,
)


class TestHelpers(unittest.TestCase):
    def test_limpiar(self):
        self.assertEqual(limpiar(None, "def"), "def")
        self.assertEqual(limpiar(float("nan"), "def"), "def")
        self.assertEqual(limpiar("", "def"), "def")
        self.assertEqual(limpiar("nan", "def"), "def")
        self.assertEqual(limpiar("NaN", "def"), "def")
        self.assertEqual(limpiar("#N/A", "def"), "def")
        self.assertEqual(limpiar("  Hola  "), "Hola")

    def test_hhmmss_a_seg(self):
        self.assertEqual(hhmmss_a_seg("01:02:03"), 3723)
        self.assertEqual(hhmmss_a_seg("05:30"), 330)
        self.assertEqual(hhmmss_a_seg(""), 0)
        self.assertEqual(hhmmss_a_seg("invalido"), 0)

    def test_min_a_seg(self):
        self.assertEqual(min_a_seg("2.5 min"), 150)
        self.assertEqual(min_a_seg("1.5"), 90)
        self.assertEqual(min_a_seg(""), 0)
        self.assertEqual(min_a_seg("abc"), 0)


class TestProcesamiento(unittest.TestCase):
    def test_procesar_calixta_filtra_area_y_genera_esquema(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "calixta.csv"
            assets_dir = tmp_path / "assets"

            df = pd.DataFrame([
                {
                    "Supervisor": "Ana Lopez",
                    "Agente": "Juan Perez",
                    "Canal": "WhatsApp",
                    "Estatus": "Cerrado",
                    "Dia": "15",
                    "AREA": "UPSELLING",
                    "Resultado": "",
                    "ID Externo": "12345",
                    "Etiquetas": "Interesado",
                    "chat_id": "999001",
                    "Fecha de inicio": "2026-11-15 10:00",
                    "Contacto": "Maria",
                    "Razón de cierre": "Finalizado",
                    "Venta": "Sí",
                    "Score": "9",
                    "Mensajes del contacto": "4",
                    "Mensajes del agente": "5",
                    "Primer respuesta": "00:01:30",
                    "Tiempo de atención": "00:10:00",
                    "Primer mensaje_V2": "Hola info",
                },
                {
                    "Supervisor": "Ana Lopez",
                    "Agente": "Juan Perez",
                    "Canal": "WhatsApp",
                    "Estatus": "Cerrado",
                    "Dia": "15",
                    "AREA": "GESTION ESCOLAR",
                    "Resultado": "Ok",
                    "ID Externo": "54321",
                    "Etiquetas": "",
                    "chat_id": "999002",
                    "Fecha de inicio": "2026-11-15 11:00",
                    "Contacto": "Pedro",
                    "Razón de cierre": "Finalizado",
                    "Venta": "No",
                    "Score": "",
                    "Mensajes del contacto": "2",
                    "Mensajes del agente": "2",
                    "Primer respuesta": "00:00:45",
                    "Tiempo de atención": "00:05:00",
                    "Primer mensaje_V2": "Constancia",
                },
            ])
            df.to_csv(csv_path, index=False)

            rows = procesar_calixta(csv_path=csv_path, assets_dir=assets_dir)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(len(row), 22)
            self.assertEqual(row[6], 1)   # sin_tipif = 1
            self.assertEqual(row[7], 0)   # sin_mat = 0
            self.assertEqual(row[8], 0)   # sin_etiq = 0
            self.assertEqual(row[9], 999001)
            self.assertEqual(row[14], 1)  # con_venta = 1
            self.assertEqual(row[18], 90) # 1 min 30 seg

            data_js = (assets_dir / "data.js").read_text(encoding="utf-8")
            self.assertTrue(data_js.startswith("const DS={calixta:"))
            payload = json.loads(data_js[len("const DS={calixta:"):-2])
            self.assertEqual(len(payload), 1)

    def test_procesar_atom_genera_esquema(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "atom.csv"
            assets_dir = tmp_path / "assets"

            df = pd.DataFrame([
                {
                    "URL": "https://app.atomchat.io/conversations/abc-123",
                    "supervisor": "Carlos Ruiz",
                    "Agente": "Laura Gomez",
                    "Canal": "WhatsApp",
                    "Ultimo estado": "cerrado",
                    "Dia": "17",
                    "Grupo": "Reactivación UPS",
                    "Tipificacion": "No tipificado",
                    "matricula": "",
                    "Fecha de inicio": "2026-11-17",
                    "Hora": "09:30",
                    "Nombre del cliente": "Sofía",
                    "Categoría de atencion": "Seguimiento",
                    "Es venta": "no",
                    "Tiempo de primer respuesta": "1.5 min",
                    "Tiempo de atencion": "4 min",
                    "Primer mensaje": "Hola Sofía, retomamos tu proceso",
                }
            ])
            df.to_csv(csv_path, index=False)

            rows = procesar_atom(csv_path=csv_path, assets_dir=assets_dir)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(len(row), 22)
            self.assertEqual(row[6], 1)  # sin_tipif
            self.assertEqual(row[7], 1)  # sin_mat
            self.assertEqual(row[9], "abc-123")
            self.assertEqual(row[21], "Hola {nombre}, retomamos tu proceso")


if __name__ == "__main__":
    unittest.main()
