from siga_mcp.domain import HoraMinuto, MeioPeriodo, PeriodoCompleto


periodo = PeriodoCompleto(
    periodos=[
        MeioPeriodo(HoraMinuto.from_string("08:00"), HoraMinuto.from_string("12:00")),
        MeioPeriodo(HoraMinuto.from_string("13:00"), HoraMinuto.from_string("17:00")),
    ]
)
