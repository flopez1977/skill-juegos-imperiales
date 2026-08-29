---
name: juegos-imperiales
description: Monta tu cuaderno de campaña para los Juegos Imperiales de la comunidad Imperio Agéntico. Te asigna tu casa por el apellido, escanea tus propias carpetas de proyecto para encontrar lo que ya tienes hecho y te devuelve un panel con el calendario de logros día a día y el borrador de cada post ya escrito en texto plano para Skool. Actívala cuando alguien diga "juegos imperiales", "monta mi cuaderno de campaña", "qué publico esta semana", "planifica mis logros", "no sé qué logro publicar hoy", "en qué casa estoy", o cuando arranque una temporada nueva de los juegos. Sirve para cualquier temporada: las reglas viven en un fichero aparte.
---

# Juegos Imperiales — cuaderno de campaña

Un mes publicando un logro al día se gana o se pierde antes de empezar. El que
improvisa cada noche falla al cuarto día; el que tiene el mes repartido de
antemano solo tiene que abrir, copiar y subir la captura.

Esta skill hace ese reparto. Y lo hace con **trabajo que ya existe**: no se
inventa logros, los busca en las carpetas de quien la usa.

## Antes de nada

Todo ocurre en la máquina del usuario. Los scripts **no hacen ninguna llamada de
red** y no envían nada a ningún sitio. El panel que sale es un fichero local.

Al terminar, dile siempre que **el panel es privado**: lleva nombres de sus
proyectos y probablemente de sus clientes.

## Proceso

### 1. Averigua la temporada

Mira qué hay en `temporadas/`. Si la que pide no está, créala copiando la
estructura de `v3.json` y preguntándole las reglas (fechas, casas y sus cortes de
letra, meta de logros, tabla de puntos, formato del post). **Nunca inventes una
regla del juego**: si no la sabes, pregúntala.

### 2. Hazle las preguntas

De una en una, en conversación normal. Son seis:

1. **¿Cuál es tu primer apellido?** — Determina la casa. Regla: manda el primer
   apellido, los acentos no cuentan y la Ñ va con la N.
2. **¿Dónde viven tus proyectos?** — Una o varias carpetas. Pide rutas concretas,
   no el disco entero: el barrido solo debe ver lo que tiene sentido que vea.
3. **¿Qué has publicado ya en la comunidad?** — Lo más importante de todo.
   Sin esto, el calendario le hará repetirse. Que pegue los títulos, o que abra su
   perfil y los liste. Anota también los que quedaron a medias en categorías tipo
   General: esos son oro, se rematan y cuentan como logro nuevo.
4. **¿Cuántos logros llevas publicados?** — Para que la numeración siga donde la dejó.
5. **¿Tienes algo pendiente de vender o entregar este mes?** — Las ventas de
   automatización suelen puntuar aparte, y además son los mejores posts.
6. **¿Cuántos días de colchón quieres al final?** — Recomienda 3. Un mes sin
   colchón se rompe el primer día que surja un imprevisto.

### 3. Escanea

```bash
python3 scripts/escanear.py <carpeta> [<carpeta>...] -o inventario.json
```

Lee solo `LOG.md`, `README.md` y `CLAUDE.md`. Nada de `.env`, claves ni nada
dentro de directorios ocultos. Todo lo que sale pasa por un filtro de secretos.

Si avisa de que tachó algo, **díselo al usuario y señálale qué proyectos son**:
significa que tiene credenciales escritas en claro en sus diarios, y eso es un
problema suyo que conviene que sepa, independientemente del juego.

### 4. Escribe el perfil

Un `perfil.json` con las respuestas y el inventario dentro:

```json
{
  "apellido": "Lopez",
  "temporada": "v3",
  "hoy": "2026-08-29",
  "publicados": 2,
  "colchon": 3,
  "ya": [["hace 2d", "Logros", "Título de lo que ya publicó", "1/28"]],
  "reserva": [{"t": "Suplente", "d": "Por si un día se cae"}],
  "acc": [{"t": "Cosa a construir", "d": "Por qué merece la pena", "c": "1 sesión"}],
  "logros": [],
  "inventario": { }
}
```

- `ya` — lo ya publicado. Sale en el panel como lista de "no repetir".
- `logros` — si lo dejas vacío, se genera solo desde el inventario. **Mejor
  llénalo tú**: un borrador escrito con lo que sabes de la conversación vale
  diez veces más que uno sacado de un LOG a la fuerza.
- `inventario` — el JSON entero de `escanear.py`.

### 5. Genera

```bash
python3 scripts/generar.py perfil.json -o cuaderno.html
```

Ábrelo y repásalo con él antes de darlo por bueno.

## Cómo escribir un buen borrador de logro

El formato lo marca la temporada (en v3: cinco bloques numerados). Lo que hace
que un post funcione no es el formato:

- **El titular va en idioma de persona, no de programador.** «Sustituto de TLDV
  que transcribe en local» se lee; «pipeline de transcripción» se pasa de largo.
- **El bloque del problema es el que se lee.** Tiene que doler. Si no sabes qué
  dolía antes, el logro no está maduro para publicarse.
- **El antes → después necesita un número.** Dos días contra veinte minutos. 16
  sitios. 2.489 fichas. Sin número es publicidad.
- **La prueba es una captura, siempre.** No hay logro sin prueba.
- **Rematar vale más que estrenar.** Un post que cierra algo que dejaste a medias
  hace mejor comunidad que uno nuevo, y cuesta la mitad.

## Restricción de formato

Skool no admite markdown: nada de asteriscos, almohadillas ni tablas. Solo texto
plano, emojis y guiones. Los borradores ya salen así — no los "mejores" con
negritas al pegarlos.

## Ficheros

```
temporadas/v3.json      reglas de la temporada — copia esto para una nueva
scripts/seguridad.py    qué se puede leer y qué se tacha
scripts/escanear.py     carpetas → inventario.json
scripts/generar.py      perfil.json → cuaderno.html
plantillas/panel.html   el panel, con marcadores
tests/                  34 tests · python3 -m pytest tests/ -q
```
