import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import crear_usuario as cu  # noqa: E402


class TestUsuarios(unittest.TestCase):
    def test_hash_conocido(self):
        self.assertEqual(
            cu.hash_clave("sal", "clave"), hashlib.sha256(b"sal:clave").hexdigest()
        )

    def test_ida_y_vuelta(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "usuarios.js"
            usuarios = {
                "admin": cu.nueva_entrada("Administrador", None, "unaClave123"),
                "ana": cu.nueva_entrada('Ana "Ñandú" Pérez', "PEREZ RUIZ ANA", "otraClave456"),
            }
            cu.escribir_usuarios(usuarios, ruta)
            leidos = cu.leer_usuarios(ruta)
            self.assertEqual(leidos, usuarios)
            self.assertIsNone(leidos["admin"]["sup"])
            self.assertEqual(
                leidos["ana"]["hash"], cu.hash_clave(leidos["ana"]["sal"], "otraClave456")
            )

    def test_usuarios_del_proyecto_son_legibles(self):
        usuarios = cu.leer_usuarios()
        self.assertIn("admin", usuarios)
        self.assertTrue(all(len(d["hash"]) == 64 for d in usuarios.values()))

    def test_validaciones(self):
        self.assertEqual(cu.validar_usuario(" Ana.Perez "), "ana.perez")
        with self.assertRaises(ValueError):
            cu.validar_usuario("a")
        with self.assertRaises(ValueError):
            cu.validar_usuario("ana pérez")
        with self.assertRaises(ValueError):
            cu.validar_clave("corta")

    def test_sal_distinta_cada_vez(self):
        a = cu.nueva_entrada("X", None, "claveLarga1")
        b = cu.nueva_entrada("X", None, "claveLarga1")
        self.assertNotEqual(a["sal"], b["sal"])
        self.assertNotEqual(a["hash"], b["hash"])


if __name__ == "__main__":
    unittest.main()
