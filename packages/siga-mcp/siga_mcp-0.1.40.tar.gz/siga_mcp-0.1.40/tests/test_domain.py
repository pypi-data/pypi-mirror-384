from siga_mcp import (
    HoraMinuto,
    DuracaoMinutos,
    MeioPeriodo,
    DiaDeTrabalho,
    PendenciasLancamentos,
)


def test_horaminuto_order_and_format():
    h1 = HoraMinuto.from_string("08:05")
    h2 = HoraMinuto.from_string("08:30")
    assert str(h1) == "08:05"
    assert h1 < h2
    assert h2.minutes_since_midnight() - h1.minutes_since_midnight() == 25


def test_duracao_arithmetic_and_format():
    d1 = DuracaoMinutos(480)
    d2 = DuracaoMinutos(30)
    total = d1 + d2
    assert isinstance(total, DuracaoMinutos)
    assert total.minutes == 510
    assert total.to_hhmm() == "08:30"


def test_meioperiodo_duration():
    mp = MeioPeriodo(HoraMinuto.from_string("08:00"), HoraMinuto.from_string("12:00"))
    assert mp.duracao.minutes == 240


def test_diatrabalho_parse_and_completion():
    dt_mod = __import__("datetime")
    dia = DiaDeTrabalho(
        data=dt_mod.date(2024, 1, 2),
        carga_horaria=DuracaoMinutos(480),
        tempo_registrado=DuracaoMinutos(240),
        batidas=[],
    )
    # completar com jornada padrão usando MeioPeriodo
    jornada = [
        MeioPeriodo(HoraMinuto.from_string("08:00"), HoraMinuto.from_string("12:00")),
        MeioPeriodo(HoraMinuto.from_string("13:00"), HoraMinuto.from_string("17:00")),
    ]
    dia.completar_batidas(jornada)
    assert [str(b) for b in dia.batidas] == ["08:00", "12:00", "13:00", "17:00"]
    assert dia.faltam_batidas() is False


def test_pendencialancamentos_from_xml_minimal():
    # XML alinhado ao formato esperado por from_xml (child pendencias_lançamentos)
    xml = (
        '<?xml version="1.0"?>\n'
        '<pendencias_lançamentos matricula="123" total="1" sistema="SIGA">\n'
        "  <pendencias_lançamentos>\n"
        "    <analista>123</analista>\n"
        "    <nome_analista>Fulano</nome_analista>\n"
        "    <dt_atendimento>02/01/24</dt_atendimento>\n"
        "    <carga_horaria>08:00</carga_horaria>\n"
        "    <tempo_registrado>04:00</tempo_registrado>\n"
        "    <percentual>50%</percentual>\n"
        "    <ponto_registrado>08:00, 12:00</ponto_registrado>\n"
        "  </pendencias_lançamentos>\n"
        "</pendencias_lançamentos>\n"
    )
    pend_all = PendenciasLancamentos.from_xml(xml)
    assert pend_all.total is None or int(pend_all.total.value) == 1
    assert pend_all.matricula is None or str(pend_all.matricula) == "123"
    assert len(pend_all.itens) == 1
    pend = pend_all.itens[0]
    assert str(pend.analista.matricula) == "123"
    assert pend.dia.data.isoformat() == "2024-01-02"
    assert pend.dia.carga_horaria.to_hhmm() == "08:00"
    assert pend.dia.tempo_registrado.to_hhmm() == "04:00"
    # batidas parsed
    assert [str(b) for b in pend.dia.batidas] == ["08:00", "12:00"]


def test_pendencias_multi_items_parsing():
    xml = (
        '<?xml version="1.0"?>\n'
        '<pendencias_lançamentos matricula="999" total="2" sistema="SIGA">\n'
        "  <pendencias_lançamentos>\n"
        "    <analista>999</analista>\n"
        "    <nome_analista>Um</nome_analista>\n"
        "    <dt_atendimento>02/01/24</dt_atendimento>\n"
        "    <carga_horaria>08:00</carga_horaria>\n"
        "    <tempo_registrado>04:00</tempo_registrado>\n"
        "    <percentual>50%</percentual>\n"
        "    <ponto_registrado>08:00, 12:00</ponto_registrado>\n"
        "  </pendencias_lançamentos>\n"
        "  <pendencias_lançamentos>\n"
        "    <analista>999</analista>\n"
        "    <nome_analista>Um</nome_analista>\n"
        "    <dt_atendimento>03/01/24</dt_atendimento>\n"
        "    <carga_horaria>08:00</carga_horaria>\n"
        "    <tempo_registrado>08:00</tempo_registrado>\n"
        "    <percentual>100%</percentual>\n"
        "    <ponto_registrado>08:00, 12:00, 13:00, 17:00</ponto_registrado>\n"
        "  </pendencias_lançamentos>\n"
        "</pendencias_lançamentos>\n"
    )
    allp = PendenciasLancamentos.from_xml(xml)
    assert allp.matricula is None or str(allp.matricula) == "999"
    assert allp.total is None or int(allp.total.value) == 2
    assert len(allp.itens) == 2
    dates = [p.dia.data.isoformat() for p in allp.itens]
    assert dates == ["2024-01-02", "2024-01-03"]
