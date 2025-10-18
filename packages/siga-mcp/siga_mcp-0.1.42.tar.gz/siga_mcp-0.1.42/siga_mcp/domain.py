from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import re
import xml.etree.ElementTree as ET
from typing import Literal, Sequence
from enum import Enum


# -------------------- Value Objects --------------------


@dataclass(frozen=True, slots=True)
class HoraMinuto:
    """Representa um horário do dia com precisão de minutos (HH:MM).

    Exemplos
    --------
    >>> h = HoraMinuto.from_string("7:05")
    >>> str(h)
    '07:05'
    >>> h.to_time()
    datetime.time(7, 5)
    >>> HoraMinuto(23, 59).minutes_since_midnight()
    1439
    """

    hour: int
    minute: int

    _REGEX = re.compile(r"^(\d{1,2}):(\d{2})$")

    def __post_init__(self):
        if not (0 <= self.hour < 24 and 0 <= self.minute < 60):
            raise ValueError("HoraMinuto inválido: fora do intervalo 00:00..23:59")

    @staticmethod
    def from_string(value: str) -> HoraMinuto:
        """Cria um horário a partir de uma string 'HH:MM'.

        Exemplos
        --------
        >>> h = HoraMinuto.from_string('7:05')
        >>> (h.hour, h.minute)
        (7, 5)
        >>> str(h)
        '07:05'
        """
        value = value.strip()
        m = HoraMinuto._REGEX.match(value)
        if not m:
            raise ValueError(f"Formato inválido de HH:MM: {value!r}")
        hh, mm = int(m.group(1)), int(m.group(2))
        return HoraMinuto(hh, mm)

    def __str__(self) -> str:
        """Representação normalizada no formato HH:MM.

        >>> str(HoraMinuto(7, 5))
        '07:05'
        """
        return f"{self.hour:02d}:{self.minute:02d}"

    def to_time(self) -> time:
        """Converte para ``datetime.time``.

        >>> HoraMinuto(7, 5).to_time()
        datetime.time(7, 5)
        """
        return time(self.hour, self.minute)

    def minutes_since_midnight(self) -> int:
        """Minutos decorridos desde 00:00.

        >>> HoraMinuto(1, 30).minutes_since_midnight()
        90
        """
        return self.hour * 60 + self.minute

    def __lt__(self, other: "HoraMinuto") -> bool:  # para ordenação/comparação simples
        """True se este horário for anterior ao outro.

        >>> HoraMinuto(8, 0) < HoraMinuto(9, 0)
        True
        """
        return self.minutes_since_midnight() < other.minutes_since_midnight()

    def __le__(self, other: "HoraMinuto") -> bool:
        """True se este horário for anterior ou igual ao outro.

        >>> HoraMinuto(8, 0) <= HoraMinuto(8, 0)
        True
        """
        return self.minutes_since_midnight() <= other.minutes_since_midnight()

    def __eq__(self, other: object) -> bool:
        """Compara igualdade por hora e minuto.

        >>> HoraMinuto(8, 0) == HoraMinuto(8, 0)
        True
        >>> HoraMinuto(8, 1) == HoraMinuto(8, 0)
        False
        """
        if not isinstance(other, HoraMinuto):
            return False
        return (self.hour, self.minute) == (other.hour, other.minute)

    def __ge__(self, other: "HoraMinuto") -> bool:
        """True se este horário for posterior ou igual ao outro.

        >>> HoraMinuto(9, 0) >= HoraMinuto(8, 59)
        True
        """
        return self.minutes_since_midnight() >= other.minutes_since_midnight()

    def __gt__(self, other: "HoraMinuto") -> bool:
        """True se este horário for posterior ao outro.

        >>> HoraMinuto(9, 0) > HoraMinuto(8, 59)
        True
        """
        return self.minutes_since_midnight() > other.minutes_since_midnight()

    def shifted(self, minutes: int, *, clamp: bool = True) -> HoraMinuto:
        """Retorna um novo horário deslocado em minutos.

        Se clamp=True (padrão), limita no intervalo 00:00..23:59.
        Se clamp=False, faz wrap-around em 24h.

        Exemplos
        --------
        >>> str(HoraMinuto(8, 0).shifted(90))
        '09:30'
        >>> str(HoraMinuto(0, 10).shifted(-30))  # clamp evita negativos
        '00:00'
        >>> str(HoraMinuto(23, 50).shifted(20, clamp=False))  # wrap 24h
        '00:10'
        """
        total = self.minutes_since_midnight() + int(minutes)
        if clamp:
            total = max(0, min(23 * 60 + 59, total))
        else:
            total %= 24 * 60
        h, m = divmod(total, 60)
        return HoraMinuto(h, m)

    def diff(self, other: HoraMinuto) -> "DuracaoMinutos":
        """Diferença absoluta entre dois horários (em minutos).

        >>> HoraMinuto(9, 0).diff(HoraMinuto(8, 30)).minutes
        30
        """
        return DuracaoMinutos(
            abs(self.minutes_since_midnight() - other.minutes_since_midnight())
        )


@dataclass(frozen=True, slots=True)
class DuracaoMinutos:
    """Duração em minutos com utilitários para conversão.

    >>> DuracaoMinutos(150).to_hhmm()
    '02:30'
    >>> DuracaoMinutos.from_hhmm('08:00').minutes
    480
    >>> (DuracaoMinutos(120) + DuracaoMinutos(45)).minutes
    165
    """

    minutes: int

    def __post_init__(self):
        if self.minutes < 0:
            object.__setattr__(self, "minutes", 0)

    @staticmethod
    def from_hhmm(value: str) -> DuracaoMinutos:
        """Cria uma duração a partir de 'HH:MM'.

        >>> DuracaoMinutos.from_hhmm('01:30').minutes
        90
        >>> str(DuracaoMinutos.from_hhmm('00:45'))
        '00:45'
        """
        h = HoraMinuto.from_string(value)
        return DuracaoMinutos(h.hour * 60 + h.minute)

    def to_hhmm(self) -> str:
        """Retorna representação HH:MM da duração.

        >>> DuracaoMinutos(90).to_hhmm()
        '01:30'
        """
        h, m = divmod(self.minutes, 60)
        return f"{h:02d}:{m:02d}"

    def __add__(self, other: DuracaoMinutos) -> DuracaoMinutos:
        """Soma duas durações.

        >>> (DuracaoMinutos(30) + DuracaoMinutos(45)).minutes
        75
        """
        return DuracaoMinutos(self.minutes + other.minutes)

    def __sub__(self, other: DuracaoMinutos) -> DuracaoMinutos:
        """Subtrai durações com piso em 0 minutos.

        >>> (DuracaoMinutos(90) - DuracaoMinutos(15)).minutes
        75
        >>> (DuracaoMinutos(10) - DuracaoMinutos(20)).minutes
        0
        """
        return DuracaoMinutos(max(0, self.minutes - other.minutes))

    # Comparações ricas para facilitar testes e regras
    def __lt__(self, other: "DuracaoMinutos") -> bool:
        """True se esta duração for menor que a outra.

        >>> DuracaoMinutos(59) < DuracaoMinutos(60)
        True
        """
        return self.minutes < other.minutes

    def __le__(self, other: "DuracaoMinutos") -> bool:
        """True se esta duração for menor ou igual à outra.

        >>> DuracaoMinutos(60) <= DuracaoMinutos(60)
        True
        """
        return self.minutes <= other.minutes

    def __eq__(self, other: object) -> bool:
        """Compara igualdade pela quantidade de minutos.

        >>> DuracaoMinutos(15) == DuracaoMinutos(15)
        True
        >>> DuracaoMinutos(15) == DuracaoMinutos(16)
        False
        """
        if not isinstance(other, DuracaoMinutos):
            return False
        return self.minutes == other.minutes

    def to_timedelta(self):
        """Converte para ``datetime.timedelta``.

        >>> DuracaoMinutos(90).to_timedelta()
        datetime.timedelta(seconds=5400)
        """
        from datetime import timedelta

        return timedelta(minutes=self.minutes)

    @staticmethod
    def from_timedelta(td: timedelta) -> "DuracaoMinutos":
        """Cria uma duração a partir de um ``timedelta``.

        >>> DuracaoMinutos.from_timedelta(timedelta(hours=2)).minutes
        120
        """
        return DuracaoMinutos(int(td.total_seconds() // 60))

    @staticmethod
    def sum(values: Sequence["DuracaoMinutos"]) -> "DuracaoMinutos":
        """Soma uma sequência de durações.

        >>> DuracaoMinutos.sum([DuracaoMinutos(10), DuracaoMinutos(20)]).minutes
        30
        """
        return DuracaoMinutos(sum(v.minutes for v in values))

    def scaled(self, factor: float) -> "DuracaoMinutos":
        """Retorna uma nova duração escalonada pelo fator.

        >>> DuracaoMinutos(60).scaled(1.5).to_hhmm()
        '01:30'
        """
        return DuracaoMinutos(int(round(self.minutes * factor)))


# -------------------- Small Value Objects --------------------


@dataclass(frozen=True, slots=True)
class Matricula:
    value: str

    def __str__(self) -> str:
        """Retorna a string da matrícula.

        >>> str(Matricula('25962'))
        '25962'
        """
        return self.value


@dataclass(frozen=True, slots=True)
class Percentual:
    value: float  # 0..100

    def __post_init__(self):
        # clamp para segurança
        v = 0.0 if self.value < 0 else 100.0 if self.value > 100 else self.value
        object.__setattr__(self, "value", round(v, 2))

    @staticmethod
    def from_string(s: str) -> Percentual:
        """Cria a partir de strings como '85,5%' ou '85.5'.

        >>> float(Percentual.from_string('85,5%'))
        85.5
        >>> str(Percentual.from_string('200'))  # clamp em 100
        '100.00%'
        """
        s = (s or "").strip().replace("%", "").strip()
        s = s.replace(".", "").replace(",", ".") if "," in s else s
        try:
            return Percentual(float(s))
        except Exception:
            return Percentual(0.0)

    def __float__(self) -> float:
        """Valor numérico entre 0 e 100.

        >>> float(Percentual(12.345))
        12.35
        """
        return self.value

    def __str__(self) -> str:
        """Formata com duas casas e símbolo %.

        >>> str(Percentual(12.3))
        '12.30%'
        """
        return f"{self.value:.2f}%"


class Sistema(Enum):
    SIGA = "SIGA"


@dataclass(frozen=True, slots=True)
class TotalCount:
    value: int

    def __post_init__(self):
        v = self.value if self.value >= 0 else 0
        object.__setattr__(self, "value", v)

    def __int__(self) -> int:
        """Inteiro não negativo.

        >>> int(TotalCount(-5))
        0
        """
        return self.value


@dataclass(frozen=True, slots=True)
class MeioPeriodo:
    """Um período de trabalho (entrada -> saída).

    >>> m = MeioPeriodo(HoraMinuto.from_string('07:50'), HoraMinuto.from_string('12:04'))
    >>> m.duracao.to_hhmm()
    '04:14'
    >>> str(m)
    '07:50-12:04'
    """

    entrada: HoraMinuto
    saida: HoraMinuto

    def __post_init__(self):
        if self.saida < self.entrada:
            raise ValueError("Saída não pode ser antes da entrada")

    @property
    def duracao(self) -> DuracaoMinutos:
        """Duração entre entrada e saída.

        >>> MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,30)).duracao.to_hhmm()
        '01:30'
        """
        a = self.entrada.minutes_since_midnight()
        b = self.saida.minutes_since_midnight()
        return DuracaoMinutos(b - a)

    def __str__(self) -> str:
        """Formata como 'HH:MM-HH:MM'.

        >>> str(MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,0)))
        '08:00-09:00'
        """
        return f"{self.entrada}-{self.saida}"

    def overlaps(self, other: "MeioPeriodo") -> bool:
        """Retorna True se os períodos se sobrepõem.

        >>> MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,0)).overlaps(MeioPeriodo(HoraMinuto(8,30), HoraMinuto(9,30)))
        True
        >>> MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,0)).overlaps(MeioPeriodo(HoraMinuto(9,0), HoraMinuto(10,0)))
        False
        """
        return not (self.saida <= other.entrada or other.saida <= self.entrada)

    def contains_time(self, t: HoraMinuto) -> bool:
        """True se t estiver dentro do período (fechado nos extremos).

        >>> MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,0)).contains_time(HoraMinuto(8,0))
        True
        >>> MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,0)).contains_time(HoraMinuto(9,1))
        False
        """
        return self.entrada <= t <= self.saida

    def gap_to(self, next_period: "MeioPeriodo") -> DuracaoMinutos:
        """Gap entre este período e o próximo (0 se sobrepõe ou encosta).

        >>> MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,0)).gap_to(MeioPeriodo(HoraMinuto(10,0), HoraMinuto(11,0))).to_hhmm()
        '01:00'
        >>> MeioPeriodo(HoraMinuto(8,0), HoraMinuto(9,0)).gap_to(MeioPeriodo(HoraMinuto(9,0), HoraMinuto(10,0))).to_hhmm()
        '00:00'
        """
        if next_period.entrada <= self.saida:
            return DuracaoMinutos(0)
        return next_period.entrada.diff(self.saida)


@dataclass(frozen=True, slots=True)
class PeriodoCompleto:
    periodos: list[MeioPeriodo]

    def total_duracao(self) -> DuracaoMinutos:
        """Soma das durações dos períodos.

        >>> pc = PeriodoCompleto([MeioPeriodo(HoraMinuto(8,0), HoraMinuto(12,0)), MeioPeriodo(HoraMinuto(13,0), HoraMinuto(17,0))])
        >>> pc.total_duracao().to_hhmm()
        '08:00'
        """
        total = 0
        for p in self.periodos:
            total += p.duracao.minutes
        return DuracaoMinutos(total)

    def tem_dois_periodos_ou_mais(self) -> bool:
        """Verifica se há dois ou mais períodos.

        >>> pc = PeriodoCompleto([MeioPeriodo(HoraMinuto(8,0), HoraMinuto(12,0)), MeioPeriodo(HoraMinuto(13,0), HoraMinuto(17,0))])
        >>> pc.tem_dois_periodos_ou_mais()
        True
        >>> pc = PeriodoCompleto([MeioPeriodo(HoraMinuto(8,0), HoraMinuto(12,0))])
        >>> pc.tem_dois_periodos_ou_mais()
        False
        """
        return len(self.periodos) >= 2

    def eh_consistente_com_carga_horaria(
        self, carga_horaria: DuracaoMinutos, tolerancia_min: int = 0
    ) -> bool:
        """Compara total de períodos com carga_horaria, com tolerância.

        >>> pc = PeriodoCompleto([MeioPeriodo(HoraMinuto(8,0), HoraMinuto(12,0)), MeioPeriodo(HoraMinuto(13,0), HoraMinuto(17,0))])
        >>> pc.eh_consistente_com_carga_horaria(DuracaoMinutos(480))
        True
        >>> pc.eh_consistente_com_carga_horaria(DuracaoMinutos(450), tolerancia_min=20)
        True
        >>> pc.eh_consistente_com_carga_horaria(DuracaoMinutos(450), tolerancia_min=10)
        False
        """
        diff = abs(self.total_duracao().minutes - carga_horaria.minutes)
        return diff <= max(0, tolerancia_min)

    def alterar_periodos(self, novos_periodos: list[MeioPeriodo]) -> PeriodoCompleto:
        """Retorna novo PeriodoCompleto com os períodos alterados.

        >>> pc = PeriodoCompleto([MeioPeriodo(HoraMinuto(8,0), HoraMinuto(12,0))])
        >>> pc2 = pc.alterar_periodos([MeioPeriodo(HoraMinuto(13,0), HoraMinuto(17,0))])
        >>> len(pc.periodos)
        1
        >>> len(pc2.periodos)
        1
        >>> str(pc2.periodos[0])
        '13:00-17:00'
        """
        return PeriodoCompleto(novos_periodos)


# -------------------- Entities/Aggregates --------------------


@dataclass(frozen=True, slots=True)
class Analista:
    """Entidade analista.

    >>> Analista(matricula='25962', nome='ARTHUR')
    Analista(matricula='25962', nome='ARTHUR')
    """

    matricula: Matricula
    nome: str


@dataclass(slots=True)
class DiaDeTrabalho:
    """Agregado que modela um dia de trabalho.

    Mantém batidas (pontos registrados), períodos derivados, carga horária e tempo registrado.
    """

    data: date
    carga_horaria: DuracaoMinutos
    tempo_registrado: DuracaoMinutos
    batidas: list[HoraMinuto]

    @staticmethod
    def parse_batidas(ponto_registrado: str) -> list[HoraMinuto]:
        """Converte string CSV de batidas para lista de HoraMinuto.

        >>> DiaDeTrabalho.parse_batidas('08:00, 12:00, 13:00, 18:00')
        [HoraMinuto(hour=8, minute=0), HoraMinuto(hour=12, minute=0), HoraMinuto(hour=13, minute=0), HoraMinuto(hour=18, minute=0)]
        >>> DiaDeTrabalho.parse_batidas('inválido, 08:00')  # ignora inválidos
        [HoraMinuto(hour=8, minute=0)]
        """
        tokens = [t.strip() for t in (ponto_registrado or "").split(",") if t.strip()]
        batidas: list[HoraMinuto] = []
        for t in tokens:
            try:
                batidas.append(HoraMinuto.from_string(t))
            except Exception:
                # Ignora tokens inválidos
                continue
        return batidas

    @staticmethod
    def _periodos_from_batidas(batidas: Sequence[HoraMinuto]) -> list[MeioPeriodo]:
        """Agrupa batidas em pares (entrada, saída) válidos.

        >>> b = [HoraMinuto(8,0), HoraMinuto(12,0), HoraMinuto(13,0), HoraMinuto(17,0)]
        >>> [str(p) for p in DiaDeTrabalho._periodos_from_batidas(b)]
        ['08:00-12:00', '13:00-17:00']
        """
        periodos: list[MeioPeriodo] = []
        for i in range(0, len(batidas) - 1, 2):
            e, s = batidas[i], batidas[i + 1]
            if s < e:
                # ignora par inconsistente
                continue
            periodos.append(MeioPeriodo(e, s))
        return periodos

    @property
    def periodos(self) -> list[MeioPeriodo]:
        """Períodos derivados das batidas."""
        return self._periodos_from_batidas(self.batidas)

    @property
    def total_minutos_periodos(self) -> DuracaoMinutos:
        """Soma das durações dos períodos.

        >>> d = DiaDeTrabalho(date.today(), DuracaoMinutos(480), DuracaoMinutos(0), [HoraMinuto(8,0), HoraMinuto(12,0)])
        >>> d.total_minutos_periodos.to_hhmm()
        '04:00'
        """
        total = 0
        for p in self.periodos:
            total += p.duracao.minutes
        return DuracaoMinutos(total)

    def percentual_registrado(self) -> float | None:
        """Percentual do tempo oficialmente registrado em relação à carga.

        >>> d = DiaDeTrabalho(date.today(), DuracaoMinutos(480), DuracaoMinutos(240), [])
        >>> d.percentual_registrado()
        50.0
        """
        if self.carga_horaria.minutes <= 0:
            return None
        return round(
            (self.tempo_registrado.minutes / self.carga_horaria.minutes) * 100, 2
        )

    def faltam_batidas(self) -> bool:
        """True se número de batidas for ímpar (faltando saída)."""
        return len(self.batidas) % 2 == 1

    def completar_batidas(
        self,
        horarios_esperados: Sequence[MeioPeriodo],
        *,
        mode: Literal["append", "add_missing"] = "append",
    ) -> None:
        """Completa batidas faltantes segundo o padrão esperado.

        Modos suportados
        ----------------
        - "append" (padrão): assume que ``horarios_esperados`` descreve o dia completo
          na ordem cronológica e adiciona as batidas que faltam a partir da
          quantidade já existente. Não reordena nem substitui.
        - "add_missing": para cada batida esperada, adiciona ao final se ainda não
          existir na lista atual (útil quando você passa apenas um meio-período,
          por exemplo só a tarde).

        Exemplos
        --------
        >>> d = DiaDeTrabalho(
        ...     data=date(2025, 1, 1),
        ...     carga_horaria=DuracaoMinutos.from_hhmm('08:00'),
        ...     tempo_registrado=DuracaoMinutos.from_hhmm('02:30'),
        ...     batidas=[HoraMinuto.from_string('07:50'), HoraMinuto.from_string('12:04')]
        ... )
        >>> d.completar_batidas([MeioPeriodo(HoraMinuto.from_string('13:58'), HoraMinuto.from_string('18:16'))])
        >>> [str(b) for b in d.batidas]
        ['07:50', '12:04', '13:58', '18:16']

        Passando apenas o período da tarde
        ----------------------------------
        >>> d2 = DiaDeTrabalho(
        ...     data=date(2025, 1, 1),
        ...     carga_horaria=DuracaoMinutos.from_hhmm('08:00'),
        ...     tempo_registrado=DuracaoMinutos.from_hhmm('02:00'),
        ...     batidas=[HoraMinuto(8, 0), HoraMinuto(10, 0)]
        ... )
        >>> d2.completar_batidas([MeioPeriodo(HoraMinuto(13, 0), HoraMinuto(17, 0))], mode='add_missing')
        >>> [str(b) for b in d2.batidas]
        ['08:00', '10:00', '13:00', '17:00']
        """
        esperadas: list[HoraMinuto] = []
        for mp in horarios_esperados:
            esperadas.append(mp.entrada)
            esperadas.append(mp.saida)

        if not esperadas:
            return

        if mode not in {"append", "add_missing"}:
            raise ValueError("mode deve ser 'append' ou 'add_missing'")

        if mode == "append":
            if len(self.batidas) >= len(esperadas):
                return
            faltantes = esperadas[len(self.batidas) :]
            self.batidas.extend(faltantes)
        else:  # add_missing
            existentes = {(b.hour, b.minute) for b in self.batidas}
            for hm in esperadas:
                key = (hm.hour, hm.minute)
                if key not in existentes:
                    self.batidas.append(hm)
                    existentes.add(key)

    # --------- Novos utilitários ---------
    def minutos_trabalhados(self) -> DuracaoMinutos:
        """Minutos trabalhados derivados dos períodos."""
        return self.total_minutos_periodos

    def horas_restantes(self) -> DuracaoMinutos:
        """Horas restantes com base no tempo_registrado oficial."""
        return self.carga_horaria - self.tempo_registrado

    def is_consistente(self, tolerancia_min: int = 0) -> bool:
        """Compara total de períodos com tempo_registrado, com tolerância.

        >>> d = DiaDeTrabalho(date.today(), DuracaoMinutos(480), DuracaoMinutos(240), [HoraMinuto(8,0), HoraMinuto(12,1)])
        >>> d.is_consistente(tolerancia_min=2)
        True
        """
        diff = abs(self.total_minutos_periodos.minutes - self.tempo_registrado.minutes)
        return diff <= max(0, tolerancia_min)

    def recomputar_tempo_registrado(self) -> None:
        """Define tempo_registrado como a soma dos períodos derivados."""
        self.tempo_registrado = self.total_minutos_periodos

    def proxima_batida_esperada(self) -> str:
        """'entrada' ou 'saida' conforme o número atual de batidas."""
        return "entrada" if len(self.batidas) % 2 == 0 else "saida"

    def adicionar_batida(self, hm: HoraMinuto) -> None:
        """Adiciona batida mantendo ordenação e evitando duplicados consecutivos."""
        # Insere mantendo ordenação e evitando duplicados imediatos
        if not self.batidas:
            self.batidas.append(hm)
            return
        if self.batidas[-1] == hm:
            return
        if hm >= self.batidas[-1]:
            self.batidas.append(hm)
        else:
            # insere ordenado
            for i, b in enumerate(self.batidas):
                if hm < b:
                    self.batidas.insert(i, hm)
                    break

    def registrar_periodo(self, mp: MeioPeriodo) -> None:
        """Atalho para inserir as duas batidas do período."""
        self.adicionar_batida(mp.entrada)
        self.adicionar_batida(mp.saida)


@dataclass(slots=True)
class PendenciaLancamentos:
    """Uma pendência (um dia) de lançamentos para um analista."""

    analista: Analista
    dia: DiaDeTrabalho
    percentual: Percentual | None = None

    # --------- Factories (XML) ---------
    @staticmethod
    def _safe_text(node: ET.Element | None) -> str:
        """Extrai texto do nó, retornando '' se None."""
        if node is None or node.text is None:
            return ""
        return node.text.strip()

    @classmethod
    def from_item_node(cls, item: ET.Element) -> PendenciaLancamentos:
        """Cria uma pendência a partir de um nó <pendencias_lançamentos> (item).

        Exemplo mínimo de XML de item
        ----------------------------
        <pendencias_lançamentos>
            <analista>25962</analista>
            <nome_analista>ARTHUR</nome_analista>
            <dt_atendimento>01/01/25</dt_atendimento>
            <carga_horaria>08:00</carga_horaria>
            <tempo_registrado>02:00</tempo_registrado>
            <percentual>25,00%</percentual>
            <ponto_registrado>08:00, 12:00</ponto_registrado>
        </pendencias_lançamentos>
        """

        def gx(tag: str) -> str:
            return cls._safe_text(item.find(tag))

        matricula = Matricula(gx("analista"))
        nome = gx("nome_analista")
        dt_str = gx("dt_atendimento")
        ch = gx("carga_horaria") or "00:00"
        tr = gx("tempo_registrado") or "00:00"
        perc_str = gx("percentual")
        ponto = gx("ponto_registrado")

        try:
            dt = datetime.strptime(dt_str, "%d/%m/%y").date()
        except Exception:
            dt = date.today()

        batidas = DiaDeTrabalho.parse_batidas(ponto)
        dia = DiaDeTrabalho(
            data=dt,
            carga_horaria=DuracaoMinutos.from_hhmm(ch),
            tempo_registrado=DuracaoMinutos.from_hhmm(tr),
            batidas=batidas,
        )
        analista = Analista(matricula=matricula, nome=nome)

        return cls(
            analista=analista,
            dia=dia,
            percentual=Percentual.from_string(perc_str) if perc_str else None,
        )

    # --------- Consultas/derivações ---------
    def minutos_pendentes(self) -> DuracaoMinutos:
        # com base nos campos oficiais informados no item
        return self.dia.carga_horaria - self.dia.tempo_registrado

    def faltam_batidas(self) -> bool:
        return self.dia.faltam_batidas()

    def percentual_registrado_float(self) -> float | None:
        return self.dia.percentual_registrado()


@dataclass(frozen=True, slots=True)
class PendenciasLancamentos:
    """Agregado que representa o retorno completo do XML com várias pendências.

    - matricula: matrícula alvo da consulta (do elemento raiz)
    - total: número de itens pendentes (do elemento raiz)
    - sistema: identificador do sistema (do elemento raiz)
    - itens: lista de pendências individuais (um dia por item)
    """

    matricula: Matricula | None
    total: TotalCount | None
    sistema: Sistema | None
    itens: list[PendenciaLancamentos]

    @classmethod
    def from_xml(cls, xml: str) -> PendenciasLancamentos:
        """Interpreta o XML raiz e popula o agregado completo.

        Inclui metadados do elemento raiz (matricula, total, sistema) e
        uma lista de itens (um por dia pendente).
        """
        root = ET.fromstring(xml)
        meta = dict(root.attrib)
        matricula = Matricula(meta["matricula"]) if "matricula" in meta else None
        total: TotalCount | None
        try:
            total = TotalCount(int(meta["total"])) if "total" in meta else None
        except Exception:
            total = None
        sistema = Sistema(meta["sistema"]) if "sistema" in meta else None

        itens: list[PendenciaLancamentos] = []
        # Cada filho <pendencias_lançamentos> representa um dia
        for child in list(root):
            if child.tag != "pendencias_lançamentos":
                continue
            itens.append(PendenciaLancamentos.from_item_node(child))

        # Caso o XML tenha vindo como item único sem filho, tentar interpretar o root
        if not itens and root.tag == "pendencias_lançamentos":
            itens.append(PendenciaLancamentos.from_item_node(root))

        return cls(matricula=matricula, total=total, sistema=sistema, itens=itens)

    # --------- Operações sobre coleção ---------
    def total_dias(self) -> int:
        """Quantidade de dias pendentes.

        >>> PendenciasLancamentos(None, None, None, []).total_dias()
        0
        """
        return len(self.itens)

    def dias_com_falta_batida(self) -> list[PendenciaLancamentos]:
        """Filtra itens com batidas ímpares."""
        return [p for p in self.itens if p.faltam_batidas()]

    def minutos_pendentes_totais(self) -> DuracaoMinutos:
        """Soma dos minutos pendentes dos itens."""
        return DuracaoMinutos.sum([p.minutos_pendentes() for p in self.itens])

    def completar_batidas_todos(
        self,
        horarios_esperados: Sequence[MeioPeriodo],
        *,
        mode: Literal["append", "add_missing"] = "append",
    ) -> None:
        """Completa batidas faltantes de todos os itens conforme um padrão esperado.

        Comportamento
        -------------
        - Converte a sequência de ``MeioPeriodo`` em uma lista linear de batidas
            esperadas [entrada1, saída1, entrada2, saída2, ...].
                - Para cada item do agregado:
                    - Em mode="append": se o número de batidas atual é menor que o número de
                        batidas esperadas, anexa (append-only) as batidas faltantes ao final,
                        sem reordenar nem substituir batidas já existentes.
                    - Em mode="add_missing": para cada batida esperada, adiciona ao final se
                        ainda não existir na lista do item (não reordena o que já existe).
        - Se um item já tem o mesmo número (ou mais) de batidas que o esperado, nada é feito para esse item.
        - Operação destrutiva: modifica os objetos ``DiaDeTrabalho`` in place.

        Exemplos
        --------
        >>> agg = PendenciasLancamentos(
        ...     matricula=Matricula('25962'),
        ...     total=TotalCount(1),
        ...     sistema=Sistema.SIGA,
        ...     itens=[
        ...         PendenciaLancamentos(
        ...             analista=Analista(matricula=Matricula('25962'), nome='ARTHUR'),
        ...             dia=DiaDeTrabalho(
        ...                 data=date(2025, 1, 1),
        ...                 carga_horaria=DuracaoMinutos.from_hhmm('08:00'),
        ...                 tempo_registrado=DuracaoMinutos.from_hhmm('02:00'),
        ...                 batidas=[HoraMinuto(8, 0), HoraMinuto(10, 0)]
        ...             )
        ...         )
        ...     ]
        ... )
        >>> esperado = [MeioPeriodo(HoraMinuto(13, 0), HoraMinuto(17, 0))]
        >>> agg.completar_batidas_todos(esperado, mode='add_missing')
        >>> [str(b) for b in agg.itens[0].dia.batidas]
        ['08:00', '10:00', '13:00', '17:00']
        """
        for p in self.itens:
            p.dia.completar_batidas(horarios_esperados, mode=mode)
