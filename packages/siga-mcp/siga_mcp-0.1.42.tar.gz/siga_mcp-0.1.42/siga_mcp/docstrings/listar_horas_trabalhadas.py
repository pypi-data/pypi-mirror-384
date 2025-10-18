def docs() -> str:
    return """
Calcula e lista o total de horas trabalhadas de um ou múltiplos analistas em um período específico.

Esta função consolida as horas trabalhadas de analista(s) considerando tanto os
atendimentos de Ordens de Serviço (OS) quanto os atendimentos avulsos realizados
no período especificado. Fornece um resumo completo da produtividade do(s) analista(s).
Suporta busca individual ou em lote para otimização de performance.

**Endpoint utilizado:** `buscarTotalHorasTrabalhadasSigaIA`

**Estrutura do XML retornado (um analista):**
```xml
<atendimentos_avulsos matricula="123" sistema="SIGA">
    <atendimentos_avulsos sistema="SIGA">
        <QTD_HORAS>40:30</QTD_HORAS>
        <USUARIO>123</USUARIO>
        <NOME_ANALISTA>JOÃO DA SILVA</NOME_ANALISTA>
    </atendimentos_avulsos>
</atendimentos_avulsos>
```

**Estrutura do XML retornado (múltiplos analistas):**
```xml
<atendimentos_avulsos matricula="123,456,789" sistema="SIGA">
    <atendimentos_avulsos sistema="SIGA">
        <QTD_HORAS>40:30</QTD_HORAS>
        <USUARIO>123</USUARIO>
        <NOME_ANALISTA>JOÃO DA SILVA</NOME_ANALISTA>
    </atendimentos_avulsos>
    <atendimentos_avulsos sistema="SIGA">
        <QTD_HORAS>35:45</QTD_HORAS>
        <USUARIO>456</USUARIO>
        <NOME_ANALISTA>MARIA SANTOS</NOME_ANALISTA>
    </atendimentos_avulsos>
    <atendimentos_avulsos sistema="SIGA">
        <QTD_HORAS>42:15</QTD_HORAS>
        <USUARIO>789</USUARIO>
        <NOME_ANALISTA>PEDRO COSTA</NOME_ANALISTA>
    </atendimentos_avulsos>
</atendimentos_avulsos>
```

**Em caso de erro:**
```
Erro ao listar horas trabalhadas.
```

Args:
    matricula (str | int | list[str | int] | Literal["CURRENT_USER"], optional): 
        Matrícula do analista ou lista de matrículas dos analistas cujas horas
        trabalhadas serão calculadas. Se "CURRENT_USER", calcula para o usuário atual
        (matrícula do .env). Para múltiplos analistas, forneça uma lista de matrículas.
        Defaults to "CURRENT_USER".
    
    data_inicio (str | Literal): 
        Data de início do período para cálculo das horas.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Este parâmetro é obrigatório.
    
    data_fim (str | Literal): 
        Data de fim do período para cálculo das horas.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Este parâmetro é obrigatório.

Returns:
    str: XML formatado contendo:
        - **Individual**: Um elemento com horas trabalhadas do analista especificado
        - **Múltiplos**: Múltiplos elementos, um para cada analista, com suas respectivas horas
        - **QTD_HORAS**: Total de horas no formato "HH:MM" (ex: "40:30")
        - **USUARIO**: Matrícula do analista
        - **NOME_ANALISTA**: Nome completo do analista
        - **Atributo matricula**: Contém a(s) matrícula(s) consultada(s), separadas por vírgula se múltiplas
        - **Em caso de erro**: Mensagem de erro simples

        O XML sempre inclui o atributo "sistema" com valor "SIGA".
        Para múltiplas matrículas, o atributo "matricula" contém todas as matrículas separadas por vírgula.


Raises:
    Não levanta exceções diretamente. Erros são capturados e retornados como string de erro simples.

Examples:
    >>> # Calcular horas trabalhadas de hoje (usuário atual)
    >>> xml = await listar_horas_trabalhadas(
    ...     data_inicio="hoje",
    ...     data_fim="hoje"
    ... )

    >>> # Calcular horas trabalhadas de um analista específico
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=12345,
    ...     data_inicio="2024-01-15",
    ...     data_fim="2024-01-19"
    ... )

    >>> # Calcular horas trabalhadas de múltiplos analistas (OTIMIZAÇÃO)
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=[12345, 67890, 54321],
    ...     data_inicio="2024-01-15",
    ...     data_fim="2024-01-19"
    ... )

    >>> # Calcular horas trabalhadas de ontem
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=12345,
    ...     data_inicio="ontem",
    ...     data_fim="ontem"
    ... )

    >>> # Calcular horas trabalhadas do mês para uma equipe
    >>> matriculas_equipe = [12345, 67890, 54321, 98765]
    >>> xml = await listar_horas_trabalhadas(
    ...     matricula=matriculas_equipe,
    ...     data_inicio="2024-01-01",
    ...     data_fim="2024-01-31"
    ... )

    >>> # Fluxo completo: buscar equipe e calcular horas trabalhadas
    >>> xml_equipe = await listar_usuarios_equipe_por_gerente(
    ...     descricao_equipe="Equipe AVA"
    ... )
    >>> matriculas = extrair_matriculas_do_xml(xml_equipe)
    >>> xml_horas = await listar_horas_trabalhadas(
    ...     matricula=matriculas,
    ...     data_inicio="2024-01-15",
    ...     data_fim="2024-01-19"
    ... )

    >>> # Integração com equipe do usuário atual
    >>> xml_equipe = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="CURRENT_USER"
    ... )
    >>> matriculas = extrair_matriculas_do_xml(xml_equipe)
    >>> xml_horas = await listar_horas_trabalhadas(
    ...     matricula=matriculas,
    ...     data_inicio="hoje",
    ...     data_fim="hoje"
    ... )

Notes:
    - **OTIMIZAÇÃO**: Função otimizada para múltiplas matrículas - uma consulta em vez de N consultas
    - **COMPATIBILIDADE**: Mantém total compatibilidade com uso individual (uma matrícula)
    - **PERFORMANCE**: Para múltiplos analistas, utiliza consulta em lote no banco de dados
    - **INTEGRAÇÃO COM EQUIPES**: Use com extrair_matriculas_do_xml para relatórios de equipe completos
    - **FLUXO DE EQUIPES**: listar_usuarios_equipe_por_gerente → extrair_matriculas_do_xml → listar_horas_trabalhadas
    - As datas são automaticamente convertidas usando converter_data_siga() quando fornecidas
    - A função utiliza a API de cálculo de horas trabalhadas do sistema SIGA
    - O cálculo inclui tanto atendimentos de OS quanto atendimentos avulsos
    - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
    - Em caso de falha na requisição HTTP ou parsing JSON, retorna mensagem de erro simples
    - O parâmetro matricula aceita tanto valores individuais quanto listas
    - Os parâmetros data_inicio e data_fim são obrigatórios (não têm valor padrão)
    - A resposta da API é processada através do XMLBuilder para formatação consistente
    - Esta função é útil para relatórios de produtividade e controle de horas individuais ou por equipe
    - O resultado consolida informações de múltiplas fontes (OS e atendimentos avulsos)
    - **QTD_HORAS**: Formato "HH:MM" representando total de horas e minutos trabalhados
    - **ESCALABILIDADE**: Suporta desde consultas individuais até equipes inteiras em uma única chamada
"""
