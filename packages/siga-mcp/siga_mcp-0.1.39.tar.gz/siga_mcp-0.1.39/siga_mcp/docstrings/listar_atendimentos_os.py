def docs() -> str:
    return """
Lista todos os atendimentos de Ordens de Serviço (OS) de um usuário com filtros opcionais.

**INSTRUÇÃO PARA O AGENTE IA:**
Para solicitações GENÉRICAS de listagem de atendimentos:
1. **SEMPRE execute AMBAS as funções**: `listar_atendimentos_os` E `listar_atendimentos_avulsos`
2. **Solicitações genéricas incluem**: "liste meus atendimentos", "mostre meus lançamentos", "atendimentos de hoje/ontem/semana", etc.
3. **COMBINE os resultados** de forma organizada para dar visão completa ao usuário
4. **Execute APENAS esta função** quando o usuário especificar explicitamente "atendimentos OS" ou "atendimentos de ordem de serviço"
5. **Use os mesmos filtros** (datas, período) em ambas as funções para consistência

**EXEMPLOS DE SOLICITAÇÕES QUE REQUEREM AMBAS AS FUNÇÕES:**
- "Liste todos os meus atendimentos de hoje"
- "Mostre meus lançamentos da semana passada"  
- "Quais foram meus atendimentos de ontem?"
- "Atendimentos realizados este mês"

Esta função busca atendimentos vinculados a Ordens de Serviço realizados por um analista,
permitindo filtrar por OS específica, período de datas, ou buscar todos os atendimentos.
Diferente dos atendimentos avulsos, estes estão sempre associados a uma OS.

**Endpoint utilizado:** `buscarAtendimentosOsSigaIA`

**Estrutura do XML retornado:**
```xml
<atendimentos_os matricula="123" os="456" dataIni="2024-01-15"
                    dataFim="2024-01-16" sistema="SIGA">
    <atendimentos_os sistema="SIGA">
        <id>789</id>
        <codigo_os>456</codigo_os>
        <matricula>123</matricula>
        <data_inicio>2024-01-15 09:00:00</data_inicio>
        <data_fim>2024-01-15 17:00:00</data_fim>
        <descricao>Implementação de funcionalidade</descricao>
        <tipo>Implementação</tipo>
        <tempo_gasto>480</tempo_gasto>
        <primeiro_atendimento>true</primeiro_atendimento>
        <apresenta_solucao>false</apresenta_solucao>
    </atendimentos_os>
    <!-- Mais atendimentos... -->
</atendimentos_os>
```

**Em caso de erro:**
```
Erro ao listar atendimentos OS.
```

Args:
    matricula (str | int | Literal["CURRENT_USER"], optional): Matrícula do usuário/analista cujos
        atendimentos de OS serão listados. Se "CURRENT_USER", busca atendimentos do usuário atual
            (matrícula do .env). Defaults to "CURRENT_USER".
    codigo_os (str | int | None, optional): Código específico da Ordem de Serviço
        para filtrar atendimentos. Se None ou não fornecido, busca atendimentos
        de todas as OSs. Defaults to None.
    data_inicio (str | Literal | None, optional): Data de início do período de busca.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Se None, não aplica filtro de data inicial. Defaults to None.
    data_fim (str | Literal | None, optional): Data de fim do período de busca.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Se None, não aplica filtro de data final. Defaults to None.

Returns:
    str: XML formatado contendo:
        - Lista de atendimentos de OS encontrados com os filtros aplicados
        - Cada atendimento inclui: id, código da OS, matrícula, datas, descrição,
            tipo, tempo gasto, flags de primeiro atendimento e apresentação de solução
        - Atributos do elemento raiz incluem todos os parâmetros de filtro utilizados
        - Em caso de erro na requisição: mensagem de erro simples

        O XML sempre inclui o atributo "sistema" com valor "SIGA".

Raises:
    Não levanta exceções diretamente. Erros são capturados e retornados
    como string de erro simples.

Examples:
    >>> # Listar todos os atendimentos de OS de um usuário
    >>> xml = await listar_atendimentos_os(
    ...     matricula=12345
    ... )

    >>> # Listar atendimentos de uma OS específica
    >>> xml = await listar_atendimentos_os(
    ...     matricula=12345,
    ...     codigo_os=456
    ... )

    >>> # Listar atendimentos de OS de hoje
    >>> xml = await listar_atendimentos_os(
    ...     matricula=12345,
    ...     data_inicio="hoje",
    ...     data_fim="hoje"
    ... )

    >>> # Listar atendimentos de OS em período específico
    >>> xml = await listar_atendimentos_os(
    ...     matricula=12345,
    ...     data_inicio="2024-01-15",
    ...     data_fim="2024-01-20"
    ... )

    >>> # Listar atendimentos de OS específica em período
    >>> xml = await listar_atendimentos_os(
    ...     matricula=12345,
    ...     codigo_os=789,
    ...     data_inicio="ontem",
    ...     data_fim="hoje"
    ... )

    >>> # Buscar sem filtros específicos (todos os parâmetros opcionais)
    >>> xml = await listar_atendimentos_os()

Notes:
    - As datas são automaticamente convertidas usando converter_data_siga() quando fornecidas
    - A função utiliza a API de atendimentos de OS do sistema SIGA
    - Atendimentos de OS são diferentes de atendimentos avulsos (vinculados a OSs específicas)
    - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
    - Em caso de falha na requisição HTTP ou parsing JSON, retorna mensagem de erro simples
    - Todos os parâmetros são opcionais, permitindo buscas flexíveis
    - Parâmetros None ou vazios são enviados como strings vazias para a API
    - O parâmetro matricula usa o tipo Literal["CURRENT_USER"] para permitir valores verdadeiramente opcionais
    - A resposta da API é processada através do XMLBuilder para formatação consistente
    - Os atributos do XML de resposta refletem exatamente os filtros aplicados na busca
"""
