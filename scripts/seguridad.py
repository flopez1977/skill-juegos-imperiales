"""Filtros de seguridad del escaneo.

Dos trabajos, los dos con la misma regla: ante la duda, fuera.

1. Decidir qué ficheros se pueden leer (lista blanca de nombres + lista negra de rutas).
2. Tachar cualquier cosa que huela a secreto antes de que llegue al panel.

El panel generado acaba siendo un fichero que la gente comparte. Todo lo que pase
por aquí hay que asumir que va a ser visto por alguien más.
"""

import re
from pathlib import Path

# Solo se leen estos ficheros. No hay comodines a propósito.
FICHEROS_PERMITIDOS = {"LOG.md", "README.md", "CLAUDE.md"}

# Si el nombre de un directorio está aquí, no se entra ni se mira qué hay dentro.
DIRECTORIOS_VETADOS = {
    ".git", ".svn", "node_modules", "vendor", "__pycache__", ".venv", "venv",
    ".ssh", ".gnupg", ".aws", ".config", ".claude", "Library", ".Trash",
    "dist", "build", ".next", ".cache", ".terraform", "secrets", "credentials",
}

# Si el nombre de un fichero encaja con alguno de estos, no se abre jamás,
# aunque se llame LOG.md dentro de una carpeta llamada .env.
PATRONES_VETADOS = [
    re.compile(p, re.I) for p in (
        r"^\.env", r"\.env$", r"\.key$", r"\.pem$", r"\.p12$", r"\.pfx$",
        r"^id_(rsa|dsa|ecdsa|ed25519)", r"\.netrc$", r"\.npmrc$", r"\.pgpass$",
        r"credential", r"secret", r"password", r"\.keychain", r"\.htpasswd$",
    )
]

# Cada patrón deja pasar el contexto y tacha solo el valor.
# El orden importa: los más específicos primero.
REGLAS_REDACCION = [
    # Claves de proveedor con prefijo reconocible
    (re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|xox[baprs]-[A-Za-z0-9-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,})"),
     "[CLAVE TACHADA]"),
    # clave: valor / password = valor / token -> valor
    (re.compile(r"(?i)\b(pass(word|wd)?|contrase(ñ|n)a|secret|token|api[_-]?key|clave|authorization|bearer)\b\s*[:=>]+\s*\S+"),
     r"\1: [TACHADO]"),
    # Cadenas de conexión con credenciales dentro
    (re.compile(r"\b([a-z][a-z0-9+.-]*)://[^\s:/@]+:[^\s@]+@"), r"\1://[USUARIO]:[TACHADO]@"),
    # Application passwords de WordPress: cuatro o más grupos de cuatro
    (re.compile(r"\b(?:[A-Za-z0-9]{4}\s){3,}[A-Za-z0-9]{4}\b"), "[TACHADO]"),
    # Correos: son datos de terceros, no secretos, pero no pintan nada en un panel
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b"), "[CORREO]"),
    # IPs privadas: revelan la topología de la red de quien usa la skill
    (re.compile(r"\b(?:10|127|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.(?:\d{1,3}\.){1,2}\d{1,3}\b"), "[IP]"),
]

# Una línea con mucha entropía y sin espacios suele ser una clave que no encaja
# en ningún patrón conocido. Se tacha entera.
_SOSPECHOSA = re.compile(r"\b[A-Za-z0-9+/_=-]{40,}\b")


def ruta_permitida(ruta: Path) -> bool:
    """True si el fichero se puede abrir. Deniega por defecto."""
    if ruta.name not in FICHEROS_PERMITIDOS:
        return False
    for parte in ruta.parts:
        if parte in DIRECTORIOS_VETADOS or parte.startswith("."):
            if parte not in (".",):
                return False
    return not any(p.search(ruta.name) for p in PATRONES_VETADOS)


def directorio_transitable(nombre: str) -> bool:
    """True si merece la pena entrar en este directorio durante el barrido."""
    return not (nombre in DIRECTORIOS_VETADOS or nombre.startswith("."))


def redactar(texto: str) -> str:
    """Devuelve el texto con los secretos tachados.

    No pretende ser un detector perfecto: pretende que un descuido no acabe
    en un fichero que se comparte. Prefiere tachar de más.
    """
    if not texto:
        return ""
    for patron, reemplazo in REGLAS_REDACCION:
        texto = patron.sub(reemplazo, texto)
    return _SOSPECHOSA.sub("[TACHADO]", texto)


def tiene_restos(texto: str) -> bool:
    """True si después de redactar todavía queda algo que huele a secreto.

    Sirve para avisar al usuario, no para bloquear: el falso positivo aquí es
    barato y el falso negativo es caro.
    """
    limpio = redactar(texto)
    return "[TACHADO]" in limpio or "[CLAVE TACHADA]" in limpio
