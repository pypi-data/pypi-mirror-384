def docs() -> str:
    return """
Edita as informações de um atendimento de Ordem de Serviço (OS) no sistema SIGA.

**INSTRUÇÃO PARA O AGENTE IA:**
ANTES de executar esta função de edição:
1. SEMPRE chame primeiro `buscar_informacoes_atendimentos_os(codigo_atendimento, codigo_analista)`
2. MOSTRE ao usuário os dados atuais vs. dados que serão alterados
3. PEÇA confirmação explícita do usuário: "Confirma as alterações? (sim/não)"
4. SÓ EXECUTE esta função se o usuário confirmar explicitamente

Esta função permite atualizar todos os campos de um atendimento existente, incluindo
datas, descrição, tipo, tempo gasto e flags de controle. Realiza validação do tipo
de atendimento e conversão automática de datas para o formato esperado pelo SIGA.

**Funcionalidade de busca automática:**
Se o atendimento não for encontrado nesta função (atendimentos OS), a mensagem de erro orientará
a buscar nas funções editar_atendimento_avulso_sistemas ou editar_atendimento_avulso_infraestrutura,
permitindo busca automática entre os tipos de atendimento.


**Endpoint utilizado:** `updateAtendimentosOsSigaIA`

**Estrutura do XML retornado:**
```xml
<ordens_servico os="123" dataIni="2024-01-15 09:00:00" analista="456"
                descricao="Descrição" tipo="Implementação" dataFim="2024-01-15 17:00:00"
                tempoGasto="480" primeiroAtendimento="False" apresentaSolucao="True"
                sistema="SIGA">
    <ordem_servico sistema="SIGA">
        <status>sucesso</status>
        <mensagem>Atendimento editado com sucesso!</mensagem>
    </ordem_servico>
</ordens_servico>
```

**Em caso de erro de validação:**
```xml
<erro_validacao sistema="SIGA" funcao="editar_atendimentos_os">
    <erro sistema="SIGA">
        <status>erro</status>
        <tipo_erro>tipo_invalido</tipo_erro>
        <tipo_informado>Tipo Inválido</tipo_informado>
        <mensagem>Tipo 'Tipo Inválido' não encontrado na constante TYPE_TO_NUMBER</mensagem>
        <tipos_validos>['Suporte Sistema', 'Implementação', ...]</tipos_validos>
    </erro>
</erro_validacao>
```

**Em caso de erro (atendimento não encontrado):**
```xml
<ordens_servico os="123" dataIni="2024-01-15 09:00:00" analista="456"
                descricao="Descrição" tipo="Implementação" dataFim="2024-01-15 17:00:00"
                tempoGasto="480" primeiroAtendimento="False" apresentaSolucao="True"
                sistema="SIGA">
    <ordem_servico sistema="SIGA">
        <status>erro</status>
        <mensagem>Atendimento não encontrado em Atendimentos OS. Este código pode estar em atendimento avulso (sistemas ou infraestrutura). Tente buscar nas funções: editar_atendimento_avulso_sistemas ou editar_atendimento_avulso_infraestrutura.</mensagem>
    </ordem_servico>
</ordens_servico>
```

**Em caso de outros erros:**
```xml
<ordens_servico os="123" dataIni="2024-01-15 09:00:00" analista="456"
                descricao="Descrição" tipo="Implementação" dataFim="2024-01-15 17:00:00"
                tempoGasto="480" primeiroAtendimento="False" apresentaSolucao="True"
                sistema="SIGA">
    <ordem_servico sistema="SIGA">
        <status>erro</status>
        <mensagem>Erro ao editar o atendimento. Tente novamente.</mensagem>
    </ordem_servico>
</ordens_servico>
```

Args:
    codigo_atendimento (int): Código único do atendimento a ser editado
    codigo_os (int): Código da Ordem de Serviço à qual o atendimento pertence
    data_inicio (str): Data e hora de início do atendimento (formato aceito pelo converter_data_siga)
    codigo_analista (int): Matrícula do analista/usuário responsável pelo atendimento
    descricao_atendimento (str): Descrição detalhada do atendimento realizado
    tipo_atendimento (Literal): Tipo do atendimento, deve ser um dos valores válidos:
        - "Suporte Sistema" (código 1)
        - "Implementação" (código 2) - padrão
        - "Manutenção Corretiva" (código 3)
        - "Reunião" (código 4)
        - "Treinamento" (código 5)
        - "Mudança de Escopo" (código 20)
        - "Anexo" (código 12)
        - "Suporte Infraestrutura" (código 13)
        - "Monitoramento" (código 21)
        - "Incidente" (código 23)
        - "Requisição" (código 24)
    data_fim (str | Literal | None, optional): Data e hora de fim do atendimento.
        Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem".
        Se None, será enviado como string vazia. Defaults to None.
    primeiro_atendimento (bool, optional): Flag indicando se é o primeiro atendimento da OS.
        Defaults to False.
    apresenta_solucao (bool, optional): Flag indicando se o atendimento apresenta solução.
        Defaults to False.

Returns:
    str: XML formatado contendo:
        - Em caso de sucesso: confirmação da edição com status "sucesso"
        - Em caso de atendimento não encontrado: status "erro" com orientação para buscar em funções de atendimento avulso 
        - Em caso de outros erros de API: status "erro" com mensagem explicativa 
        - Em caso de erro de validação: detalhes do erro com tipos válidos 
        - Em caso de erro interno: mensagem de erro genérica

        O XML sempre inclui os parâmetros enviados como atributos do elemento raiz.

Raises:
    Não levanta exceções diretamente. Todos os erros são capturados e retornados
    como XML formatado com informações detalhadas do erro.

Examples:
    >>> # Editar atendimento básico
    >>> xml = await editar_atendimentos_os(
    ...     codigo_atendimento=123,
    ...     codigo_os=456,
    ...     data_inicio="2024-01-15 09:00:00",
    ...     codigo_analista=789,
    ...     descricao_atendimento="Implementação de nova funcionalidade",
    ...     tipo_atendimento="Implementação"
    ... )

    >>> # Editar atendimento completo com solução
    >>> xml = await editar_atendimentos_os(
    ...     codigo_atendimento=123,
    ...     codigo_os=456,
    ...     data_inicio="hoje 09:00",
    ...     codigo_analista=789,
    ...     descricao_atendimento="Correção de bug crítico",
    ...     tipo_atendimento="Manutenção Corretiva",
    ...     data_fim="hoje 17:00",
    ...     primeiro_atendimento=True,
    ...     apresenta_solucao=True
    ... )

    >>> # Exemplo quando não encontra (orienta busca automática)
    >>> xml = await editar_atendimentos_os(
    ...     codigo_atendimento=99999,
    ...     codigo_os=456,
    ...     data_inicio="2024-01-15 09:00:00",
    ...     codigo_analista=789,
    ...     descricao_atendimento="Teste",
    ...     tipo_atendimento="Implementação"
    ... )
    # Retorna XML orientando buscar nas funções de atendimento avulso

    >>> # Exemplo com tipo inválido (retorna erro)
    >>> xml = await editar_atendimentos_os(
    ...     codigo_atendimento=123,
    ...     codigo_os=456,
    ...     data_inicio="2024-01-15 09:00:00",
    ...     codigo_analista=789,
    ...     descricao_atendimento="Teste",
    ...     tipo_atendimento="Tipo Inexistente"  # Erro!
    ... )

Notes:
    - ATENÇÃO: Esta operação modifica permanentemente os dados do atendimento 
    - DIFERENCIAÇÃO DE TIPOS: Esta função é específica para atendimentos OS. Para atendimentos avulsos, use as funções específicas
    - Para busca automática: Se não encontrar nesta função, use as funções de edição de atendimento avulso com os mesmos parâmetros
    - A função realiza validação case-insensitive do tipo_atendimento
    - As datas são automaticamente convertidas usando converter_data_siga com manter_horas=True
    - A função utiliza a constante TYPE_TO_NUMBER para mapear tipos para códigos numéricos
    - Todos os parâmetros enviados são incluídos como atributos no XML de resposta
    - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
    - Em caso de falha na requisição HTTP, retorna erro interno formatado em XML
"""
