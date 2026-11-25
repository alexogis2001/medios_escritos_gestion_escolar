#!/usr/bin/env python3
"""Administra los usuarios del tablero (archivo src/usuarios.js).

Las contraseñas nunca se guardan en texto plano: se guarda una sal aleatoria y el
hash SHA-256 de  sal + ":" + contraseña  (el mismo cálculo que hace src/auth.js).

Uso:
    python src/crear_usuario.py crear                 # pregunta todo paso a paso
    python src/crear_usuario.py crear -u ana -n "Ana Pérez Ruiz" -s "PEREZ RUIZ ANA"
    python src/crear_usuario.py crear -u direccion -n "Dirección" --admin
    python src/crear_usuario.py clave -u ana          # cambia la contraseña
    python src/crear_usuario.py listar
    python src/crear_usuario.py eliminar -u ana

El valor de --sup debe ser idéntico al nombre del supervisor en los datos
(por ejemplo "PEREZ RUIZ ANA"). Un usuario --admin ve toda la información.
"""
import argparse
import getpass
import hashlib
import json
import re
import secrets
import sys
from pathlib import Path

RUTA_USUARIOS = Path(__file__).resolve().parent / "usuarios.js"
MARCA_INI = "// >>> USUARIOS"
MARCA_FIN = "// <<< USUARIOS"
LINEA = re.compile(
    r'^\s*(?P<u>[a-z0-9._-]+):\{nombre:(?P<nombre>"(?:[^"\\]|\\.)*"),'
    r'sup:(?P<sup>null|"(?:[^"\\]|\\.)*"),'
    r'sal:"(?P<sal>[0-9a-f]+)",hash:"(?P<hash>[0-9a-f]{64})"\},?\s*$'
)
USUARIO_VALIDO = re.compile(r"^[a-z0-9._-]{3,32}$")
MIN_CLAVE = 8


def hash_clave(sal: str, clave: str) -> str:
    """Mismo cálculo que `hashClave` en src/auth.js."""
    return hashlib.sha256(f"{sal}:{clave}".encode("utf-8")).hexdigest()


def leer_usuarios(ruta: Path = RUTA_USUARIOS) -> dict:
    """Devuelve {usuario: {nombre, sup, sal, hash}} leyendo el bloque marcado."""
    usuarios = {}
    if not ruta.exists():
        return usuarios
    dentro = False
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if MARCA_INI in linea:
            dentro = True
            continue
        if MARCA_FIN in linea:
            break
        if not dentro or not linea.strip():
            continue
        m = LINEA.match(linea)
        if not m:
            raise ValueError(f"Línea no reconocida en {ruta.name}: {linea.strip()[:80]}")
        usuarios[m["u"]] = {
            "nombre": json.loads(m["nombre"]),
            "sup": None if m["sup"] == "null" else json.loads(m["sup"]),
            "sal": m["sal"],
            "hash": m["hash"],
        }
    return usuarios


PLANTILLA = """// Usuarios del tablero. Archivo generado por src/crear_usuario.py (también puedes
// pegar aquí las líneas que genera crear_usuario.html).
// - sup: nombre EXACTO del supervisor en los datos; null = ve toda la información.
// - Las contraseñas se guardan como hash con sal, no en texto plano.
const USUARIOS={
@@INI@@
@@LINEAS@@
@@FIN@@
};
"""


def escribir_usuarios(usuarios: dict, ruta: Path = RUTA_USUARIOS) -> None:
    lineas = []
    for u in sorted(usuarios, key=lambda x: (usuarios[x]["sup"] is not None, x)):
        d = usuarios[u]
        sup = "null" if d["sup"] is None else json.dumps(d["sup"], ensure_ascii=False)
        lineas.append(
            f'  {u}:{{nombre:{json.dumps(d["nombre"], ensure_ascii=False)},sup:{sup},'
            f'sal:"{d["sal"]}",hash:"{d["hash"]}"}},'
        )
    texto = (
        PLANTILLA.replace("@@INI@@", MARCA_INI)
        .replace("@@FIN@@", MARCA_FIN)
        .replace("@@LINEAS@@", "\n".join(lineas))
    )
    ruta.write_text(texto, encoding="utf-8")


def nueva_entrada(nombre: str, sup, clave: str) -> dict:
    sal = secrets.token_hex(8)
    return {"nombre": nombre, "sup": sup, "sal": sal, "hash": hash_clave(sal, clave)}


def validar_usuario(usuario: str) -> str:
    usuario = usuario.strip().lower()
    if not USUARIO_VALIDO.match(usuario):
        raise ValueError(
            "El usuario debe tener de 3 a 32 caracteres: letras minúsculas sin acentos, "
            "números, punto, guion o guion bajo."
        )
    return usuario


def validar_clave(clave: str) -> str:
    if len(clave) < MIN_CLAVE:
        raise ValueError(f"La contraseña debe tener al menos {MIN_CLAVE} caracteres.")
    return clave


def pedir_clave(clave_arg):
    if clave_arg:
        return validar_clave(clave_arg)
    while True:
        c1 = getpass.getpass("Contraseña: ")
        c2 = getpass.getpass("Repite la contraseña: ")
        if c1 != c2:
            print("Las contraseñas no coinciden, intenta de nuevo.")
            continue
        try:
            return validar_clave(c1)
        except ValueError as e:
            print(e)


def cmd_crear(args) -> int:
    usuarios = leer_usuarios()
    usuario = validar_usuario(args.usuario or input("Usuario (para entrar): "))
    if usuario in usuarios:
        print(f"El usuario «{usuario}» ya existe. Usa el comando «clave» para cambiar su contraseña.")
        return 1
    nombre = (args.nombre or input("Nombre completo (se muestra en el tablero): ")).strip()
    if not nombre:
        print("El nombre no puede estar vacío.")
        return 1
    if args.admin:
        sup = None
    else:
        sup = (args.sup or input("Nombre exacto del supervisor en los datos: ")).strip()
        if not sup:
            print("Indica el supervisor o usa --admin para acceso total.")
            return 1
    clave = pedir_clave(args.clave)
    usuarios[usuario] = nueva_entrada(nombre, sup, clave)
    escribir_usuarios(usuarios)
    print(f"Usuario «{usuario}» creado ({'acceso total' if sup is None else sup}).")
    return 0


def cmd_clave(args) -> int:
    usuarios = leer_usuarios()
    usuario = validar_usuario(args.usuario or input("Usuario: "))
    if usuario not in usuarios:
        print(f"El usuario «{usuario}» no existe.")
        return 1
    d = usuarios[usuario]
    usuarios[usuario] = nueva_entrada(d["nombre"], d["sup"], pedir_clave(args.clave))
    escribir_usuarios(usuarios)
    print(f"Contraseña de «{usuario}» actualizada.")
    return 0


def cmd_eliminar(args) -> int:
    usuarios = leer_usuarios()
    usuario = validar_usuario(args.usuario or input("Usuario a eliminar: "))
    if usuario not in usuarios:
        print(f"El usuario «{usuario}» no existe.")
        return 1
    if usuarios[usuario]["sup"] is None and sum(1 for d in usuarios.values() if d["sup"] is None) == 1:
        print("No se puede eliminar al único usuario con acceso total.")
        return 1
    del usuarios[usuario]
    escribir_usuarios(usuarios)
    print(f"Usuario «{usuario}» eliminado.")
    return 0


def cmd_listar(_args) -> int:
    usuarios = leer_usuarios()
    if not usuarios:
        print("No hay usuarios registrados.")
        return 0
    ancho = max(len(u) for u in usuarios)
    for u, d in usuarios.items():
        print(f"{u:<{ancho}}  {d['nombre']}  →  {d['sup'] or 'acceso total'}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Administra los usuarios del tablero.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("crear", help="crea un usuario nuevo")
    c.add_argument("-u", "--usuario")
    c.add_argument("-n", "--nombre")
    c.add_argument("-s", "--sup", help="nombre exacto del supervisor en los datos")
    c.add_argument("--admin", action="store_true", help="acceso a toda la información")
    c.add_argument("-c", "--clave", help="evita usarlo: queda en el historial de la terminal")
    c.set_defaults(fn=cmd_crear)

    k = sub.add_parser("clave", help="cambia la contraseña de un usuario")
    k.add_argument("-u", "--usuario")
    k.add_argument("-c", "--clave")
    k.set_defaults(fn=cmd_clave)

    e = sub.add_parser("eliminar", help="elimina un usuario")
    e.add_argument("-u", "--usuario")
    e.set_defaults(fn=cmd_eliminar)

    l = sub.add_parser("listar", help="muestra los usuarios registrados")
    l.set_defaults(fn=cmd_listar)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except ValueError as err:
        print(err)
        return 1


if __name__ == "__main__":
    sys.exit(main())
