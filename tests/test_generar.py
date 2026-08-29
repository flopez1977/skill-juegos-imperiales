import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import generar as gen  # noqa: E402

CASAS = json.loads(
    (Path(__file__).resolve().parents[1] / "temporadas" / "v3.json").read_text()
)["casas"]


class TestCasaPorApellido:
    def test_los_tres_tramos(self):
        assert gen.casa_de("Cordero", CASAS)["nombre"] == "Águila"
        assert gen.casa_de("Lopez", CASAS)["nombre"] == "Grifo"
        assert gen.casa_de("Zurita", CASAS)["nombre"] == "Pegaso"

    def test_los_acentos_no_mueven_a_nadie(self):
        assert gen.casa_de("Ángel", CASAS)["nombre"] == "Águila"
        assert gen.casa_de("Óscar", CASAS)["nombre"] == "Grifo"

    def test_la_enye_va_con_la_ene(self):
        assert gen.casa_de("Ñuño", CASAS)["nombre"] == "Grifo"

    def test_con_dos_apellidos_manda_el_primero(self):
        assert gen.casa_de("De la Cruz", CASAS)["nombre"] == "Águila"

    def test_las_letras_de_los_bordes(self):
        for apellido, esperada in (("Alonso", "Águila"), ("Fernández", "Águila"),
                                   ("García", "Grifo"), ("Ortega", "Grifo"),
                                   ("Pérez", "Pegaso"), ("Zamora", "Pegaso")):
            assert gen.casa_de(apellido, CASAS)["nombre"] == esperada

    def test_apellido_vacio_no_revienta(self):
        assert gen.casa_de("", CASAS)["nombre"] in {"Águila", "Grifo", "Pegaso"}


class TestReparto:
    def _dias(self, n):
        return [date(2026, 9, d) for d in range(1, n + 1)]

    def test_cada_logro_recibe_su_dia(self):
        salida = gen.repartir(self._dias(10), [{"tit": f"L{i}"} for i in range(7)], colchon=3)
        assert [x["d"] for x in salida[:3]] == ["2026-09-01", "2026-09-02", "2026-09-03"]
        assert salida[0]["tit"] == "L0"

    def test_el_colchon_queda_al_final(self):
        salida = gen.repartir(self._dias(10), [{"tit": f"L{i}"} for i in range(7)], colchon=3)
        assert [x["t"] for x in salida[-3:]] == ["buffer"] * 3

    def test_sobran_logros_y_no_se_pierde_ningun_dia(self):
        salida = gen.repartir(self._dias(5), [{"tit": f"L{i}"} for i in range(40)], colchon=2)
        assert len(salida) == 5

    def test_faltan_logros_y_el_resto_es_colchon(self):
        salida = gen.repartir(self._dias(8), [{"tit": "único"}], colchon=1)
        assert salida[0]["tit"] == "único"
        assert all(x["t"] == "buffer" for x in salida[1:])

    def test_sin_logros_el_mes_entero_es_colchon(self):
        salida = gen.repartir(self._dias(4), [], colchon=1)
        assert all(x["t"] == "buffer" for x in salida)


class TestDesdeInventario:
    PROYECTOS = [
        {"nombre": "chatbot-gym", "estado": "terminado", "ruta": "/p/gym",
         "objetivo": "Agente que coge reservas", "estado_texto": "En producción"},
        {"nombre": "vault", "estado": "terminado", "ruta": "/p/vault",
         "objetivo": "Caja fuerte de claves", "estado_texto": "En uso"},
        {"nombre": "idea-suelta", "estado": "parado", "ruta": "/p/idea",
         "objetivo": "", "estado_texto": "Pausado"},
    ]

    def test_solo_entra_lo_terminado_o_en_curso(self):
        salida = gen.desde_inventario(self.PROYECTOS, [], 10)
        assert "idea-suelta" not in [b["src"] for b in salida]
        assert len(salida) == 2

    def test_se_salta_lo_que_ya_publicaste(self):
        salida = gen.desde_inventario(self.PROYECTOS, ["vault"], 10)
        assert all("vault" not in b["src"] for b in salida)

    def test_respeta_el_limite(self):
        assert len(gen.desde_inventario(self.PROYECTOS, [], 1)) == 1

    def test_marca_los_bloques_que_hay_que_escribir_a_mano(self):
        salida = gen.desde_inventario(self.PROYECTOS, [], 10)
        assert salida[0]["pro"] == ""
        assert "bloque 2" in salida[0]["nota"]


class TestEscapado:
    def test_escapa_html_en_texto_anidado(self):
        sucio = {"tit": "<script>alert(1)</script>", "stk": ["<img onerror=x>"]}
        limpio = gen.escapar(sucio)
        assert "<script>" not in limpio["tit"]
        assert "&lt;script&gt;" in limpio["tit"]
        assert "<img" not in limpio["stk"][0]

    def test_no_toca_numeros_ni_booleanos(self):
        assert gen.escapar({"n": 5, "b": True, "x": None}) == {"n": 5, "b": True, "x": None}


class TestPanelCompleto:
    def test_genera_un_panel_sin_marcadores_pendientes(self, tmp_path):
        perfil = {
            "apellido": "Lopez", "temporada": "v3", "hoy": "2026-09-10",
            "publicados": 2, "ya": [], "acc": [], "reserva": [],
            "logros": [{"t": "done", "tit": "Algo hecho", "src": "/p/x",
                        "sis": "", "pro": "", "stk": [], "ant": "", "aho": ""}],
        }
        html = gen.construir(perfil)
        assert "__CONFIG__" not in html
        assert "__CASA__" not in html
        assert "Casa Grifo" in html
        assert "<title>" in html

    def test_el_panel_no_deja_pasar_un_script_del_inventario(self):
        perfil = {
            "apellido": "Lopez", "temporada": "v3", "hoy": "2026-09-10",
            "publicados": 0, "ya": [], "acc": [], "reserva": [],
            "logros": [{"t": "done", "tit": "<script>robar()</script>", "src": "/p/x",
                        "sis": "", "pro": "", "stk": [], "ant": "", "aho": ""}],
        }
        assert "<script>robar()" not in gen.construir(perfil)
