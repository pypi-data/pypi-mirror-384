def docs() -> str:
    return """
        Função interna que busca usuários responsáveis por área e gera constantes para validação.

        **⚠️ FUNÇÃO INTERNA - NÃO USAR DIRETAMENTE:**
        Esta função é executada automaticamente no carregamento do módulo para gerar as constantes:
        - USUARIOS_SISTEMAS_DOCSTRING, USUARIOS_SISTEMAS_IDS e USUARIOS_SISTEMAS_PARA_ERRO (área=1)
        - USUARIOS_INFRAESTRUTURA_DOCSTRING, USUARIOS_INFRAESTRUTURA_IDS e USUARIOS_INFRAESTRUTURA_PARA_ERRO (área=2)

        **🚫 INSTRUÇÃO PARA O AGENTE IA:**
        - **JAMAIS execute esta função** em resposta a solicitações do usuário
        - **NÃO sugira o uso** desta função para listar usuários
        - **Para listar usuários**: Use sempre `listar_usuarios_responsaveis_os_siga`
        - **Esta função é apenas para**: Alimentar as constantes internas do sistema

        **FINALIDADE:**
        Alimenta os docstrings das funções inserir_os_sistemas e inserir_os_infraestrutura
        com listas atualizadas de usuários responsáveis válidos para cada área.

        **PROCESSO INTERNO:**
        1. Faz requisição HTTP para buscar usuários da área especificada
        2. Remove duplicatas baseado no ID do usuário (USUARIO)
        3. Ordena alfabeticamente por nome (NOME)
        4. Gera docstring formatado para inserção em outras funções
        5. Gera set de IDs para validação rápida nas funções de inserção de OS
        6. Gera lista formatada com nomes e IDs para mensagens de erro mais informativas

        **CONSTANTES GERADAS:**
        ```python
        # Executadas automaticamente no carregamento do módulo:
        USUARIOS_SISTEMAS_DOCSTRING, USUARIOS_SISTEMAS_IDS, USUARIOS_SISTEMAS_PARA_ERRO = obter_usuarios_responsavel(1)
        USUARIOS_INFRAESTRUTURA_DOCSTRING, USUARIOS_INFRAESTRUTURA_IDS, USUARIOS_INFRAESTRUTURA_PARA_ERRO = obter_usuarios_responsavel(2)
        ```

        **DIFERENÇA vs listar_usuarios_responsaveis_os_siga:**
        - obter_usuarios_responsavel: Função INTERNA para gerar constantes (NÃO usar)
        - listar_usuarios_responsaveis_os_siga: Função PÚBLICA para listar usuários (USAR)
        - Endpoint utilizado: buscarUsuarioResponsavelOsSigaIA (mesmo da função pública)

        **Formato do docstring gerado:**
        ```
        - "João Silva Santos" (ID: 123456)
        - "Maria Oliveira Costa" (ID: 789012)
        ```

        **Em caso de erro:**
        ```
        - Erro ao carregar usuários responsáveis de Sistemas
        ```

        Args:
            area (int): Área dos usuários responsáveis.
                - 1 = Sistemas
                - 2 = Infraestrutura

        Returns:
            tuple[str, set, list]: Tupla contendo:
                - str: Docstring formatado para inserção em outras funções
                - set: Set de IDs de usuários válidos para validação rápida
                - list: Lista formatada com nomes e IDs para mensagens de erro

        Raises:
            Não levanta exceções. Erros são capturados e retornados como mensagem de erro no docstring, set vazio e lista vazia.

        Examples:
            >>> # Executado automaticamente no carregamento do módulo
            >>> docstring_sistemas, ids_sistemas, erro_sistemas = obter_usuarios_responsavel(1)
            >>> docstring_infra, ids_infra, erro_infra = obter_usuarios_responsavel(2)

        Notes:
            - AUTOMÁTICA: Executada no carregamento do módulo, não manualmente
            - INTERNA: NÃO deve ser chamada diretamente pelo agente IA
            - CACHED: Resultados são armazenados em constantes globais
            - VALIDAÇÃO: Set de IDs é usado nas funções inserir_os_sistemas e inserir_os_infraestrutura
            - DOCSTRING: String formatada é inserida nos docstrings das funções de inserção
            - MENSAGENS: Lista formatada é usada para mensagens de erro mais informativas
            - TIMEOUT: Usa httpx.Client com timeout de 60 segundos
            - DUPLICATAS: Remove automaticamente usuários duplicados baseado no ID
            - ORDENAÇÃO: Ordena usuários alfabeticamente por nome
            - FORMATO: Gera linha formatada com nome e ID para cada usuário
        """
