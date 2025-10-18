from siga_mcp.constants import PROJETO_TO_NUMBER
from siga_mcp.dynamic_constants import USUARIOS_SISTEMAS_DOCSTRING
from siga_mcp.utils import montar_string


def docs() -> str:
    return f"""
        Insere uma nova Ordem de Serviço no sistema SIGA para a área de Sistemas.

        **INSTRUÇÃO PARA O AGENTE IA:**
        ANTES de executar esta função de inserção:
        1. MOSTRE ao usuário TODAS as informações que serão criadas/inseridas no sistema
        2. APRESENTE os dados de forma clara e organizada (datas, descrição, tipo, origem, sistema, equipe, projeto, responsável, etc.)
        3. PEÇA confirmação explícita do usuário: "Confirma a criação? (sim/não)"
        4. SÓ EXECUTE esta função se o usuário confirmar explicitamente
        5. Se o usuário não confirmar, cancele a operação e informe que foi cancelada

        Esta função cria uma nova OS (Ordem de Serviço) para **ÁREA SISTEMAS** (área=1),
        incluindo informações como datas, descrição, tipo, origem, sistema, equipe, projeto e responsável.
        Realiza validação de todos os campos obrigatórios e conversão automática de datas.

        **ORIENTAÇÃO PARA SOLICITAÇÕES GENÉRICAS:**
        Quando o usuário solicitar "criar OS" sem especificar área:
        1. **Perguntar qual área**: Sistemas (1) ou Infraestrutura (2)
        2. **Se escolher Sistemas**: Usar esta função
        3. **Se escolher Infraestrutura**: Direcionar para `inserir_os_infraestrutura`

        **Endpoint utilizado:** `inserirOsSigaIA`

        **Estrutura do XML retornado:**
        ```xml
        <ordens_servico dtSolicitacao="15/05/2025 10:09:00" assunto="Desenvolvimento de funcionalidade"
                        descricao="Implementar nova funcionalidade no sistema AVA"
                        matSolicitante="123456" tipo="2" origem="3" equipe="AVA" 
                        responsavel="789" sistema="271" linguagem="6" projeto="67">
            <ordem_servico sistema="SIGA">
                <status>sucesso</status>
                <mensagem>OS cadastrado com sucesso!</mensagem>
            </ordem_servico>
        </ordens_servico>
        ```

        **Em caso de erro de validação:**
        ```xml
        <erro_validacao sistema="SIGA" funcao="inserir_os_sistemas">
            <erro sistema="SIGA">
                <status>erro</status>
                <tipo_erro>tipo_invalido</tipo_erro>
                <tipo_informado>Tipo Inválido</tipo_informado>
                <mensagem>Tipo 'Tipo Inválido' não encontrado na constante TIPO_TO_NUMBER_OS_SISTEMAS</mensagem>
                <tipos_validos>['Suporte Sistema', 'Implementação', 'Manutenção Corretiva', ...]</tipos_validos>
            </erro>
        </erro_validacao>
        ```

        **Em caso de erro de validação (matSolicitante obrigatório):**
        ```xml
        <erro_validacao sistema="SIGA" funcao="inserir_os_sistemas">
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
        <erro_validacao sistema="SIGA" funcao="inserir_os_sistemas">
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
        <ordens_servico dtSolicitacao="15/05/2025 10:09:00" assunto="Desenvolvimento de funcionalidade"
                        matSolicitante="123456" tipo="2" descricao="Descrição"
                        origem="3" equipe="AVA" responsavel="789" projeto="67" sistema="271">
            <ordem_servico sistema="SIGA">
                <status>erro</status>
                <mensagem>Não foi possível salvar a OS. Verifique as informações digitadas.</mensagem>
            </ordem_servico>
        </ordens_servico>
        ```

        **Em caso de outros erros:**
        ```xml
        <ordens_servico dtSolicitacao="15/05/2025 10:09:00" assunto="Desenvolvimento de funcionalidade"
                        matSolicitante="123456" tipo="2" descricao="Descrição"
                        origem="3" equipe="AVA" responsavel="789" projeto="67" sistema="271">
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
            {USUARIOS_SISTEMAS_DOCSTRING}
            responsavel_atual (str | Literal["CURRENT_USER"]): Matrícula do usuário responsável atual pela OS
            {USUARIOS_SISTEMAS_DOCSTRING}
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
                - "Suporte Sistema" (código 1)
                - "Implementação" (código 2) - padrão
                - "Manutenção Corretiva" (código 3)
                - "Treinamento" (código 5)
                - "Suporte Infraestrutura" (código 13)
                - "Mudança de Escopo" (código 20)
                - "Monitoramento" (código 21)
            sistema (Literal): Sistema relacionado a OS, deve ser um dos valores válidos:
                - "Abaris" (código 285)
                - "Administrar Permissões e Acesso - Segurança" (código 45)
                - "Analytics / BI" (código 282)
                - "Analytics / BI (Administrativos/Hospitalares)" (código 305)
                - "APP Pega Plantão" (código 304)
                - "Assinatura Digital / Bird ID" (código 286)
                - "Controle de Contratos" (código 106)
                - "Custo/Orçamento Institucional" (código 226)
                - "GEM - Aplicativo de Apoio" (código 92)
                - "Intranet" (código 302)
                - "MV - Almoxarifado" (código 154)
                - "MV - Ambulatório" (código 155)
                - "MV - Apoio à TI" (código 156)
                - "MV - Auditoria e Glosa" (código 157)
                - "MV - Caixa" (código 158)
                - "MV - CCIH" (código 159)
                - "MV - Central de Marcação" (código 160)
                - "MV - Centro Cirúrgico e Obstétrico" (código 161)
                - "MV - CME" (código 303)
                - "MV - Conciliação de Convênios" (código 163)
                - "MV - Contabilidade" (código 164)
                - "MV - Contas a Pagar" (código 165)
                - "MV - Contas a Receber" (código 166)
                - "MV - Controle Bancário" (código 167)
                - "MV - Custos" (código 217)
                - "MV - Diagnóstico por Imagem" (código 168)
                - "MV - Diretoria Clínica" (código 169)
                - "MV - Faturamento de Convênios e Particulares" (código 170)
                - "MV - Faturamento SUS" (código 171)
                - "MV - Gerenciamento de Projetos" (código 239)
                - "MV - Gestão de Documentos" (código 238)
                - "MV - Gestão de Ocorrências" (código 236)
                - "MV - Gestão de Riscos" (código 237)
                - "MV - Higienização" (código 172)
                - "MV - HMed" (código 264)
                - "MV - Internação" (código 173)
                - "MV - Laboratório de Análises Clínicas" (código 174)
                - "MV - Lavanderia e Rouparia" (código 175)
                - "MV - Manutenção" (código 176)
                - "MV - MovDoc" (código 177)
                - "MV - Nutrição" (código 178)
                - "MV - Patrimônio" (código 179)
                - "MV - PEP" (código 140)
                - "MV - Repasse Médico" (código 219)
                - "MV - SAC" (código 180)
                - "MV - SAME" (código 181)
                - "MV - Sistema de Apoio" (código 129)
                - "MV - Tesouraria" (código 182)
                - "MV - Urgência" (código 223)
                - "Prefeitura Universitária" (código 124)
                - "PROT - Protocolo" (código 108)
                - "RCI - Avaliador (Cópias e Impressões)" (código 4)
                - "RH - Controle de Convênios" (código 121)
                - "RH - Plano de Cargos e Salários" (código 115)
                - "RH - Sistema de Apoio ao Recursos Humanos" (código 107)
                - "RMS - Almoxarifado" (código 1)
                - "RMS - Aprovador" (código 6)
                - "RMS - Avaliador" (código 8)
                - "RMS - Compras" (código 2)
                - "RMS - Gestão de Logística" (código 122)
                - "RMS - Gestão de Serviços" (código 103)
                - "RMS - Gestão de Transporte" (código 113)
                - "RMS - Marketing & Comunicacao" (código 138)
                - "RMS - Patrimônio" (código 232)
                - "RMS - Requisitante" (código 10)
                - "RPA - Recibo de Pagamento Autônomo (Pessoa Física)" (código 274)
                - "Sapiens - Contabilidade" (código 250)
                - "Sapiens - Contas a Pagar" (código 266)
                - "Sapiens - Contas a Receber" (código 269)
                - "Sapiens - Fluxo de Caixa" (código 268)
                - "Sapiens - Recebimento" (código 267)
                - "Sapiens - Sistema de Apoio" (código 259)
                - "Sapiens - Tesouraria" (código 270)
                - "Sapiens - Tributos" (código 249)
                - "Senior - Administração de Pessoal" (código 184)
                - "Senior - Controle de Acesso" (código 185)
                - "Senior - Controle de Ponto" (código 183)
                - "Senior - Jurídico Trabalhista" (código 278)
                - "Senior - Medicina e Segurança do Trabalho" (código 186)
                - "SGA - Acadêmico" (código 131)
                - "SGA - Atividades Administrativas" (código 110)
                - "SGA - Carteirinhas" (código 125)
                - "SGA - Censo" (código 290)
                - "SGA - Contabilidade" (código 119)
                - "SGA - Controle de Ponto" (código 30)
                - "SGA - Controle de Reuniões do Conselho e Câmara" (código 116)
                - "SGA - CPA" (código 287)
                - "SGA - Estágio" (código 24)
                - "SGA - Estágio (Novo)" (código 224)
                - "SGA - Extrator de Dados" (código 227)
                - "SGA - Financeiro" (código 38)
                - "SGA - Formandos" (código 19)
                - "SGA - FORMANDOS (DIPLOMA DIGITAL) - ANTIGO" (código 277)
                - "SGA - FORMANDOS (DIPLOMA DIGITAL) - ATUAL" (código 300)
                - "SGA - Pesquisa" (código 109)
                - "SGA - PIME" (código 120)
                - "SGA - Planejamento EAD" (código 127)
                - "SGA - Pós-Graduação e Extensão" (código 23)
                - "SGA - Pós-Graduação .Net" (código 248)
                - "SGA - Processos Seletivos" (código 118)
                - "SGA - Produção de Materiais Didáticos" (código 49)
                - "SGA - Roteiros" (código 128)
                - "SGA - SISCAP" (código 272)
                - "SGA - Telemarketing" (código 37)
                - "SGA - WEB Administrativo" (código 222)
                - "SGB - Biblioteca" (código 126)
                - "SGS - Clínicas Integradas" (código 104)
                - "SGS - Laboratorio Protese" (código 230)
                - "SGV - Administrativo" (código 51)
                - "SGV - Ambulatório" (código 52)
                - "SGV - Cirúrgico" (código 53)
                - "SGV - Farmácia" (código 54)
                - "SGV - Financeiro" (código 55)
                - "SGV - Financeiro .Net" (código 229)
                - "SGV - Imagem" (código 221)
                - "SGV - Internação" (código 56)
                - "SGV - Laboratório" (código 57)
                - "SGV - LMVP" (código 58)
                - "SGV - Patologia" (código 59)
                - "SGV - Recepção" (código 60)
                - "SIGA - Gestão de Solicitações a DTD / Atividades" (código 143)
                - "Sistemas AVA" (código 271) - padrão
                - "Site Institucional" (código 275)
                - "Site UAGRO - Dottatec" (código 284)
                - "Site Universidade do Agro (Drupal)" (código 301)
                - "SITES SAUDE / HOSPITAIS" (código 295)
                - "Sophia" (código 262)
                - "Uniube Sistemas Integrados - USI" (código 291)
                - "Uniube.br - Acesso restrito" (código 279)
                - "Consist Gem - Contabilidade (INATIVO)" (código 144)
                - "Consist Gem - Contas a Pagar (INATIVO)" (código 146)
                - "ORSE - Aplicativo de Apoio (INATIVO)" (código 93)
                - "SGA - Digitalizações (INATIVO)" (código 43)
                - "SGA - Pesquisa MPHU (INATIVO)" (código 133)
            equipe (Literal): Equipe responsável pela OS:
                - "SGA - Acadêmico" (código ACAD)
                - "RMS (Requisições, Materiais e Serviços)" (código RMS)
                - "SGA - Financeiro" (código FIN)
                - "Recursos Humanos" (código RH)
                - "Financeiro e Contábil" (código FINCONT)
                - "Saúde" (código SAUDE)
                - "SGA - Web" (código SGAWEB)
                - "Administador de Banco de Dados" (código DBA)
                - "Escritório de Projetos" (código PROJ)
                - "Analytics" (código Analytics)
                - "Equipe AVA" (código AVA) - padrão
            linguagem (Literal): Linguagem/tecnologia da OS, deve ser um dos valores válidos:
                - "C#" (código 1)
                - "Fox" (código 2)
                - "SQL" (código 3)
                - "ASP.Net" (código 4)
                - "Access" (código 5)
                - "PHP" (código 6) - padrão
                - "Extrator de Dados" (código 7)
                - "MV Painel de Indicadores" (código 8)
                - "MV Editor" (código 9)
                - "Gerador de Relatórios" (código 10)
                - "Gerador de Cubos" (código 11)
                - "Gerador de Tela" (código 12)
                - "Editor de Regra" (código 13)
                - "Delphi" (código 14)
                - "Script SO" (código 15)
                - "Power BI" (código 18)
                - "Analytics" (código 20)
                - "Node.js" (código 23)
                - "Senior - Gerador de visão dinâmica" (código 24)
            projeto (Literal): Projeto relacionado à OS:
                {montar_string(PROJETO_TO_NUMBER)} "O padrão é: "Operação AVA"
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
                - "E-mail" (código 1)
                - "Pessoalmente" (código 2)
                - "Teams" (código 3) - padrão
                - "Telefone" (código 4)
                - "WhatsApp" (código 5)
                - "Siga" (código 6)
                - "Plantão" (código 7)
                - "SATIC" (código 8)
                - "SAE" (código 11)
        Returns:
            str: XML formatado contendo:
                - Em caso de sucesso: confirmação da inserção com status "sucesso"
                - Em caso de erro de validação: detalhes do erro (tipo inválido, matSolicitante obrigatório, criada_por obrigatório, responsável inválido, etc.)
                - Em caso de erro de API: mensagem de erro específica
                - Em caso de erro interno: mensagem de erro genérica

                O XML sempre inclui os parâmetros enviados como atributos do elemento raiz.

        Raises:
            Não levanta exceções diretamente. Todos os erros são capturados e retornados
            como XML formatado com informações detalhadas do erro.

        Examples:
            >>> # Inserir OS com configurações específicas
            >>> xml = await inserir_os_sistemas(
            ...     data_solicitacao="hoje 09:00",
            ...     assunto="Manutenção banco de dados",
            ...     descricao="Otimização de queries do sistema",
            ...     matSolicitante="654321",
            ...     tipo="Manutenção Corretiva",
            ...     linguagem="SQL",
            ...     sistema="Sistemas AVA",
            ...     projeto="Operação Banco de Dados"
            ... )

            >>> # Exemplo com tipo inválido (retorna erro)
            >>> xml = await inserir_os_sistemas(
            ...     data_solicitacao="2024-01-15 09:00:00",
            ...     assunto="Teste",
            ...     descricao="Teste de OS",
            ...     matSolicitante="123456",
            ...     tipo="Tipo Inexistente"  # Erro!
            ... )

            >>> # Exemplo com matSolicitante inválido (retorna erro)
            >>> xml = await inserir_os_sistemas(
            ...     data_solicitacao="2024-01-15 09:00:00",
            ...     assunto="Teste",
            ...     descricao="Teste de OS",
            ...     matSolicitante="0",  # Erro!
            ...     responsavel="123456",
            ...     responsavel_atual="123456"
            ... )

            >>> # Exemplo com criada_por inválido (retorna erro)
            >>> xml = await inserir_os_sistemas(
            ...     data_solicitacao="2024-01-15 09:00:00",
            ...     assunto="Teste",
            ...     descricao="Teste de OS",
            ...     matSolicitante="123456",
            ...     responsavel="123456",
            ...     responsavel_atual="123456",
            ...     criada_por="abc"  # Erro!
            ... )

        Notes:
            - **DIFERENCIAÇÃO DE FUNÇÃO**: Esta função cria nova OS para área sistemas (área=1). Para editar, use editar_os_sistemas 
            - **VALIDAÇÕES OBRIGATÓRIAS**: Campos matSolicitante e criada_por devem ser "CURRENT_USER" ou números válidos maiores que zero (não aceita valores vazios, "0" ou não-numéricos)
            - A função realiza validação case-insensitive de todos os campos (tipo, origem, sistema, equipe, projeto) 
            - As datas são automaticamente convertidas usando converter_data_siga com manter_horas=True 
            - Utiliza as constantes: TIPO_TO_NUMBER_OS_SISTEMAS, SISTEMA_TO_NUMBER, EQUIPE_TO_NUMBER, LINGUAGEM_TO_NUMBER_OS_SISTEMAS, PROJETO_TO_NUMBER, STATUS_OS_TO_NUMBER, OS_INTERNA_OS_TO_NUMBER, ORIGEM_OS_TO_NUMBER, PRIORIDADE_USUARIO_OS_TO_NUMBER, CRITICIDADE_OS_TO_NUMBER para mapear valores para códigos numéricos 
            - Todos os parâmetros enviados são incluídos como atributos no XML de resposta 
            - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY 
            - Em caso de falha na requisição HTTP, retorna erro interno formatado em XML 
            - O resultado da API (1 = sucesso, outros valores = erro) é interpretado automaticamente 
            - Campos opcionais como nomeSolicitante, centroCusto, etc. são enviados vazios por padrão 
            - Esta função cria OS (Ordens de Serviços) independentes
        """
