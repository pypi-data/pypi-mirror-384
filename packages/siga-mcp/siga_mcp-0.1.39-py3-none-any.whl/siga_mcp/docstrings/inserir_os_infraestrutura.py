from siga_mcp.constants import PROJETO_TO_NUMBER
from siga_mcp.dynamic_constants import USUARIOS_INFRAESTRUTURA_DOCSTRING
from siga_mcp.utils import montar_string


def docs() -> str:
    return f"""
        Insere uma nova Ordem de Serviço no sistema SIGA para a área de Infraestrutura.

        **INSTRUÇÃO PARA O AGENTE IA:**
        ANTES de executar esta função de inserção:
        1. MOSTRE ao usuário TODAS as informações que serão criadas/inseridas no sistema
        2. APRESENTE os dados de forma clara e organizada (datas, descrição, tipo, origem, categoria, equipe, projeto, responsável, etc.)
        3. PEÇA confirmação explícita do usuário: "Confirma a criação? (sim/não)"
        4. SÓ EXECUTE esta função se o usuário confirmar explicitamente
        5. Se o usuário não confirmar, cancele a operação e informe que foi cancelada

        Esta função cria uma nova OS (Ordem de Serviço) para **ÁREA INFRAESTRUTURA** (área=2),
        incluindo informações como datas, descrição, tipo, origem, categoria, equipe, projeto e responsável.
        Realiza validação de todos os campos obrigatórios e conversão automática de datas.

        **ORIENTAÇÃO PARA SOLICITAÇÕES GENÉRICAS:**
        Quando o usuário solicitar "criar OS" sem especificar área:
        1. **Perguntar qual área**: Sistemas (1) ou Infraestrutura (2)
        2. **Se escolher Infraestrutura**: Usar esta função
        3. **Se escolher Sistemas**: Direcionar para `inserir_os_sistemas`

        **Endpoint utilizado:** `inserirOsSigaIA`

        **Estrutura do XML retornado:**
        ```xml
        <ordens_servico dtSolicitacao="15/05/2025 10:09:00" assunto="Suporte técnico estação trabalho"
                        descricao="Resolver problema de conectividade de rede"
                        matSolicitante="123456" tipo="1" origem="1" equipe="HELPDESK" 
                        responsavel="789" categoria="1" projeto="61">
            <ordem_servico sistema="SIGA">
                <status>sucesso</status>
                <mensagem>OS cadastrado com sucesso!</mensagem>
            </ordem_servico>
        </ordens_servico>
        ```

        **Em caso de erro de validação:**
        ```xml
        <erro_validacao sistema="SIGA" funcao="inserir_os_infraestrutura">
            <erro sistema="SIGA">
                <status>erro</status>
                <tipo_erro>tipo_invalido</tipo_erro>
                <tipo_informado>Tipo Inválido</tipo_informado>
                <mensagem>Tipo 'Tipo Inválido' não encontrado na constante TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA</mensagem>
                <tipos_validos>['Suporte', 'Manutenção', 'Instalação', ...]</tipos_validos>
            </erro>
        </erro_validacao>
        ```

        **Em caso de erro de validação (matSolicitante obrigatório):**
        ```xml
        <erro_validacao sistema="SIGA" funcao="inserir_os_infraestrutura">
            <erro sistema="SIGA">
                <status>erro</status>
                <tipo_erro>mat_solicitante_obrigatorio</tipo_erro>
                <campo_invalido>matSolicitante</campo_invalido>
                <valor_informado>0</valor_informado>
                <mensagem>Campo 'matSolicitante' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: 0</mensagem>
            </erro>
        </erro_validacao>
        ```

        **Em caso de erro de validação (criada_por obrigatório):**
        ```xml
        <erro_validacao sistema="SIGA" funcao="inserir_os_infraestrutura">
            <erro sistema="SIGA">
                <status>erro</status>
                <tipo_erro>criada_por_obrigatorio</tipo_erro>
                <campo_invalido>criada_por</campo_invalido>
                <valor_informado>abc</valor_informado>
                <mensagem>Campo 'criada_por' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: abc</mensagem>
            </erro>
        </erro_validacao>
        ```

        **Em caso de erro (dados inválidos):**
        ```xml
        <ordens_servico dtSolicitacao="15/05/2025 10:09:00" assunto="Suporte técnico estação trabalho"
                        matSolicitante="123456" tipo="1" descricao="Descrição"
                        origem="1" equipe="HELPDESK" responsavel="789" projeto="61" categoria="1">
            <ordem_servico sistema="SIGA">
                <status>erro</status>
                <mensagem>Não foi possível salvar a OS. Verifique as informações digitadas.</mensagem>
            </ordem_servico>
        </ordens_servico>
        ```

        **Em caso de outros erros:**
        ```xml
        <ordens_servico dtSolicitacao="15/05/2025 10:09:00" assunto="Suporte técnico estação trabalho"
                        matSolicitante="123456" tipo="1" descricao="Descrição"
                        origem="1" equipe="HELPDESK" responsavel="789" projeto="61" categoria="1">
            <ordem_servico sistema="SIGA">
                <status>erro</status>
                <mensagem>Erro ao gravar a OS. Tente novamente.</mensagem>
            </ordem_servico>
        </ordens_servico>
        ```

        Args:
            data_solicitacao (str): Data e hora da solicitação da OS (Ordem de Serviço).
                Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
            assunto (str): Descrição resumida (título) da OS
            descricao (str): Descrição detalhada da OS a ser realizada
            matSolicitante (str | Literal["CURRENT_USER"]): **[OBRIGATÓRIO]** Matrícula do usuário que está solicitando a OS.
            Deve ser "CURRENT_USER" ou um número válido maior que zero. Não aceita valores vazios, "0" ou não-numéricos.
            responsavel (str | Literal["CURRENT_USER"]): Matrícula do usuário responsável pela OS
            {USUARIOS_INFRAESTRUTURA_DOCSTRING}
            responsavel_atual (str | Literal["CURRENT_USER"]): Matrícula do usuário responsável atual pela OS
            {USUARIOS_INFRAESTRUTURA_DOCSTRING}
            criada_por (str | Literal["CURRENT_USER"]): **[OBRIGATÓRIO]** Matrícula do usuário que criou a OS.
            Deve ser "CURRENT_USER" ou um número válido maior que zero. Não aceita valores vazios, "0" ou não-numéricos.
            prioridade (str | None): Código da Solicitação prioritária da OS
            tempo_previsto (int | None): Cálculo do tempo previsto para a conclusão da OS
            data_inicio_previsto (str | None): Data e hora previsto para iniciar a OS (Ordem de Serviço).
                Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
            data_limite (str | None): Data e hora limite para realização da OS (Ordem de Serviço).
                Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
            sprint (str | None): Descrição dos sprints
            os_predecessora (str | None): Código da OS predecessora da OS em andamento
            chamado_fornecedor (str | None): Código do chamado do fornecedor
            rotinas (str | None): Descrição da rotina
            plaqueta (str | None): Plaqueta relacionado ao equipamento que está sendo atendido.
            os_principal (str | None): Código da OS principal
            classificacao (str | None): Classificação da OS
            nova (str | None): Código para verificar se a OS é nova ou transferência de responsável atual
            data_previsao_entrega (str | None): Data e hora da previsão de entrega da OS (Ordem de Serviço).
                Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
            modulo (str | None): Módulo da OS
            tempo_restante (str | None): Tempo restante para concluir a OS
            ramal (str | None): Número do Ramal
            data_envio_email_conclusao (str | None): Data e hora para o envio do email de conclusão da OS (Ordem de Serviço).
                Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
            tipo_transacao (str | None): código do tipo da transação
            acao (str | None): código da ação
            planejamento (str | None): Descrição do Planejamento da OS
            grupo (str | None): Grupo da OS
            tipo (Literal): Tipo da OS, deve ser um dos valores válidos:
                - "Atividade Interna" (código 19)
                - "Implementação" (código 15)
                - "Incidente" (código 23)
                - "Manutenção Corretiva" (código 17)
                - "Manutenção de Banco" (código 10)
                - "Manutenção Preventiva" (código 16)
                - "Monitoramento" (código 22)
                - "Requisição" (código 24)
                - "Suporte" (código 14) - padrão
                - "Treinamento" (código 18)
            categoria (Literal): Categoria relacionado a OS, deve ser um dos valores válidos:
                - "AD - Alterar Configuração do Domínio" (código 13)
                - "AD - Criar usuário" (código 93)
                - "AD - Desbloquear usuário" (código 68)
                - "AD - Excluir/Bloquear usuário" (código 67)
                - "AD - Liberar permissões de acesso" (código 11)
                - "AD - Redefinir Senha" (código 12)
                - "AD - Suporte/Dúvidas/Outros" (código 39)
                - "BD - Alterar tabela" (código 72)
                - "BD - Atividade Interna" (código 94)
                - "BD - Atualizar esquema" (código 56)
                - "BD - Corrigir lentidão e bloqueios" (código 57)
                - "BD - Criar tabela/índice" (código 71)
                - "BD - Criar usuário" (código 54)
                - "BD - Liberar acessos/permissões" (código 69)
                - "BD - Monitorar rotina de backups e testes de restauração" (código 55)
                - "BD - Reiniciar tabela / Tablespace" (código 53)
                - "BD - Restauração de LOG" (código 70)
                - "BD - Tunning de instrução" (código 58)
                - "DB - Suporte/Dúvidas/Outros" (código 96)
                - "DPO - Analisar contratos" (código 74)
                - "DPO - Analisar/Autorizar autorização de dados e imagens" (código 75)
                - "DPO - Conscientizar sobre segurança digital" (código 76)
                - "DPO - Criar/Implementar política de segurança" (código 77)
                - "E-mail - Alterar Colaborador Responsável" (código 5)
                - "E-mail - Configurar Google Workspace" (código 9)
                - "E-mail - Configurar primeiro acesso" (código 8)
                - "E-mail - Criar e-mail" (código 6)
                - "E-mail - Desbloquear e-mail" (código 78)
                - "E-mail - Excluir/Bloquear e-mail" (código 79)
                - "E-mail - Redefinir senha" (código 7)
                - "E-mail - Suporte/Dúvidas/Outros" (código 40)
                - "Hardware - Atualizar driver(s)/Firmware(s)/Limpeza computador/notebook" (código 35)
                - "Hardware - Atualizar driver(s)/Firmware(s)/Limpeza impressora/scanner" (código 65)
                - "Hardware - Backup" (código 24)
                - "Hardware - Consertar computador/notebook" (código 73)
                - "Hardware - Consertar/Trocar impressora/scanner" (código 80)
                - "Hardware - Formatar" (código 25)
                - "Hardware - Instalar Antivírus" (código 34)
                - "Hardware - Instalar/Desinstalar/Atualizar Software" (código 26)
                - "Hardware - Suporte/Dúvidas/Outros" (código 27) - padrão
                - "Inclusão / Remoção de Colaboradores" (código 62)
                - "Liberar dispositivo de armazenamento" (código 97)
                - "Publicação - AVA" (código 66)
                - "Rede - Alterar perfil de acesso" (código 2)
                - "Rede - Ativar/Crimpar Ponto de Rede" (código 19)
                - "Rede - Configurar Firewall" (código 4)
                - "Rede - Criar/Alterar regra Firewall" (código 3)
                - "Rede - Instalar/Configurar/Atualizar AP/Câmera/Router/Voip" (código 22)
                - "Rede - Instalar/Configurar/Atualizar controle de acesso/catraca" (código 23)
                - "Rede - Instalar/Configurar/Atualizar REP" (código 21)
                - "Rede - Instalar/Configurar/Atualizar Switch/VLAN" (código 20)
                - "Rede - Liberar internet" (código 81)
                - "Rede - Suporte VPN" (código 60)
                - "Rede - Suporte/Dúvidas/Outros" (código 41)
                - "Segurança - Investigar ataques cibernéticos" (código 83)
                - "Segurança - Remover ameaças detectadas" (código 82)
                - "Serviços - Atividade interna" (código 28)
                - "Serviços - Empréstimo de Equipamento" (código 42)
                - "Serviços - Realizar auditoria/Criar relatório" (código 1)
                - "Serviços - Transferir/Recolher equipamento" (código 36)
                - "Serviços - Treinamento" (código 29)
                - "Servidores - Alterar configuração" (código 15)
                - "Servidores - Atualizar driver(s)/Firmware(s)/Limpeza" (código 89)
                - "Servidores - Atualizar/Reiniciar" (código 16)
                - "Servidores - Criar usuário" (código 85)
                - "Servidores - Disparar/Conferir/Restaurar backup" (código 18)
                - "Servidores - Excluir/Bloquear Usuário" (código 84)
                - "Servidores - Liberar/Bloquear permissões" (código 86)
                - "Servidores - Manutenção Corretiva" (código 88)
                - "Servidores - Manutenção Preventiva" (código 87)
                - "Sistemas - Desbloquear usuário" (código 49)
                - "Sistemas - Instalar sistema" (código 50)
                - "Sistemas - Liberar Permissões" (código 91)
                - "Sistemas - Redefinir senha" (código 51)
                - "Sistemas - Retirar Permissões" (código 90)
                - "Sistemas - Suporte/Dúvidas/Outros" (código 52)
                - "Telefonia - Atualizar aparelho" (código 92)
                - "Telefonia - Configurar aparelho" (código 44)
                - "Telefonia - Consertar/Trocar aparelho" (código 45)
                - "Telefonia - Suporte/Dúvidas/Outros" (código 46)
                - "Verificar log de eventos" (código 98)
                - "AD - Atribuir Direitos de Acesso em Pasta/Impressora (INATIVO)" (código 32)
                - "AD - Criar/Renomear/Bloquear/Desbloquear usuário (INATIVO)" (código 10)
                - "Alterar REP (INATIVO)" (código 63)
                - "Catracas - Manutenção Corretiva/Preventiva (INATIVO)" (código 47)
                - "Coletor Biométrico - Manutenção Corretiva/Preventiva (INATIVO)" (código 48)
                - "DPO (INATIVO)" (código 64)
                - "Equipamentos - Instalar/Desinstalar (INATIVO)" (código 30)
                - "Equipamentos - Manutenção Corretiva/Preventiva (INATIVO)" (código 37)
                - "Equipamentos - Suporte/Dúvida/Outros (INATIVO)" (código 31)
                - "Firewall - Suporte/Dúvida/Outros (INATIVO)" (código 61)
                - "Internet - Suporte/Dúvidas/Outros (INATIVO)" (código 43)
                - "Servidores - Criar/Configurar (INATIVO)" (código 17)
                - "Servidores - Criar/Deletar Usuários e/ou Diretórios (INATIVO)" (código 33)
                - "Servidores - Manutenção Preventiva/Corretiva (INATIVO)" (código 14)
                - "Sistemas - Liberar/Retirar Permissão (INATIVO)" (código 59)
            equipe (Literal): Equipe responsável pela OS:
                - "Administador de Banco de Dados" (código DBA)
                - "Gerenciamento de Redes" (código REDES)
                - "Gerenciamento de Redes - Linux" (código LINUX)
                - "Gerenciamento de Redes - Windows" (código WINDOWS)
                - "Help-Desk - Aeroporto" (código Help Aero) - padrão
                - "Help-Desk - Ambulatório" (código Help Amb)
                - "Help-Desk - Araxá" (código Help Ara)
                - "Help-Desk - Centro" (código Help Cen)
                - "Help-Desk - HR" (código Help HR)
                - "Help-Desk - HVU" (código Help HVU)
                - "Help-Desk - IMM" (código Help IMM)
                - "Help-Desk - MPHU" (código Help MPHU)
                - "Help-Desk - NPG" (código Help NPG)
                - "Help-Desk - UPA Mirante" (código Help UPA_M)
                - "Help-Desk - UPA São Benedito" (código Help UPASB)
                - "Help-Desk - Via Centro" (código Help Mar)
                - "Help-Desk - Vila Gávea" (código Help-Desk)
                - "LIAE - Aeroporto" (código LIAE Aero)
                - "LIAE - Via Centro" (código LIAE Mar)
                - "Ouvidoria / Telefonia" (código OUVIDORIA)
                - "Proteção de dados" (código DPO)
                - "Publicação AVA" (código Pub-AVA)
            projeto (Literal): Projeto relacionado à OS:
                {montar_string(PROJETO_TO_NUMBER)} O padrão é: "Operação Help Desk"
            status (Literal): Status da OS, deve ser um dos valores válidos:
                - "Não Planejada" (código 1)
                - "Pendente-Atendimento" (código 2)
                - "Em Atendimento" (código 3) - padrão
                - "Pendente-Teste" (código 4)
                - "Em Teste" (código 5)
                - "Pendente-Liberação" (código 6)
                - "Em Implantação" (código 7)
                - "Concluída" (código 8)
                - "Concluída por Encaminhamento" (código 9)
                - "Concluída por substituição" (código 10)
                - "Pendente-Help-Desk" (código 87)
                - "Pendente-Equipe Manutenção" (código 88)
                - "Pendente-Marketing" (código 89)
                - "Pendente-Sist. Acadêmicos" (código 90)
                - "Pendente-Sist. Administrativos" (código 91)
                - "Pendente-Consultoria" (código 92)
                - "Pendente-Atualização de Versão" (código 93)
                - "Pendente-AVA" (código 94)
                - "Pendente-Equipe Infraestrutura" (código 95)
                - "Pendente-Aprovação" (código 96)
                - "Pendente-Fornecedor" (código 97)
                - "Pendente-Usuário" (código 98)
                - "Cancelamento DTD | Arquivado" (código 99)
                - "Cancelada-Usuário" (código 100)
                - "Solicitação em Aprovação" (código 101)
            os_interna (Literal): Indica se a OS é interna, deve ser um dos valores válidos:
                - "Não" (código 0)
                - "Sim" (código 1) - padrão
            criticidade (Literal): Criticidade da OS, deve ser um dos valores válidos:
                - "Nenhuma" (código 0) - padrão
                - "Baixa" (código 1)
                - "Média" (código 2)
                - "Alta" (código 3)    
            prioridade_usuario (Literal): Prioridade definida pelo usuário, deve ser um dos valores válidos:
                - "Nenhuma" (código 0) - padrão
                - "Urgente" (código 1)
                - "Alta" (código 2)
                - "Média" (código 3)
                - "Baixa" (código 4)
            origem (Literal): Origem da solicitação da OS, deve ser um dos valores válidos:
                - "E-mail" (código 1) - padrão
                - "Pessoalmente" (código 2)
                - "Teams" (código 3)
                - "Telefone" (código 4)
                - "WhatsApp" (código 5)
                - "Siga" (código 6)
                - "Plantão" (código 7)
                - "SATIC" (código 8)
                - "SAE" (código 11)
        Returns:
            str: XML formatado contendo:
                - Em caso de sucesso: confirmação da inserção com status "sucesso"
                - Em caso de erro de validação: detalhes do erro (tipo inválido, matSolicitante obrigatório, criada_por obrigatório, responsável inválido, categoria inválida, etc.)
                - Em caso de erro de API: mensagem de erro específica
                - Em caso de erro interno: mensagem de erro genérica

                O XML sempre inclui os parâmetros enviados como atributos do elemento raiz.

        Raises:
            Não levanta exceções diretamente. Todos os erros são capturados e retornados
            como XML formatado com informações detalhadas do erro.

        Examples:
            >>> # Inserir OS de infraestrutura com configurações específicas
            >>> xml = await inserir_os_infraestrutura(
            ...     data_solicitacao="hoje 09:00",
            ...     assunto="Suporte técnico estação trabalho",
            ...     descricao="Resolver problema de conectividade de rede",
            ...     matSolicitante="654321",
            ...     tipo="Suporte",
            ...     categoria="Hardware - Suporte/Dúvidas/Outros",
            ...     equipe="Help-Desk - Aeroporto",
            ...     projeto="Operação Help Desk"
            ... )

            >>> # Exemplo com tipo inválido (retorna erro)
            >>> xml = await inserir_os_infraestrutura(
            ...     data_solicitacao="2024-01-15 09:00:00",
            ...     assunto="Teste",
            ...     descricao="Teste de OS",
            ...     matSolicitante="123456",
            ...     tipo="Tipo Inexistente"  # Erro!
            ... )

            >>> # Exemplo com matSolicitante inválido (retorna erro)
            >>> xml = await inserir_os_infraestrutura(
            ...     data_solicitacao="2024-01-15 09:00:00",
            ...     assunto="Teste",
            ...     descricao="Teste de OS",
            ...     matSolicitante="0",  # Erro!
            ...     responsavel="123456",
            ...     responsavel_atual="123456"
            ... )

            >>> # Exemplo com criada_por inválido (retorna erro)
            >>> xml = await inserir_os_infraestrutura(
            ...     data_solicitacao="2024-01-15 09:00:00",
            ...     assunto="Teste",
            ...     descricao="Teste de OS",
            ...     matSolicitante="123456",
            ...     responsavel="123456",
            ...     responsavel_atual="123456",
            ...     criada_por="abc"  # Erro!
            ... )

        Notes:
            - **DIFERENCIAÇÃO DE FUNÇÃO**: Esta função cria nova OS para área infraestrutura (área=2). Para editar, use editar_os_infraestrutura 
            - **VALIDAÇÕES OBRIGATÓRIAS**: Campos matSolicitante e criada_por devem ser "CURRENT_USER" ou números válidos maiores que zero (não aceita valores vazios, "0" ou não-numéricos)
            - A função realiza validação case-insensitive de todos os campos (tipo, origem, categoria, equipe, projeto) 
            - As datas são automaticamente convertidas usando converter_data_siga com manter_horas=True 
            - Utiliza as constantes: TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA, CATEGORIA_TO_NUMBER, EQUIPE_INFRAESTRUTURA_TO_NUMBER, PROJETO_TO_NUMBER, STATUS_OS_TO_NUMBER, OS_INTERNA_OS_TO_NUMBER, ORIGEM_OS_TO_NUMBER, PRIORIDADE_USUARIO_OS_TO_NUMBER, CRITICIDADE_OS_TO_NUMBER para mapear valores para códigos numéricos 
            - Todos os parâmetros enviados são incluídos como atributos no XML de resposta 
            - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY 
            - Em caso de falha na requisição HTTP, retorna erro interno formatado em XML 
            - O resultado da API (1 = sucesso, outros valores = erro) é interpretado automaticamente 
            - Campos opcionais como nomeSolicitante, centroCusto, etc. são enviados vazios por padrão 
            - Esta função cria OS (Ordens de Serviços) independentes
        """
