#!/usr/bin/env python3
"""Barre tus carpetas de proyecto y saca el inventario de logros publicables.

    python3 escanear.py ~/Proyectos ~/trabajo/clientes > inventario.json

Lee LOG.md, README.md y CLAUDE.md — nada más — y de cada proyecto saca de qué va,
en qué estado está y cuándo se tocó por última vez. Todo lo que lee pasa por el
filtro de secretos antes de salir.

No hace ninguna llamada de red. No escribe nada fuera de la salida estándar.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seguridad import (  # noqa: E402
    directorio_transitable,
    redactar,
    ruta_permitida,
    tiene_restos,
)

PROFUNDIDAD_MAX = 3
TAMANO_MAX = 400_000  # un LOG legítimo no pasa de aquí; si pasa, es un volcado

# Cómo se traduce lo que pone el LOG a un estado con el que se puede planificar.
SENALES = (
    ("terminado", ("en producción", "completado", "terminada", "terminado", "publicada",
                   "en vivo", "operativo", "en uso", "cerrado", "abierta al público",
                   "desplegado", "funcionando", "estable")),
    ("en_curso",  ("en desarrollo", "en marcha", "en curso", "en estudio", "activo",
                   "en mantenimiento", "piloto", "avance")),
    ("parado",    ("pausado", "bloqueado", "a la espera", "retirado", "sin documentar",
                   "pendiente de", "detenido")),
)


def _leer(ruta: Path) -> str:
    if not ruta_permitida(ruta):
        return ""
    try:
        if ruta.stat().st_size > TAMANO_MAX:
            return ""
        return ruta.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _linea_tras(texto: str, etiqueta: str) -> str:
    m = re.search(rf"^\*\*{etiqueta}[^:]*:\*\*\s*(.+)$", texto, re.I | re.M)
    return m.group(1).strip() if m else ""


def _seccion(texto: str, titulo: str, lineas: int = 6) -> str:
    m = re.search(rf"^#+\s*{titulo}.*$", texto, re.I | re.M)
    if not m:
        return ""
    resto = texto[m.end():].lstrip("\n").split("\n")
    fuera = []
    for linea in resto[:lineas]:
        if linea.startswith("#") or linea.startswith("---"):
            break
        fuera.append(linea)
    return " ".join(x.strip() for x in fuera if x.strip())


def _estado(texto_estado: str) -> str:
    bajo = texto_estado.lower()
    for etiqueta, señales in SENALES:
        if any(s in bajo for s in señales):
            return etiqueta
    return "en_curso" if texto_estado else "sin_datos"


def _fecha(texto: str) -> str:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", texto)
    return m.group(0) if m else ""


def _git(carpeta: Path) -> dict:
    if not (carpeta / ".git").exists():
        return {}
    def corre(*args):
        try:
            r = subprocess.run(["git", "-C", str(carpeta), *args],
                               capture_output=True, text=True, timeout=8)
            return r.stdout.strip() if r.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""
    return {
        "ultimo_commit": _fecha(corre("log", "-1", "--format=%cd", "--date=short")),
        "commits": corre("rev-list", "--count", "HEAD"),
    }


def _dias_desde(iso: str) -> int | None:
    if not iso:
        return None
    try:
        return (date.today() - datetime.strptime(iso, "%Y-%m-%d").date()).days
    except ValueError:
        return None


def analizar(carpeta: Path) -> dict | None:
    """Devuelve la ficha de un proyecto, o None si ahí no hay proyecto."""
    textos = {n: _leer(carpeta / n) for n in ("LOG.md", "README.md", "CLAUDE.md")}
    if not any(textos.values()):
        return None

    log = textos["LOG.md"]
    fuente = log or textos["README.md"] or textos["CLAUDE.md"]

    estado_txt = _linea_tras(log, "Estado actual") or _seccion(fuente, "Estado", 3)
    objetivo = _seccion(fuente, "Objetivo.*", 6) or _seccion(textos["README.md"], ".*", 4)
    actualizado = _fecha(_linea_tras(log, "Última actualización"))
    git = _git(carpeta)

    ficha = {
        "nombre": carpeta.name,
        "ruta": str(carpeta),
        "estado": _estado(estado_txt),
        "estado_texto": redactar(estado_txt)[:400],
        "objetivo": redactar(objetivo)[:600],
        "actualizado": actualizado or git.get("ultimo_commit", ""),
        "commits": git.get("commits", ""),
        "tiene_log": bool(log),
        "aviso_secretos": tiene_restos(estado_txt + objetivo),
    }
    ficha["dias_sin_tocar"] = _dias_desde(ficha["actualizado"])
    return ficha


def barrer(raices: list[Path]) -> list[dict]:
    vistos, fichas = set(), []

    def entra(carpeta: Path, nivel: int):
        if nivel > PROFUNDIDAD_MAX or carpeta in vistos:
            return
        vistos.add(carpeta)
        ficha = analizar(carpeta)
        if ficha:
            fichas.append(ficha)
        try:
            hijos = sorted(p for p in carpeta.iterdir() if p.is_dir() and not p.is_symlink())
        except OSError:
            return
        for hijo in hijos:
            if directorio_transitable(hijo.name):
                entra(hijo, nivel + 1)

    for raiz in raices:
        raiz = raiz.expanduser().resolve()
        if raiz.is_dir():
            entra(raiz, 0)

    # Lo más reciente arriba: es lo que mejor se cuenta y lo que mejor recuerdas.
    fichas.sort(key=lambda f: f["actualizado"] or "", reverse=True)
    return fichas


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventario de proyectos publicables.")
    ap.add_argument("raices", nargs="+", type=Path,
                    help="carpetas donde viven tus proyectos")
    ap.add_argument("-o", "--salida", type=Path, help="fichero JSON de salida")
    args = ap.parse_args()

    fichas = barrer(args.raices)
    resumen = {
        "generado": date.today().isoformat(),
        "total": len(fichas),
        "por_estado": {e: sum(1 for f in fichas if f["estado"] == e)
                       for e in ("terminado", "en_curso", "parado", "sin_datos")},
        "con_aviso": sum(1 for f in fichas if f["aviso_secretos"]),
        "proyectos": fichas,
    }
    texto = json.dumps(resumen, ensure_ascii=False, indent=2)

    if args.salida:
        args.salida.write_text(texto, encoding="utf-8")
        print(f"{len(fichas)} proyectos → {args.salida}", file=sys.stderr)
    else:
        print(texto)

    if resumen["con_aviso"]:
        print(f"\n  Aviso: en {resumen['con_aviso']} proyecto(s) se tachó algo que "
              f"parecía una credencial. Revisa esas fichas antes de publicar nada.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
