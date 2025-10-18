def docs() -> str:
    return """
Lista usuários de uma equipe filtrados por gerente responsável, descrição da equipe e situação do usuário.

**INSTRUÇÃO PARA O AGENTE IA:**
- **NÃO INVENTAR USUÁRIOS**: Quando esta função retornar resultado vazio (nenhum usuário encontrado), NUNCA invente, crie ou sugira usuários que não existem
- **APENAS INFORMAR**: Se não encontrar usuários, apenas informe o resultado real da busca (nenhum usuário encontrado)
- **NÃO SUGERIR CRIAÇÃO**: Esta função é para LISTAGEM apenas, não sugira criar usuários ou usar outras funções para inserir usuários

Esta função permite que gerentes pesquisem funcionários da sua equipe ou de equipes específicas,
utilizando validação robusta através de constantes predefinidas. É útil para gestão de equipes
e integra-se com a função listar_horas_trabalhadas através da função utilitária extrair_matriculas_do_xml
para buscar horas trabalhadas dos funcionários da equipe.
A função valida equipes através da constante EQUIPE_GERAL_TO_NUMBER e situações através da 
constante SITUACAO_USUARIO_TO_NUMBER, garantindo consistência e type safety.

**Endpoint utilizado:** `listarUsuariosEquipePorGerente`

**Estrutura do XML retornado (com resultados):**
```xml
<usuarios_equipe_gerente matriculaGerente="8372" equipe="AVA" 
                         situacaoUsuario="1" sistema="SIGA">
    <usuario_equipe_gerente sistema="SIGA">
        <usuario>25962</usuario>
        <nome>ARTHUR BRENNO RIBEIRO COELHO</nome>
        <equipe>AVA</equipe>
        <descr_equipe>Equipe AVA</descr_equipe>
        <cargo>12608</cargo>
        <descr_cargo>PROGRAMADOR PL</descr_cargo>
        <gerente>8372</gerente>
        <nome_gerente>ROBERTO SILVA ARAUJO ASSIS</nome_gerente>
    </usuario_equipe_gerente>
    <usuario_equipe_gerente sistema="SIGA">
        <usuario>24290</usuario>
        <nome>ARTHUR TOSTA MATIAS</nome>
        <equipe>AVA</equipe>
        <descr_equipe>Equipe AVA</descr_equipe>
        <cargo>12416</cargo>
        <descr_cargo>ANALISTA DE SISTEMAS JR</descr_cargo>
        <gerente>8372</gerente>
        <nome_gerente>ROBERTO SILVA ARAUJO ASSIS</nome_gerente>
    </usuario_equipe_gerente>
    <!-- Mais usuários... -->
</usuarios_equipe_gerente>

**Em caso de nenhum resultado encontrado:**
<usuarios_equipe_gerente matriculaGerente="999" equipe="" 
                         situacaoUsuario="" sistema="SIGA">
    <resultado sistema="SIGA">
        <status>aviso</status>
        <mensagem>Nenhum usuário encontrado para os filtros informados. Verifique se você é gerente de uma equipe ou ajuste os filtros de busca.</mensagem>
    </resultado>
</usuarios_equipe_gerente>

**Em caso de erro de validação (equipe inválida):**
<erro_validacao sistema="SIGA" funcao="listar_usuarios_equipe_por_gerente">
    <erro sistema="SIGA">
        <status>erro</status>
        <tipo_erro>equipe_invalida</tipo_erro>
        <equipe_informada>Equipe Inexistente</equipe_informada>
        <mensagem>Equipe 'Equipe Inexistente' não encontrada na constante EQUIPE_GERAL_TO_NUMBER</mensagem>
        <equipes_validas>["SGA - Acadêmico", "RMS (Requisições, Materiais e Serviços)", "SGA - Financeiro", ...]</equipes_validas>
    </erro>
</erro_validacao>

**Em caso de erro de validação (situação inválida):**
<erro_validacao sistema="SIGA" funcao="listar_usuarios_equipe_por_gerente">
    <erro sistema="SIGA">
        <status>erro</status>
        <tipo_erro>situacao_invalida</tipo_erro>
        <situacao_informada>Status Inexistente</situacao_informada>
        <mensagem>Situação 'Status Inexistente' não encontrada na constante SITUACAO_USUARIO_TO_NUMBER</mensagem>
        <situacoes_validas>["Bloqueado", "Ativo", "Bloqueado (Afastamento)", ...]</situacoes_validas>
    </erro>
</erro_validacao>

**Em caso de erro interno:**
<resultado sistema="SIGA">
    <item sistema="SIGA">
        <status>erro</status>
        <mensagem>Erro interno: [detalhes do erro]. Tente novamente mais tarde.</mensagem>
    </item>
</resultado>

Args:
    matricula_gerente (str | int | Literal["CURRENT_USER"] | None, optional): Matrícula do gerente responsável pelas equipes. Se "CURRENT_USER", busca equipes do usuário atual. Se None ou não fornecido, busca usuários de todas as equipes. Defaults to None.

    descricao_equipe (EquipeGeralType | None, optional): Nome da equipe específica para filtrar usuários. Deve ser um dos valores válidos:
        - "SGA - Acadêmico" (código "ACAD")
        - "RMS (Requisições, Materiais e Serviços)" (código "RMS")
        - "SGA - Financeiro" (código "FIN")
        - "Recursos Humanos" (código "RH")
        - "Financeiro e Contábil" (código "FINCONT")
        - "Saúde" (código "SAUDE")
        - "SGA - Web" (código "SGAWEB")
        - "Administador de Banco de Dados" (código "DBA")
        - "Escritório de Projetos" (código "PROJ")
        - "Analytics" (código "Analytics")
        - "Equipe AVA" (código "AVA")
        - "Gerenciamento de Redes" (código "REDES")
        - "Gerenciamento de Redes - Linux" (código "LINUX")
        - "Gerenciamento de Redes - Windows" (código "WINDOWS")
        - "Help-Desk - Aeroporto" (código "Help Aero")
        - "Help-Desk - Ambulatório" (código "Help Amb")
        - "Help-Desk - Araxá" (código "Help Ara")
        - "Help-Desk - Centro" (código "Help Cen")
        - "Help-Desk - HR" (código "Help HR")
        - "Help-Desk - HVU" (código "Help HVU")
        - "Help-Desk - IMM" (código "Help IMM")
        - "Help-Desk - MPHU" (código "Help MPHU")
        - "Help-Desk - NPG" (código "Help NPG")
        - "Help-Desk - UPA Mirante" (código "Help UPA_M")
        - "Help-Desk - UPA São Benedito" (código "Help UPASB")
        - "Help-Desk - Via Centro" (código "Help Mar")
        - "Help-Desk - Vila Gávea" (código "Help Vila")
        - "LIAE - Aeroporto" (código "LIAE Aero")
        - "LIAE - Via Centro" (código "LIAE Mar")
        - "Ouvidoria / Telefonia" (código "OUVIDORIA")
        - "Proteção de dados" (código "DPO")
        - "Publicação AVA" (código "Pub-AVA")
        Se None, busca usuários de todas as equipes. Defaults to None.

    situacao_usuario (SituacaoUsuarioType | None, optional): Situação do usuário para filtro. Deve ser um dos valores válidos:
        - "Bloqueado" (código 0)
        - "Ativo" (código 1)
        - "Bloqueado (Afastamento)" (código 2)
        - "Bloqueado pelo RH (Individual)" (código 3)
        - "Bloqueado por Falta de Justificativa de Ponto (Individual)" (código 4)
        - "Bloqueado Licença sem Remuneração" (código 5)
        Se None, busca usuários independente da situação (padrão). Defaults to None.


Returns:
    str: XML formatado contendo:
        - **Com resultados**: Lista de usuários encontrados, cada um com matrícula (usuario), nome, código da equipe, descrição da equipe, código do cargo, descrição do cargo, matrícula do gerente e nome do gerente
        - **Sem resultados**: XML com status "aviso" e mensagem explicativa sobre possíveis causas (usuário não é gerente, equipe não existe, filtros muito restritivos)
        - **Erro de validação**: XML com status "erro", tipo do erro, valor informado e lista de valores válidos para equipes ou situações
        - **Erro interno**: XML com status "erro" e detalhes da exceção ocorrida
        - Atributos do elemento raiz sempre incluem os parâmetros de filtro utilizados (valores normalizados)
        - Ordenação dos resultados: por gerente → equipe → nome do usuário
        
        Todos os XMLs incluem o atributo "sistema" com valor "SIGA".

Raises: 
    Não levanta exceções diretamente. Todos os erros são capturados e retornados como XML formatado com status "erro" e detalhes da exceção ou validação.

Examples:
    >>> # Liste todos os funcionários da minha equipe
    >>> xml = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="CURRENT_USER"
    ... )

    >>> # Liste todos os funcionários da minha equipe que estão ativos
    >>> xml = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="CURRENT_USER",
    ...     situacao_usuario="Ativo"
    ... )

    >>> # Liste todos os funcionários da Equipe AVA
    >>> xml = await listar_usuarios_equipe_por_gerente(
    ...     descricao_equipe="Equipe AVA"
    ... )

    >>> # Liste todos os funcionários da Equipe AVA que estão ativos
    >>> xml = await listar_usuarios_equipe_por_gerente(
    ...     descricao_equipe="Equipe AVA",
    ...     situacao_usuario="Ativo"
    ... )

    >>> # Liste todos os funcionários da minha equipe que são da Equipe AVA e que estão ativos
    >>> xml = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="CURRENT_USER",
    ...     descricao_equipe="Equipe AVA",
    ...     situacao_usuario="Ativo"
    ... )

    >>> # Liste todos os funcionários de um gerente específico
    >>> xml = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="8372"
    ... )

    >>> # Liste todos os funcionários de um gerente específico que estão bloqueados
    >>> xml = await listar_usuarios_equipe_por_gerente(
    ...     matricula_gerente="8372",
    ...     situacao_usuario="Bloqueado"
    ... )

    >>> # Buscar sem filtros (todos os usuários de todas as equipes)
    >>> xml = await listar_usuarios_equipe_por_gerente()

Notes:
    - **GESTÃO DE EQUIPES**: Permite que gerentes visualizem sua equipe e pesquisem outras equipes
    - **INTEGRAÇÃO DISPONÍVEL**: Use extrair_matriculas_do_xml + listar_horas_trabalhadas para relatórios completos de equipe
    - **FLUXO DE INTEGRAÇÃO**: listar_usuarios_equipe_por_gerente → extrair_matriculas_do_xml → listar_horas_trabalhadas
    - **NÃO INVENTAR USUÁRIOS**: Quando não encontrar usuários, NUNCA inventar ou sugerir criação de usuários inexistentes
    - A função realiza validação case-insensitive de todos os campos (equipe e situação)
    - Utiliza as constantes: EQUIPE_GERAL_TO_NUMBER, SITUACAO_USUARIO_TO_NUMBER para mapear valores para códigos
    - Todos os parâmetros são opcionais, permitindo buscas flexíveis
    - Parâmetros None ou vazios são enviados como strings vazias para a API
    - Em caso de nenhum resultado, retorna XML com status "aviso" em vez de erro
    - Erro de validação retorna lista completa de valores válidos quando informado valor inválido
    - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
    - A resposta da API é processada através do XMLBuilder para formatação consistente
    - Os atributos do XML de resposta refletem os valores normalizados (códigos) enviados para a API
    - Resultado ordenado por: gerente → equipe → nome do usuário
    - Estrutura de resposta consistente com outras funções do sistema
"""
