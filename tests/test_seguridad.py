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
