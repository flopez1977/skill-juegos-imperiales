#!/usr/bin/env python3
"""Monta el cuaderno de campaña a partir del perfil y del inventario.

    python3 generar.py perfil.json -o mi-panel.html

El perfil lo escribe Claude después de hacerte las preguntas (ver SKILL.md).
El inventario lo saca escanear.py. Aquí solo se juntan y se pintan.

No hace ninguna llamada de red. Todo el texto que viene de fichero se escapa
antes de entrar en el HTML.
"""

import argparse
import html
import json
import sys
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "plantillas" / "panel.html"
TEMPORADAS = RAIZ / "temporadas"

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago",
         "sep", "oct", "nov", "dic"]


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def casa_de(apellido: str, casas: list[dict]) -> dict:
    """Primera letra del primer apellido. Los acentos no mueven a nadie."""
    limpio = _sin_tildes(apellido.strip()).upper()
    inicial = limpio[0] if limpio else "?"
    if inicial == "Ñ":
        inicial = "N"
    for casa in casas:
        if casa["desde"] <= inicial <= casa["hasta"]:
            return casa
    return casas[-1]


def _fecha(iso: str) -> date:
    return datetime.strptime(iso, "%Y-%m-%d").date()


def _corto(d: date) -> str:
    return f"{d.day} {MESES[d.month - 1]}".upper()


def escapar(valor):
    """Escapa recursivamente cualquier texto que acabe dentro del HTML."""
    if isinstance(valor, str):
        return html.escape(valor, quote=False)
    if isinstance(valor, list):
        return [escapar(v) for v in valor]
    if isinstance(valor, dict):
        return {k: escapar(v) for k, v in valor.items()}
    return valor


def repartir(dias_libres: list[date], entradas: list[dict], colchon: int) -> list[dict]:
    """Coloca cada logro en un día y deja el colchón al final.

    El colchón no es relleno: es lo que hace que perder un día no rompa el mes.
    """
    huecos = len(dias_libres)
    utiles = max(0, huecos - colchon)
    salida = []

    for i, dia in enumerate(dias_libres):
        if i < utiles and i < len(entradas):
            entrada = dict(entradas[i])
        elif i == huecos - 1 and entradas and entradas[-1].get("cierre"):
            entrada = dict(entradas[-1])
        else:
            entrada = {"t": "buffer", "tit": "Colchón · concurso o banco de reserva",
                       "src": "sin asignar", "sis": "", "pro": "", "stk": [],
                       "ant": "", "aho": "",
                       "nota": "Día libre a propósito: para un concurso, para recuperar "
                               "uno que se cayó, o para tirar del banco de reserva."}
        entrada["d"] = dia.isoformat()
        salida.append(entrada)
    return salida


def desde_inventario(proyectos: list[dict], excluir: list[str], limite: int) -> list[dict]:
    """Convierte fichas de proyecto en borradores de logro.

    Solo entra lo terminado o casi: un logro se cuenta cuando existe, no cuando
    se promete. Y se salta cualquier cosa que el usuario diga que ya publicó.
    """
    veto = [_sin_tildes(x).lower() for x in excluir]
    orden = {"terminado": 0, "en_curso": 1, "parado": 2, "sin_datos": 3}
    candidatos = [p for p in proyectos if p["estado"] in ("terminado", "en_curso")]
    candidatos.sort(key=lambda p: (orden[p["estado"]], -(len(p.get("objetivo", "")))))

    borradores = []
    for p in candidatos:
        etiqueta = _sin_tildes(f"{p['nombre']} {p.get('objetivo','')}").lower()
        if any(v and v in etiqueta for v in veto):
            continue
        borradores.append({
            "t": "done" if p["estado"] == "terminado" else "build",
            "tit": p["nombre"].replace("-", " ").replace("_", " ").capitalize(),
            "src": p["ruta"],
            "sis": p.get("objetivo", "")[:400],
            "pro": "",
            "stk": [],
            "ant": "",
            "aho": p.get("estado_texto", "")[:300],
            "nota": ("Borrador automático desde tu LOG. Falta el bloque 2 (qué problema "
                     "resuelve) y el stack: eso no está en ningún fichero, está en tu cabeza."
                     + ("  Se tachó algo que parecía una credencial: revísalo."
                        if p.get("aviso_secretos") else "")),
        })
        if len(borradores) >= limite:
            break
    return borradores


def construir(perfil: dict) -> str:
    temporada_id = perfil.get("temporada", "v3")
    temporada = json.loads((TEMPORADAS / f"{temporada_id}.json").read_text(encoding="utf-8"))

    apellido = perfil.get("apellido", "").strip()
    casa = casa_de(apellido, temporada["casas"])

    inicio, fin = _fecha(temporada["inicio"]), _fecha(temporada["fin"])
    hoy = _fecha(perfil["hoy"]) if perfil.get("hoy") else date.today()
    primero = max(hoy + timedelta(days=1), inicio)

    dias = []
    cursor = primero
    while cursor <= fin:
        dias.append(cursor)
        cursor += timedelta(days=1)

    entradas = list(perfil.get("logros", []))
    if not entradas:
        entradas = desde_inventario(perfil.get("inventario", {}).get("proyectos", []),
                                    [y[2] for y in perfil.get("ya", [])],
                                    len(dias))

    cfg = {
        "ya": perfil.get("ya", []),
        "dias": repartir(dias, entradas, perfil.get("colchon", 3)),
        "reserva": perfil.get("reserva", []),
        "acc": perfil.get("acc", []),
        "hoy": [hoy.year, hoy.month, hoy.day],
        "inicio": [inicio.year, inicio.month, inicio.day],
        "fin": [fin.year, fin.month, fin.day],
        "publicados": perfil.get("publicados", 0),
        "meta": temporada["meta_logros"],
    }

    plantilla = PLANTILLA.read_text(encoding="utf-8")
    salida = plantilla.replace("__CONFIG__",
                               json.dumps(escapar(cfg), ensure_ascii=False))
    for marca, valor in (
        ("__TITULO__", perfil.get("titulo", f"Cuaderno de Campaña {casa['nombre']}")),
        ("__CASA__", f"Casa {casa['nombre']}"),
        ("__APELLIDO__", f"{apellido} · {casa['desde']}–{casa['hasta']}"),
        ("__PERIODO__", f"{_corto(inicio).lower()} → {_corto(fin).lower()} "
                        f"{fin.year} · {temporada['nombre']}"),
        ("__INI_CORTO__", _corto(inicio)),
        ("__FIN_CORTO__", _corto(fin) + " · FINAL"),
        ("__META__", str(temporada["meta_logros"])),
    ):
        salida = salida.replace(marca, html.escape(str(valor), quote=False))

    # El acento del panel es el color de tu casa, no siempre el del Grifo.
    color = casa.get("color", {})
    for tema, clave in (("L", "claro"), ("D", "oscuro")):
        for i, valor in enumerate(color.get(clave, [])):
            salida = salida.replace(f"__C_{tema}{i}__", valor)
    return salida


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera tu cuaderno de campaña.")
    ap.add_argument("perfil", type=Path, help="perfil.json con tus respuestas")
    ap.add_argument("-o", "--salida", type=Path, default=Path("cuaderno.html"))
    args = ap.parse_args()

    perfil = json.loads(args.perfil.read_text(encoding="utf-8"))
    args.salida.write_text(construir(perfil), encoding="utf-8")

    casa = casa_de(perfil.get("apellido", ""), json.loads(
        (TEMPORADAS / f"{perfil.get('temporada','v3')}.json").read_text(encoding="utf-8")
    )["casas"])
    print(f"Cuaderno de la Casa {casa['nombre']} → {args.salida}", file=sys.stderr)
    print("El panel lleva nombres de tus proyectos y puede llevar nombres de tus "
          "clientes. Es privado: léelo antes de compartirlo con nadie.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
