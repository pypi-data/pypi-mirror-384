def docs() -> str:
    return """
Calcula e lista o total de horas trabalhadas de um analista em um período específico.

Esta função consolida as horas trabalhadas de um analista considerando tanto os
atendimentos de Ordens de Serviço (OS) quanto os atendimentos avulsos realizados
no período especificado. Fornece um resumo completo da produtividade do analista.

**Endpoint utilizado:** `buscarTotalHorasTrabalhadasSigaIA`

**Estrutura do XML retornado:**
```xml
<atendimentos_avulsos matricula="123" sistema="SIGA">
    <atendimentos_avulsos sistema="SIGA">
        <total_horas_os>32.5</total_horas_os>
        <total_horas_avulsos>8.0</total_horas_avulsos>
        <total_horas_geral>40.5</total_horas_geral>
        <periodo_inicio>2024-01-15</periodo_inicio>
        <periodo_fim>2024-01-19</periodo_fim>
        <dias_trabalhados>5</dias_trabalhados>
        <media_horas_dia>8.1</media_horas_dia>
    </atendimentos_avulsos>
</atendimentos_avulsos>
```

**Em caso de erro:**
```
Erro ao listar horas trabalhadas.
```

Args:
    matricula (str | int | Literal["CURRENT_USER"], optional): Matrícula do analista cujas horas
        trabalhadas serão calculadas. Se "CURRENT_USER", calcula para o usuário atual
            (matrícula do .env). Defaults to "CURRENT_USER".
    data_inicio (str | Literal): Data de início do período para cálculo das horas.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Este parâmetro é obrigatório.
    data_fim (str | Literal): Data de fim do período para cálculo das horas.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Este parâmetro é obrigatório.

Returns:
    str: XML formatado contendo:
        - Total de horas trabalhadas em atendimentos de OS
        - Total de horas trabalhadas em atendimentos avulsos
        - Total geral de horas trabalhadas no período
        - Informações do período consultado (início e fim)
        - Estatísticas adicionais como dias trabalhados e média por dia
        - Atributos do elemento raiz incluem a matrícula consultada
        - Em caso de erro na requisição: mensagem de erro simples

        O XML sempre inclui o atributo "sistema" com valor "SIGA".

Raises:
    Não levanta exceções diretamente. Erros são capturados e retornados
    como string de erro simples.

Examples:
    >>> # Calcular horas trabalhadas de hoje
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=12345,
    ...     data_inicio="hoje",
    ...     data_fim="hoje"
    ... )

    >>> # Calcular horas trabalhadas da semana
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=12345,
    ...     data_inicio="2024-01-15",
    ...     data_fim="2024-01-19"
    ... )

    >>> # Calcular horas trabalhadas de ontem
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=12345,
    ...     data_inicio="ontem",
    ...     data_fim="ontem"
    ... )

    >>> # Calcular horas trabalhadas do mês
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=12345,
    ...     data_inicio="2024-01-01",
    ...     data_fim="2024-01-31"
    ... )

    >>> # Buscar sem especificar matrícula (se suportado pela API)
    >>> xml = await listar_horas_trabalhadas(
    ...     data_inicio="hoje",
    ...     data_fim="hoje"
    ... )

Notes:
    - As datas são automaticamente convertidas usando converter_data_siga() quando fornecidas
    - A função utiliza a API de cálculo de horas trabalhadas do sistema SIGA
    - O cálculo inclui tanto atendimentos de OS quanto atendimentos avulsos
    - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
    - Em caso de falha na requisição HTTP ou parsing JSON, retorna mensagem de erro simples
    - O parâmetro matricula usa o tipo Literal["CURRENT_USER"] para permitir valores opcionais
    - Os parâmetros data_inicio e data_fim são obrigatórios (não têm valor padrão)
    - A resposta da API é processada através do XMLBuilder para formatação consistente
    - Esta função é útil para relatórios de produtividade e controle de horas
    - O resultado consolida informações de múltiplas fontes (OS e atendimentos avulsos)
    - Pode incluir estatísticas adicionais como média de horas por dia trabalhado
"""
