from datetime import date
from datetime import timedelta

from django.test import SimpleTestCase

from .lunar import events
from .lunar import month_phases
from .lunar import phase_on
from .lunar import proxima_buena_para_sembrar
from .lunar import recomendacion


class LunarTests(SimpleTestCase):
    def test_ecuador_date_rollover(self):
        assert phase_on(date(2026, 4, 1))["name"] == "Luna llena"
        assert phase_on(date(2026, 4, 1))["time"] == "21:12"
        assert phase_on(date(2026, 1, 25))["name"] == "Cuarto creciente"
        assert not phase_on(date(2026, 4, 2))["primary"]

    def test_full_moon_and_tradition(self):
        assert phase_on(date(2026, 11, 18))["sow"]
        assert not phase_on(date(2026, 11, 24))["sow"]
        assert phase_on(date(2026, 11, 24))["time"] == "09:53"

    def test_month_and_coverage(self):
        assert len(month_phases(date(2026, 11, 1))) == 4
        assert len(month_phases(date(2026, 5, 1))) == 5
        assert phase_on(date(2031, 1, 1)) is None
        assert phase_on(date(2025, 1, 1)) is None
        assert len(events()) == 297


class RecomendacionLunarTests(SimpleTestCase):
    def test_preparacion_siembra_y_cosecha_segun_la_fase(self):
        nueva = next(e for e in events() if e["phase"] == "New Moon")
        llena = next(e for e in events() if e["phase"] == "Full Moon")
        menguante = next(e for e in events() if e["phase"] == "Last Quarter")
        assert recomendacion("preparacion", nueva["date"])["ideal"]
        assert recomendacion("siembra", llena["date"])["ideal"]
        assert not recomendacion("siembra", nueva["date"])["ideal"]
        assert recomendacion("cosecha", menguante["date"], "semillas_raices")["ideal"]
        assert not recomendacion("cosecha", llena["date"], "semillas_raices")["ideal"]
        assert recomendacion("cosecha", llena["date"], "hojas_flores_frutos")["ideal"]

    def test_sin_recomendacion_para_otros_tipos_o_fecha_fuera_de_rango(self):
        llena = next(e for e in events() if e["phase"] == "Full Moon")
        assert recomendacion("riego", llena["date"]) is None
        assert recomendacion("cosecha", llena["date"], "") is None
        assert recomendacion("siembra", date(2031, 1, 1)) is None


class ProximaBuenaParaSembrarTests(SimpleTestCase):
    def test_hoy_cuando_la_fecha_ya_es_favorable(self):
        llena = next(e for e in events() if e["phase"] == "Full Moon")
        resultado = proxima_buena_para_sembrar(llena["date"])
        assert resultado == {
            "fecha": llena["date"],
            "hoy": True,
            "fase": "Luna llena",
            "icono": "🌕",
        }

    def test_busca_hacia_adelante_cuando_hoy_no_es_favorable(self):
        nueva = next(e for e in events() if e["phase"] == "New Moon")
        resultado = proxima_buena_para_sembrar(nueva["date"])
        assert not resultado["hoy"]
        assert resultado["fecha"] == nueva["date"] + timedelta(days=1)

    def test_sin_resultado_fuera_del_rango_de_datos_lunares(self):
        assert proxima_buena_para_sembrar(date(2031, 1, 1)) is None
