# LOG — skill juegos-imperiales

**Última actualización:** 2026-08-29
**Estado actual:** v1.0 terminada, 34 tests en verde, pendiente de publicar en GitHub

---

## Objetivo del proyecto

Skill pública de Claude Code que monta el cuaderno de campaña de cualquier
miembro de la comunidad Imperio Agéntico para cualquier temporada de los Juegos
Imperiales: casa por apellido, escaneo de sus propios proyectos, calendario de
logros repartido y borrador de cada post en texto plano de Skool.

Nace del panel privado de Fernando (`../panel-juegos-imperiales.html`), que se
generaliza para que cada uno tenga el suyo con sus cosas.

## Stack técnico

Python 3.10+ sin dependencias. HTML/CSS/JS estático en la plantilla.
Cero llamadas de red por diseño.

## Decisiones de diseño

- **Las reglas fuera del código.** `temporadas/*.json` guarda fechas, casas,
  puntos y formato del post. La V4 es un fichero nuevo, no un cambio de código.
- **Denegar por defecto en el escaneo.** Lista blanca de tres nombres de fichero
  en vez de lista negra de extensiones: la lista negra siempre se queda corta.
- **Tachar de más.** El filtro de secretos prefiere el falso positivo. Un correo
  tachado de sobra no molesta; una clave publicada sí.
- **El colchón no es relleno.** Tres días libres al final es lo que hace que
  perder un día no rompa la numeración del mes.
- **El borrador automático deja huecos a propósito.** El bloque «qué problema
  resuelve» no está en ningún LOG: está en la cabeza de quien lo hizo. Se marca
  como pendiente en vez de rellenarlo con humo.

## Threat model (skill dev-security, 2026-08-29)

Fase: desarrollo con publicación pública inmediata. Sin servidor, sin red, sin
recogida de datos. GDPR: no aplica al software; el panel puede contener datos de
clientes del usuario y se avisa por escrito al generarlo y en el README.

| Riesgo | Nivel | Mitigación |
|---|---|---|
| Secretos del usuario en el panel | Alto | `redactar()` con 6 reglas + entropía; aviso por proyecto |
| Lectura fuera de ámbito (.env, ~/.ssh) | Alto | Lista blanca de 3 ficheros + veto de directorios |
| Datos de clientes en un fichero compartible | Medio | Aviso explícito al generar y en el README |
| Inyección de HTML desde un LOG | Bajo | `escapar()` recursivo antes de serializar |
| Confianza en repo público | — | Cero dependencias, cero red, código legible |

---

## Historial de sesiones

### [2026-08-29] — Construcción completa de la v1.0
**Estado al inicio:** no existía. Solo el panel privado de Fernando, con los
datos metidos a mano.
**Trabajo realizado:**
- Threat model exprés con la skill `dev-security` antes de escribir código.
- `scripts/seguridad.py`: lista blanca de ficheros, veto de directorios y filtro
  de secretos con 6 reglas más detección por entropía. 15 tests.
- `scripts/escanear.py`: barrido con profundidad 3, lectura de LOG/README/CLAUDE,
  clasificación de estado por señales de texto y datos de git.
- `scripts/generar.py`: casa por apellido, reparto de días con colchón,
  borradores desde inventario, escapado recursivo. 19 tests.
- `plantillas/panel.html`: el panel privado parametrizado con marcadores.
- `temporadas/v3.json`: reglas de la temporada 3 completas.
- Probado contra las carpetas reales: 149 proyectos detectados, 52 terminados,
  11 con credenciales en claro tachadas por el filtro.
**Estado al terminar:** 34 tests en verde, generación de punta a punta correcta.
**Pendiente para próxima sesión:**
- [ ] Captura para `docs/panel.png` (la usa el README)
- [ ] Crear el repo público `flopez1977/skill-juegos-imperiales` y subir
- [ ] Montar CI con la skill `seguridad-repo`
- [ ] Publicar el logro 3/28 en Imperio con el enlace al repo
