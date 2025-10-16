def docs() -> str:
    return """
        Lista todos os usuários responsáveis por Ordens de Serviço SIGA de acordo com a área especificada.
        Serve para obter listas tanto para RESPONSAVEL quanto para RESPONSAVEL_ATUAL.

        **INSTRUÇÃO PARA O AGENTE IA:**
        Para solicitações sobre usuários responsáveis:
        1. **SEMPRE pergunte a área** se não for especificada: "Qual área? (1) Sistemas ou (2) Infraestrutura?"
        2. **Execute com area=1** para área de Sistemas
        3. **Execute com area=2** para área de Infraestrutura
        4. **Use esta função** quando o usuário solicitar:
        - "lista de usuários responsáveis"
        - "quem pode ser responsável"
        - "quem pode ser responsável atual"
        - "responsáveis disponíveis"
        - "analistas da área X"

        **⚠️ REGRA CRÍTICA - NUNCA INVENTAR USUÁRIOS:**
        - **JAMAIS crie, invente ou sugira usuários** que não estejam na lista retornada por esta função
        - **SE a busca retornar vazia**, informe que não há usuários disponíveis para a área
        - **APENAS use usuários** que apareçam explicitamente no XML de retorno
        - **NÃO sugira matrículas** ou nomes que não estejam na resposta real da API
        - **SE não houver usuários**, oriente o usuário a verificar com o administrador do sistema

        **CASOS DE USO:**
        - **RESPONSAVEL**: Lista usuários que podem ser definidos como responsáveis por uma OS
        - **RESPONSAVEL_ATUAL**: Lista usuários que podem ser definidos como responsáveis atuais por uma OS
        - **Ambos usam a mesma lista** de usuários habilitados por área

        **EXEMPLOS DE SOLICITAÇÕES:**
        - "Liste os usuários responsáveis da área de Sistemas"
        - "Quem pode ser responsável por uma OS de Infraestrutura?"
        - "Mostre os analistas disponíveis para Sistemas"
        - "Lista de responsáveis atuais da Infraestrutura"
        - "Usuários que podem assumir uma OS"

        Esta função busca todos os usuários habilitados a serem responsáveis ou responsáveis atuais
        por Ordens de Serviço em uma área específica. É utilizada pelas funções inserir_os_sistemas
        e inserir_os_infraestrutura para validação de usuários.

        **Endpoint utilizado:** `buscarUsuarioResponsavelOsSigaIA`

        **Estrutura do XML retornado:**
        ```xml
        <usuarios_responsaveis area="1" tipo="Sistemas" sistema="SIGA">
            <usuario_responsavel sistema="SIGA">
                <USUARIO>123456</USUARIO>
                <NOME>João Silva Santos</NOME>
            </usuario_responsavel>
            <usuario_responsavel sistema="SIGA">
                <USUARIO>789012</USUARIO>
                <NOME>Maria Oliveira Costa</NOME>
            </usuario_responsavel>
        </usuarios_responsaveis>
        
        Em caso de lista vazia:

        <usuarios_responsaveis area="1" tipo="Sistemas" sistema="SIGA">
        </usuarios_responsaveis>
        
        Em caso de erro:

        Erro ao listar usuários responsáveis área 1.
        Args: area (int): Área dos usuários responsáveis a serem listados. - 1 = Sistemas - 2 = Infraestrutura Este parâmetro é obrigatório.

        Returns: str: XML formatado contendo: - Lista de usuários responsáveis da área especificada (pode estar vazia) - Cada usuário inclui apenas: USUARIO (matrícula) e NOME - Atributos do elemento raiz incluem área e tipo (Sistemas/Infraestrutura) - Em caso de erro na requisição: mensagem de erro simples

        Examples: >>> # Para área de Sistemas >>> xml = await listar_usuarios_responsaveis_os_siga(area=1)

        >>> # Para área de Infraestrutura
        >>> xml = await listar_usuarios_responsaveis_os_siga(area=2)
        Notes: 
            - DUPLA FINALIDADE: Serve para RESPONSAVEL e RESPONSAVEL_ATUAL 
            - INTEGRAÇÃO: Usada por inserir_os_sistemas e inserir_os_infraestrutura 
            - DADOS SIMPLES: Retorna apenas matrícula (USUARIO) e nome (NOME) 
            - VALIDAÇÃO: Os usuários retornados são os mesmos das constantes de validação 
            - SEGURANÇA: NUNCA invente usuários que não estejam na resposta da API 
            - COMPLEMENTAR: Existe também a função obter_usuarios_responsavel para casos específicos 
        
        """
