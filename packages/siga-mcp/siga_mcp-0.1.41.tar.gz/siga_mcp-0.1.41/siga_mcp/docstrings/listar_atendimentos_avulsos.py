def docs() -> str:
    return """
Lista todos os atendimentos avulsos registrados por um usuário em um período específico.

**INSTRUÇÃO PARA O AGENTE IA:**
Para solicitações GENÉRICAS de listagem de atendimentos:
1. **SEMPRE execute AMBAS as funções**: `listar_atendimentos_os` E `listar_atendimentos_avulsos`
2. **Solicitações genéricas incluem**: "liste meus atendimentos", "mostre meus lançamentos", "atendimentos de hoje/ontem/semana", etc.
3. **COMBINE os resultados** de forma organizada para dar visão completa ao usuário
4. **Execute APENAS esta função** quando o usuário especificar explicitamente "atendimentos avulsos"
5. **Use os mesmos filtros** (datas, período) em ambas as funções para consistência

**EXEMPLOS DE SOLICITAÇÕES QUE REQUEREM AMBAS AS FUNÇÕES:**
- "Liste todos os meus atendimentos de hoje"
- "Mostre meus lançamentos da semana passada"  
- "Quais foram meus atendimentos de ontem?"
- "Atendimentos realizados este mês"

Esta função busca atendimentos avulsos (não vinculados a Ordens de Serviço) realizados
por um analista em um intervalo de datas. Os atendimentos avulsos são atividades
registradas independentemente de OSs específicas.

**Endpoint utilizado:** `buscarAtendimentosAvulsosSigaIA`

**Estrutura do XML retornado:**
```xml
<atendimentos_avulsos matricula="123" sistema="SIGA">
    <atendimentos_avulsos sistema="SIGA">
        <id>456</id>
        <matricula>123</matricula>
        <data_inicio>2024-01-15 09:00:00</data_inicio>
        <data_fim>2024-01-15 17:00:00</data_fim>
        <descricao>Atendimento avulso realizado</descricao>
        <tempo_gasto>480</tempo_gasto>
        <tipo>Suporte Sistema</tipo>
    </atendimentos_avulsos>
    <!-- Mais atendimentos... -->
</atendimentos_avulsos>
```

**Em caso de erro:**
```
Erro ao listar atendimentos avulsos.
```

Args:
    matricula (str | int | Literal["CURRENT_USER"]): Matrícula do usuário/analista cujos atendimentos
        avulsos serão listados. Se "CURRENT_USER", busca atendimentos do usuário atual
            (matrícula do .env). Defaults to "CURRENT_USER".
    data_inicio (str | Literal): Data de início do período de busca.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Este parâmetro é obrigatório.
    data_fim (str | Literal): Data de fim do período de busca.
        Aceita formatos de data ou palavras-chave "hoje" ou "ontem".
        Este parâmetro é obrigatório.

Returns:
    str: XML formatado contendo:
        - Lista de atendimentos avulsos encontrados no período
        - Cada atendimento inclui: id, matrícula, datas, descrição, tempo gasto, tipo
        - Atributos do elemento raiz incluem a matrícula consultada
        - Em caso de erro na requisição: mensagem de erro simples

        O XML sempre inclui o atributo "sistema" com valor "SIGA".

Raises:
    Não levanta exceções diretamente. Erros são capturados e retornados
    como string de erro simples.

Examples:
    >>> # Listar atendimentos avulsos de hoje
    >>> xml = await listar_atendimentos_avulsos(
    ...     matricula=12345,
    ...     data_inicio="hoje",
    ...     data_fim="hoje"
    ... )

    >>> # Listar atendimentos avulsos da semana passada
    >>> xml = await listar_atendimentos_avulsos(
    ...     matricula=12345,
    ...     data_inicio="2024-01-08",
    ...     data_fim="2024-01-12"
    ... )

    >>> # Listar atendimentos de ontem
    >>> xml = await listar_atendimentos_avulsos(
    ...     matricula=12345,
    ...     data_inicio="ontem",
    ...     data_fim="ontem"
    ... )

    >>> # Buscar sem especificar matrícula (se suportado pela API)
    >>> xml = await listar_atendimentos_avulsos(
    ...     data_inicio="hoje",
    ...     data_fim="hoje"
    ... )

Notes:
    - As datas são automaticamente convertidas usando converter_data_siga()
    - A função utiliza a API de atendimentos avulsos do sistema SIGA
    - Atendimentos avulsos são diferentes de atendimentos de OS (Ordens de Serviço)
    - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
    - Em caso de falha na requisição HTTP ou parsing JSON, retorna mensagem de erro simples
    - O parâmetro matricula usa o tipo Literal["CURRENT_USER"] para permitir valores opcionais
    - Os parâmetros data_inicio e data_fim são obrigatórios (não têm valor padrão)
    - A resposta da API é processada através do XMLBuilder para formatação consistente
"""
