def docs() -> str:
    return """
Extrai matrículas de usuários do XML retornado pela função listar_usuarios_equipe_por_gerente.

Esta função utilitária assíncrona parseia o XML gerado por listar_usuarios_equipe_por_gerente e extrai
todas as matrículas encontradas, retornando uma lista limpa e pronta para uso em outras
funções do sistema. É especialmente útil para integração com a função listar_horas_trabalhadas,
permitindo buscar horas trabalhadas de toda uma equipe de forma otimizada.

A função trata automaticamente casos de XML malformado, elementos ausentes ou vazios,
garantindo sempre o retorno de uma lista válida (mesmo que vazia) sem quebrar o fluxo
de execução do código.

**Contexto de uso:** Integração entre funções de gestão de equipes e horas trabalhadas

**XML de entrada esperado:**
```xml
<usuarios_equipe_gerente matriculaGerente="8372" equipe="AVA" sistema="SIGA">
    <usuario_equipe_gerente sistema="SIGA">
        <usuario>25962</usuario>  <!-- ← MATRÍCULA EXTRAÍDA -->
        <nome>ARTHUR BRENNO RIBEIRO COELHO</nome>
        <equipe>AVA</equipe>
        <!-- outros campos... -->
    </usuario_equipe_gerente>
    <usuario_equipe_gerente sistema="SIGA">
        <usuario>24290</usuario>  <!-- ← MATRÍCULA EXTRAÍDA -->
        <nome>ARTHUR TOSTA MATIAS</nome>
        <equipe>AVA</equipe>
        <!-- outros campos... -->
    </usuario_equipe_gerente>
</usuarios_equipe_gerente>

**Resultado da extração:**
```python
["25962", "24290"]
```

**Casos especiais tratados:**
- **XML malformado**: Retorna lista vazia []
- **Sem elementos usuario_equipe_gerente**: Retorna lista vazia []
- **Elementos <usuario> vazios**: Ignora e continua processamento
- **Elementos <usuario> ausentes**: Ignora e continua processamento
- **XML de erro/aviso**: Retorna lista vazia []

Args:
    xml_string (str): 
        String contendo o XML retornado pela função listar_usuarios_equipe_por_gerente.
        Deve estar no formato esperado com elementos <usuario_equipe_gerente> contendo
        subelementos <usuario> com as matrículas. Aceita qualquer XML válido,
        incluindo casos de erro, aviso ou resultado vazio.

Returns:
    list[str]: Lista de matrículas extraídas do XML como strings:
        - **Com usuários encontrados**: Lista contendo todas as matrículas encontradas
        - **Sem usuários encontrados**: Lista vazia []
        - **XML malformado**: Lista vazia []
        - **Elementos vazios/ausentes**: Lista vazia []
        - **Espaços em branco**: Matrículas são automaticamente limpas (strip())
        - **Ordem**: Mantém a ordem dos elementos no XML original
        
        Sempre retorna uma lista válida, nunca None ou exceção.

Raises: 
    Não levanta exceções. Todos os erros de parsing XML ou outros problemas são capturados internamente e resultam no retorno de lista vazia [].

Examples: 
    >>> # Fluxo básico: buscar equipe e extrair matrículas
    >>> xml_equipe = await listar_usuarios_equipe_por_gerente(
    ...     descricao_equipe="Equipe AVA"
    ... )
    >>> matriculas = await extrair_matriculas_do_xml(xml_equipe)
    >>> # Resultado: ["25962", "24290", "12345"]

    >>> # Integração com função de horas trabalhadas
    >>> xml_equipe = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="CURRENT_USER",
    ...     situacao_usuario="Ativo"
    ... )
    >>> matriculas = await extrair_matriculas_do_xml(xml_equipe)
    >>> if matriculas:
    ...     xml_horas = await listar_horas_trabalhadas(
    ...         matricula=matriculas,
    ...         data_inicio="hoje",
    ...         data_fim="hoje"
    ...     )

    >>> # Tratamento de caso sem resultados
    >>> xml_equipe = await listar_usuarios_equipe_por_gerente(
    ...     descricao_equipe="Equipe Inexistente"
    ... )
    >>> matriculas = await extrair_matriculas_do_xml(xml_equipe)
    >>> # Resultado: [] (lista vazia)

    >>> # Fluxo completo para relatório de equipe
    >>> xml_equipe = await listar_usuarios_equipe_por_gerente(
    ...     descricao_equipe="Equipe AVA",
    ...     situacao_usuario="Ativo"
    ... )
    >>> matriculas = await extrair_matriculas_do_xml(xml_equipe)
    >>> if matriculas:
    ...     xml_horas = await listar_horas_trabalhadas(
    ...         matricula=matriculas,
    ...         data_inicio="2024-01-01",
    ...         data_fim="2024-01-31"
    ...     )
    ...     print(f"Processado horas de {len(matriculas)} usuários")
    ... else:
    ...     print("Nenhum usuário encontrado na equipe")

    >>> # Verificação prévia antes de processar
    >>> xml_equipe = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="8372"
    ... )
    >>> matriculas = await extrair_matriculas_do_xml(xml_equipe)
    >>> print(f"Encontrados {len(matriculas)} usuários na equipe")
    >>> for matricula in matriculas:
    ...     print(f"Usuário: {matricula}")

Notes:
    - **FUNÇÃO UTILITÁRIA ASSÍNCRONA**: Projetada especificamente para integração entre funções de equipe e horas
    - **ROBUSTEZ**: Nunca falha - sempre retorna lista válida mesmo com XML inválido
    - **PERFORMANCE**: Parsing rápido usando xml.etree.ElementTree nativo do Python
    - **INTEGRAÇÃO OTIMIZADA**: Funciona perfeitamente com listar_horas_trabalhadas otimizada para listas
    - **CASOS DE ERRO**: XML de erro/aviso retorna lista vazia, permitindo tratamento adequado
    - **LIMPEZA AUTOMÁTICA**: Remove espaços em branco das matrículas automaticamente
    - **XPATH USADO**: './/usuario_equipe_gerente' para buscar todos os elementos independente da profundidade
    - **VALIDAÇÃO**: Verifica se elemento <usuario> existe e contém texto antes de adicionar à lista
    - **FLUXO RECOMENDADO**: 
      1. Chamar listar_usuarios_equipe_por_gerente
      2. Chamar await extrair_matriculas_do_xml com o resultado
      3. Verificar se lista não está vazia
      4. Chamar listar_horas_trabalhadas com a lista de matrículas
    - **REUTILIZAÇÃO**: Pode ser usada com qualquer XML que siga o padrão de usuarios_equipe_gerente
    - **THREAD-SAFE**: Função pura sem estado, segura para uso concorrente
    - **MEMORIA**: Eficiente - processa XML em streaming sem carregar tudo na memória
"""
