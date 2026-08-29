# Juegos Imperiales — cuaderno de campaña

Skill de Claude Code para la comunidad **Imperio Agéntico**.

Publicar un logro al día durante un mes no falla por falta de trabajo hecho.
Falla porque a las once de la noche no te acuerdas de lo que hiciste en junio, y
ese día lo pierdes.

Esta skill escanea tus propias carpetas de proyecto, encuentra lo que ya tienes
terminado y te devuelve un panel con **el mes entero repartido** y el borrador de
cada post ya escrito en texto plano, listo para pegar en Skool.

![Casa por apellido, calendario, borradores y banco de reserva](docs/panel.png)

## Instalar

```bash
git clone https://github.com/flopez1977/skill-juegos-imperiales.git \
  ~/.claude/skills/juegos-imperiales
```

Y en Claude Code: **«monta mi cuaderno de campaña»**.

Te hará seis preguntas, escaneará lo que le digas y te dejará el panel.

## Qué hace

- Te asigna tu casa por el primer apellido (acentos y Ñ resueltos).
- Barre tus carpetas y clasifica cada proyecto en terminado / en curso / parado.
- Reparte los logros por días y deja colchón al final, para que perder un día no
  rompa el mes.
- Te avisa de lo que ya publicaste para que no te repitas.
- Escribe el borrador de cada post con la cabecera y los bloques de la temporada.
- Marca cuáles son ventas (que suelen puntuar aparte) y cuáles son remates de
  algo que dejaste a medias.

## Cualquier temporada

Las reglas viven en `temporadas/*.json`: fechas, casas y sus cortes de letra,
tabla de puntos, meta de logros y formato del post. Para la V4 se copia el
fichero y se cambian los números. El motor no se toca.

## Privacidad

**Nada sale de tu máquina.** Los scripts no hacen ninguna llamada de red, no
tienen dependencias fuera de la librería estándar de Python y no envían
telemetría. Puedes leerlos enteros en diez minutos.

Del escaneo:

- Solo abre `LOG.md`, `README.md` y `CLAUDE.md`. Nada más, sin comodines.
- No entra en directorios ocultos, `node_modules`, `.ssh`, `.aws` ni similares.
- Todo lo que lee pasa por un filtro que tacha claves de API, contraseñas,
  cadenas de conexión, correos e IPs privadas antes de escribir nada.
- Si el filtro tacha algo, te dice en qué proyecto: significa que tienes
  credenciales en claro en tus diarios y conviene que lo sepas.

Aun así: **el panel que genera es privado.** Lleva nombres de tus proyectos y
probablemente de tus clientes. Léelo antes de compartirlo con nadie.

## Tests

```bash
python3 -m pytest tests/ -q     # 34 tests
```

Requiere Python 3.10 o superior. Sin dependencias.

## Licencia

MIT. Cógelo y adáptalo.
