import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import seguridad as sg  # noqa: E402


class TestRutaPermitida:
    def test_acepta_los_tres_ficheros_de_la_lista(self):
        for nombre in ("LOG.md", "README.md", "CLAUDE.md"):
            assert sg.ruta_permitida(Path("proyectos/web") / nombre)

    def test_rechaza_cualquier_otro_nombre(self):
        for nombre in ("notas.md", ".env", "config.php", "id_rsa", "secretos.md"):
            assert not sg.ruta_permitida(Path("proyectos/web") / nombre)

    def test_rechaza_un_log_dentro_de_un_directorio_vetado(self):
        assert not sg.ruta_permitida(Path("proyecto/node_modules/LOG.md"))
        assert not sg.ruta_permitida(Path("~/.ssh/LOG.md"))

    def test_rechaza_un_log_dentro_de_cualquier_directorio_oculto(self):
        assert not sg.ruta_permitida(Path("proyecto/.oculto/LOG.md"))

    def test_no_transita_directorios_vetados_ni_ocultos(self):
        assert sg.directorio_transitable("web-work")
        assert not sg.directorio_transitable("node_modules")
        assert not sg.directorio_transitable(".git")


class TestRedactar:
    def test_tacha_claves_con_prefijo_conocido(self):
        for clave in (
            "sk-abcdefghijklmnop1234567890",
            "ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "AKIAIOSFODNN7EXAMPLE",
            "xoxb-1234567890-abcdefghij",
        ):
            fuera = sg.redactar(f"la clave es {clave} y ya")
            assert clave not in fuera

    def test_tacha_el_valor_pero_deja_la_etiqueta(self):
        fuera = sg.redactar("password: Tr0ncoV3rde!")
        assert "Tr0ncoV3rde!" not in fuera
        assert "password" in fuera.lower()

    def test_tacha_credenciales_de_una_cadena_de_conexion(self):
        fuera = sg.redactar("mysql://fer:miclave@db.local/base")
        assert "miclave" not in fuera
        assert "mysql://" in fuera

    def test_tacha_application_password_de_wordpress(self):
        fuera = sg.redactar("APP PASS: abcd EFGH 1234 wxyz")
        assert "abcd EFGH 1234 wxyz" not in fuera

    def test_tacha_correos_y_ips_privadas(self):
        fuera = sg.redactar("avisa a jefe@cliente.com en 192.168.1.51")
        assert "jefe@cliente.com" not in fuera
        assert "192.168.1.51" not in fuera

    def test_tacha_cadenas_largas_sin_patron_conocido(self):
        basura = "Qm9uaXRvRGlhUGFyYVVuU2VjcmV0b011eUxhcmdvRGVWZXJkYWQxMjM0"
        assert basura not in sg.redactar(f"valor {basura}")

    def test_no_estropea_un_texto_normal(self):
        texto = "Se migró la web a un hosting nuevo con 301 completas y quedó indexable."
        assert sg.redactar(texto) == texto

    def test_aguanta_texto_vacio(self):
        assert sg.redactar("") == ""
        assert sg.redactar(None) == ""


class TestAviso:
    def test_avisa_cuando_habia_algo_que_tachar(self):
        assert sg.tiene_restos("token: abc123supersecretovalor")

    def test_no_avisa_con_texto_limpio(self):
        assert not sg.tiene_restos("Web en producción, 12 artículos programados.")


class TestFalsosPositivos:
    """Casos reales que hacían saltar el aviso sin haber ningún secreto.

    Salieron de pasar el escáner por un árbol de 149 proyectos: los 11 avisos
    que dio eran los 11 falsos. Un aviso que siempre miente no lo mira nadie.
    """

    def test_no_tacha_un_sha_de_git(self):
        sha = "d541fd0aa1b2c3d4e5f60718293a4b5c6d7e8f90"
        assert sha in sg.redactar(f"Commit {sha} en main")

    def test_no_tacha_el_slug_largo_de_un_articulo(self):
        slug = "como-elegir-la-mejor-piscina-de-obra-en-madrid-guia"
        assert slug in sg.redactar(f"Publicado /blog/{slug}/")

    def test_no_tacha_una_url_larga(self):
        url = "https://ejemplo.com/wp-content/uploads/2026/08/fotografia-de-portada.jpg"
        assert "fotografia-de-portada" in sg.redactar(f"Imagen en {url}")

    def test_no_tacha_una_lectura_de_variable_de_entorno(self):
        linea = 'api_key = os.environ.get("NVIDIA_API_KEY")'
        assert sg.redactar(linea) == linea

    def test_no_tacha_un_hueco_por_rellenar(self):
        for linea in ('password: <tu contraseña>', "token: xxxxxxxx",
                      "api_key: ${API_KEY}", "clave: ..."):
            assert "[TACHADO]" not in sg.redactar(linea)

    def test_no_tacha_prosa_con_palabras_de_cuatro_letras(self):
        texto = "Cada vez que sale algo malo hay que ver como esta todo esto"
        assert sg.redactar(texto) == texto

    def test_no_avisa_al_hablar_de_credenciales_sin_ponerlas(self):
        assert not sg.tiene_restos(
            "Token de GitHub expuesto en el remote: incidente resuelto, rotado el 12-07.")

    def test_pero_sigue_tachando_lo_que_si_es_una_clave(self):
        """El afinado no puede haberse llevado por delante la detección real."""
        assert sg.tiene_restos("password: Tr0ncoV3rde2026")
        assert sg.tiene_restos("APP PASS: ab3d EFGH 12x4 wxyz")
        assert sg.tiene_restos("mysql://fer:miclave@db.local/base")
