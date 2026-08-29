# LOG — skill juegos-imperiales (privada de Imperio)

**Última actualización:** 2026-08-29
**Estado actual:** v1.2 · repo privado de Imperio · 45 tests en verde · CI en verde

---

## Objetivo del proyecto

Skill pública de Claude Code que monta el cuaderno de campaña de cualquier
miembro de la comunidad Imperio Agéntico para cualquier temporada de los Juegos
Imperiales: casa por apellido, escaneo de sus propios proyectos, calendario de
logros repartido y borrador de cada post en texto plano de Skool.

Nace de un panel privado hecho a mano para una sola persona, que se generaliza
para que cada uno tenga el suyo con sus propios proyectos dentro.

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
**Estado al inicio:** no existía. Solo un panel privado hecho a mano, con los
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
- Probado contra un árbol de proyectos real de gran tamaño: detecta y clasifica
  correctamente, y el filtro de secretos saltó en varios proyectos (el aviso por
  proyecto funciona).
**Estado al terminar:** 34 tests en verde, generación de punta a punta correcta.
**Pendiente para próxima sesión:**
- [ ] Publicar el logro 3/28 en Imperio con el enlace al repo

### [2026-08-29] — Privado, marca de Imperio y afinado del filtro
**Estado al inicio:** v1.0 en repo público, filtro de secretos sin calibrar.
**Trabajo realizado:**
- El repositorio pasa a **privado**: es material interno de Imperio y se entra
  por invitación. El README explica cómo pedirla.
- La corona de Imperio va en la cabecera del panel generado, embebida como data
  URI para que el HTML siga funcionando como fichero suelto.
- El acento del panel toma el color de la casa (Águila rojo, Grifo oro, Pegaso azul).
- `<meta charset>` en la plantilla: sin ella los acentos salen rotos al abrir el
  cuaderno como fichero local, que es como lo abre todo el mundo.
- Quitadas dos rutas personales que se colaron al extraer la plantilla del panel
  original, y saneado el diario de datos sobre la máquina de quien lo probó.
- **Calibrado del filtro de secretos contra un árbol real de 150 proyectos.**
  Daba 11 avisos y los 11 eran falsos: SHA de git, slugs de artículo, trozos de
  URL, prosa con palabras de cuatro letras y `os.environ.get(...)`, que es
  justamente el patrón correcto. Ahora descarta hashes y slugs, exige mayúscula
  y dígito en las cadenas largas, no dispara con lecturas de entorno ni con
  huecos por rellenar, y pide un dígito para dar por buena una application
  password. **Resultado: 11 avisos → 0, sin perder ninguna detección real.**
  Los ocho casos que lo engañaban están fijados como tests.
**Estado al terminar:** 42 tests en verde, ruido a cero contra datos reales.
**Aprendizaje:** un detector que avisa siempre es igual de inútil que uno que no
avisa nunca — con el agravante de que este parece que funciona. El calibrado
contra datos reales no era opcional, era parte de construirlo.
**Pendiente para próxima sesión:**
- [ ] Invitar al repo a quien lo pida por privado en la comunidad

### [2026-08-29] — La cabecera del post llevaba la casa equivocada
**Estado al inicio:** v1.1, a punto de sacar las capturas del post.
**Trabajo realizado:**
- Sacando la captura del borrador con un perfil de prueba de la Casa Pegaso, la
  primera línea del post decía **CASA GRIFO**. Estaba fija en la plantilla desde
  que se extrajo del panel original. Cualquiera que no fuera del Grifo habría
  publicado en la casa de otro, y en la línea más visible del post.
- La cabecera se compone ahora con el emoji y el nombre de la casa a partir del
  fichero de la temporada. Tres tests nuevos la fijan por casa.
- Dependabot: `actions/checkout` v4 → v7 (quita además el aviso de Node 20) y
  `setup-python` v5 → v7, este a mano porque su PR chocaba con el anterior.
  Ramas fusionadas y borradas en el acto: queda solo `main`.
- Capturas del logro 3/28 generadas con un perfil inventado (Casa Pegaso), en
  `../capturas/`, y el post redactado en `../posts/`.
**Estado al terminar:** 45 tests en verde, CI en verde, una sola rama.
**Aprendizaje:** el bug no salió de los tests ni de leer el código. Salió de
mirar una captura. Sacar la captura del README no era trabajo de marketing: era
la primera vez que alguien miraba el producto con ojos de usuario que no es su
autor.
**Pendiente para próxima sesión:**
- [ ] Proteger `main` requiere GitHub Pro en repos privados: decidir si compensa
      o si basta con un hook local
