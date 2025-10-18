from textwrap import dedent


def docs() -> str:
    return dedent("""\
            Edita as informações de um atendimento avulso infraestrutura existente no sistema SIGA.

            **INSTRUÇÃO PARA O AGENTE IA:**
            ANTES de executar esta função de edição:
            1. SEMPRE chame primeiro `buscar_informacoes_atendimento_avulso(codigo_atendimento, codigo_analista)`
            2. MOSTRE ao usuário os dados atuais vs. dados que serão alterados em formato claro e comparativo
            3. PEÇA confirmação explícita do usuário: "Confirma as alterações? (sim/não)"
            4. SÓ EXECUTE esta função se o usuário confirmar explicitamente
            5. Se o usuário não confirmar, cancele a operação e informe que foi cancelada
                  
            Esta função atualiza um registro de atendimento avulso independente de qualquer Ordem de Serviço, incluindo informações como datas, descrição, tipo, origem, categoria, equipe, projeto e plaqueta.
            Realiza validação de todos os campos obrigatórios e conversão automática de datas.
                  
            **Funcionalidade de busca automática:**
            Se o atendimento não for encontrado nesta função (atendimentos avulso infraestrutura), a mensagem de erro orientará a buscar nas funções editar_atendimentos_os ou editar_atendimento_avulso_sistemas, permitindo busca automática entre os tipos de atendimento.

            **Endpoint utilizado:** atualizarAtendimentoAvulsoSigaIA

            **Estrutura do XML retornado:**
                  
            **Sucesso:**
            ```xml
            <atendimentos_avulsos_infra codigo_atendimento="123" dataIni="2024-01-15 09:00:00" dataFim="2024-01-15 17:00:00"
                                        matSolicitante="123456" tipo="14" descricao="Descrição"
                                        origem="3" equipe="Help Aero" analista="789" projeto="61" categoria="27" plaqueta="222222">
                <atendimento_avulso_infra sistema="SIGA">
                    <status>sucesso</status>
                    <mensagem>Atendimento avulso editado com sucesso!</mensagem>
                </atendimento_avulso_infra>
            </atendimentos_avulsos_infra>
            ```

            **Em caso de erro de validação (campo inválido):**
            ```xml
            <erro_validacao sistema="SIGA" funcao="editar_atendimento_avulso_infraestrutura">
                <erro sistema="SIGA">
                    <status>erro</status>
                    <tipo_erro>tipo_invalido</tipo_erro>
                    <tipo_informado>Tipo Inválido</tipo_informado>
                    <mensagem>Tipo 'Tipo Inválido' não encontrado na constante TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA</mensagem>
                    <tipos_validos>['Atividade Interna', 'Implementação', 'Incidente', 'Manutenção Corretiva', 'Manutenção de Banco', 'Manutenção Preventiva', 'Monitoramento',	'Requisição', 'Suporte', 'Treinamento']</tipos_validos>
                </erro>
            </erro_validacao>
            ```                  
            
            **Em caso de erro (atendimento não encontrado):**
            ```xml
            <atendimentos_avulsos_infra codigo_atendimento="99999" dataIni="2024-01-15 09:00:00" dataFim="2024-01-15 17:00:00" matSolicitante="123456" tipo="14" descricao="Teste"
                            origem="1" equipe="Help Aero" analista="789" projeto="61" categoria="27" plaqueta="">
                <atendimento_avulso_infra sistema="SIGA">
                    <status>erro</status>
                    <mensagem>Atendimento não encontrado em Avulso Infraestrutura. Tente buscar nas funções editar_atendimentos_os ou editar_atendimento_avulso_sistemas.</mensagem>
                </atendimento_avulso_infra>
            </atendimentos_avulsos_infra>
            ```
                  
            **Em caso de outros erros:**
            ```xml
            <atendimentos_avulsos_infra codigo_atendimento="123" dataIni="2024-01-15 09:00:00"  dataFim="2024-01-15 17:00:00" matSolicitante="123456" tipo="14" descricao="Descrição" origem="1" equipe="Help Aero" analista="789" projeto="61" categoria="27" plaqueta="222222">
                <atendimento_avulso_infra sistema="SIGA">
                    <status>erro</status>
                    <mensagem>Erro ao gravar o atendimento avulso. Tente novamente.</mensagem>
                </atendimento_avulso_infra>
            </atendimentos_avulsos_infra>
            ```

            Args:
                codigo_atendimento (int): Código do atendimento avulso a ser editado.
                data_inicio (str): Data e hora de início do atendimento avulso.
                    Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
                data_fim (str): Data e hora de fim do atendimento avulso.
                    Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
                matricula_solicitante (str | Literal["CURRENT_USER"]): Matrícula do usuário que está solicitando o atendimento avulso
                descricao_atendimento (str): Descrição detalhada do atendimento avulso a ser realizado
                codigo_analista (str | Literal["CURRENT_USER"]): Matrícula do analista/usuário responsável pelo atendimento avulso
                tipo (Literal): Tipo do atendimento avulso, deve ser um dos valores válidos:
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
                origem (Literal): Canal/origem do atendimento avulso, deve ser um dos valores válidos:
                    - "E-mail" (código 1) - padrão
                    - "Pessoalmente" (código 2)
                    - "Teams" (código 3)
                    - "Telefone" (código 4)
                    - "WhatsApp" (código 5)
                    - "Plantão" (código 7)
                    - "SAE" (código 11)
                categoria (Literal): Categoria relacionado ao atendimento avulso, deve ser um dos valores válidos:
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
                equipe (Literal): Equipe responsável pelo atendimento avulso, deve ser uma das equipes válidas:
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
                projeto (Literal): Projeto relacionado ao atendimento avulso, deve ser um dos valores válidos:
                    - "Adequações para ONA 2022" (código 107)
                    - "Adequações para ONA 2024" (código 155)
                    - "Adequações para ONA 2025" (código 198)
                    - "Aditivos ao contrato dos alunos" (código 125)
                    - "Anonimização de prontuário do paciente" (código 143)
                    - "Análise Inicial - Implantação do sistema de imagens na Policlínica" (código 15)
                    - "APP do Paciente" (código 136)
                    - "Autoria" (código 77)
                    - "AVA - CORPORATIVO" (código 129)
                    - "Campus Villa Gávea - Infraestrutura e Segurança" (código 133)
                    - "Cartão Saúde Uniube" (código 181)
                    - "Cartão Vital" (código 189)
                    - "Consultoria externa Contábil/Financeiro" (código 170)
                    - "Consultoria externa HCM" (código 171)
                    - "Controle de limpeza de leitos hospitalares" (código 145)
                    - "Controle de registros dos médicos" (código 137)
                    - "Criar script de mapeamento das impressoras" (código 54)
                    - "Desenvolvimento Componentes / Framework" (código 188)
                    - "Desenvolvimento Web / Mobile" (código 186)
                    - "Estudo de plataformas de CRM e Vendas" (código 156)
                    - "Gestão de Sucesso dos Polos" (código 118)
                    - "Graduação - ajustes na transferência, 2ª graduação - 2025" (código 197)
                    - "Implantação do módulo jurídico" (código 99)
                    - "Implantação do sistema No Harm - Farmácia" (código 142)
                    - "Implantação Integração MVPEP e ATRIUM" (código 146)
                    - "Implantação UPAs" (código 131)
                    - "Integração da modalidade ECG com o PACs" (código 153)
                    - "Integração entre Sistema Epimed Monitor UTI e o MVPEP" (código 174)
                    - "Integração SAE e Protocolos" (código 75)
                    - "ITVix - SIG Polos Integração" (código 130)
                    - "Mapeamento AS IS Logística e Central de Malotes" (código 122)
                    - "Melhorias e automação de atendimento - MPHU e TakeBlip" (código 120)
                    - "Melhorias na Transferência externa e aproveitamento de estudos" (código 116)
                    - "Melhorias no módulo de treinamento" (código 196)
                    - "Melhorias no Sistema de Geração de Provas e Fechamento de Disciplinas do EAD" (código 103)
                    - "Melhorias para SADT - MPHU" (código 124)
                    - "Migração .Net (Entity + Crystal)" (código 101)
                    - "Migração de sistemas Fox Pro" (código 138)
                    - "Migração para o PHP 8" (código 100)
                    - "Novo CNES das Clínicas Integradas" (código 140)
                    - "Novo formato alfanumérico para o Cadastro Nacional da Pessoa Jurídica (CNPJ)" (código 205)
                    - "Operacao Publicacao AVA" (código 119)
                    - "Operaçao DPO" (código 114)
                    - "Operação Acadêmico" (código 28)
                    - "Operação Analytics" (código 151)
                    - "Operação AVA" (código 67)
                    - "Operação Banco de Dados" (código 207)
                    - "Operação Biblioteca" (código 30)
                    - "Operação Clínicas" (código 2)
                    - "Operação Compras" (código 3)
                    - "Operação Financeiro/Contabilidade" (código 4)
                    - "Operação Gestão de Relacionamento" (código 72)
                    - "Operação Help Desk" (código 61) - padrão
                    - "Operação HMed" (código 64)
                    - "Operação HVU" (código 5)
                    - "Operação Infraestrutura" (código 62)
                    - "Operação Jurídico Trabalhista" (código 201)
                    - "Operação LIAE" (código 63)
                    - "Operação Medicina do Trabalho" (código 199)
                    - "Operação MV" (código 6)
                    - "Operação RH" (código 7)
                    - "Operação RMS" (código 8)
                    - "Operação Saúde - Web" (código 187)
                    - "Operação Segurança do Trabalho" (código 200)
                    - "Operação SGA - Financeiro/Contabilidade" (código 29)
                    - "Operação Site Institucional" (código 98)
                    - "Operação TI" (código 19)
                    - "Operação WEB Administrativo" (código 27)
                    - "Overmind.ia - Automação entre MV e Convênios" (código 203)
                    - "Painéis interativos de sistemas de saúde" (código 135)
                    - "Projeto - Fluxo de locação de espaços físicos" (código 123)
                    - "Projeto APP Marcação de Ponto para Professores" (código 139)
                    - "Projeto App Pega Plantão" (código 202)
                    - "Projeto AVA 3.0" (código 73)
                    - "Projeto Banco de Questões" (código 84)
                    - "Projeto BI" (código 89)
                    - "Projeto Carrinhos Beira Leito" (código 173)
                    - "Projeto Contratos Empresariais - PROED" (código 20)
                    - "Projeto Controle de Acessos dos Hospitais" (código 157)
                    - "Projeto Cópia de perfil" (código 108)
                    - "Projeto de adequação Rede WIFI" (código 132)
                    - "Projeto de Automatização de Convênios do MPHU" (código 127)
                    - "Projeto de Controle de Vacinas no HVU" (código 147)
                    - "Projeto de desenvolvimento IA para Plano Terapeutico" (código 204)
                    - "Projeto de integração Comtele" (código 93)
                    - "Projeto de integração Intersaberes" (código 92)
                    - "Projeto de Melhoria de Agendamento de Serviços de Transportes" (código 193)
                    - "Projeto de melhorias nas Clínicas Integradas" (código 109)
                    - "Projeto de Melhorias no Controle de Contratos" (código 74)
                    - "Projeto de melhorias no faturamento MPHU" (código 106)
                    - "Projeto de melhorias no HVU" (código 105)
                    - "Projeto de Melhorias nos Setores Jurídicos" (código 126)
                    - "Projeto de melhorias SEU Financeiro" (código 112)
                    - "Projeto de Solicitação de Contratação" (código 110)
                    - "Projeto Digitalização Secretaria do Conselho Universitário" (código 160)
                    - "Projeto Diploma Digital" (código 97)
                    - "Projeto Documentação de Telas e Sistemas" (código 154)
                    - "Projeto DRG Brasil - Hospitais" (código 144)
                    - "Projeto Evolução do Sistema RMS-Almoxarifado" (código 195)
                    - "Projeto Fluxo de Situação Acadêmica EAD" (código 38)
                    - "Projeto Gestão da Permanência Qualificada" (código 36)
                    - "Projeto GIT" (código 83)
                    - "Projeto GPQ" (código 70)
                    - "Projeto Ilhas de Impressão" (código 128)
                    - "Projeto IMM - Implantação Multiempresa" (código 178)
                    - "Projeto Implantação Clínicas MV" (código 190)
                    - "Projeto Implantação Ábaris - secretaria digital e diplomas" (código 115)
                    - "Projeto Implantação Ábaris - XML histórico parcial e oficial" (código 164)
                    - "Projeto Inscrição e Matrícula dos Cursos de Graduação" (código 102)
                    - "Projeto LGPD" (código 88)
                    - "Projeto Limpeza dos Sistemas AVA" (código 79)
                    - "Projeto MELHORIA SISTEMA de APOIO RH" (código 113)
                    - "Projeto Melhorias no controle de acesso - Hospitais - Campus Centro - Estacionamentos" (código 177)
                    - "Projeto Migração para .Net SGA - Financeiro" (código 31)
                    - "Projeto Migração para o Sistemas Integrados WEB" (código 35)
                    - "Projeto Número de Alunos - Graduação" (código 149)
                    - "Projeto Número de Alunos - Pós-Graduação" (código 150)
                    - "Projeto Operação Formandos" (código 152)
                    - "Projeto Reestruturação do Repasse a Parceiros - PROED" (código 21)
                    - "Projeto Revisão Orçamento Institucional" (código 168)
                    - "Projeto RH - Análise de Danos Causados pelo Empregado" (código 185)
                    - "Projeto RH - Avaliação de Desenvolvimento" (código 172)
                    - "Projeto RH - Coleta de assinatura digital dos ASOs" (código 191)
                    - "Projeto RH - Plano de Cargos e Salários" (código 158)
                    - "Projeto SEAD CONSAE - Etapa 1" (código 16)
                    - "Projeto SEAD CONSAE - Etapa 2" (código 34)
                    - "Projeto Secretaria Digital" (código 86)
                    - "Projeto Sistema de Avaliação da EAD" (código 78)
                    - "Projeto Sistemas de Saúde - WEB" (código 175)
                    - "Projeto SMS" (código 85)
                    - "Projeto Unificação do PIAC" (código 81)
                    - "Projeto Unificação do PROEST" (código 80)
                    - "Projeto UniFlex" (código 39)
                    - "Projeto Universidade do Agro" (código 111)
                    - "Projeto Ábaris - Currículo dos cursos em XML" (código 165)
                    - "Projeto: Migração do sistema de Compras/Bionexo" (código 192)
                    - "Projetos ASSCOM" (código 90)
                    - "Projetos de BIs do sistema RMS" (código 141)
                    - "Projetos Estágio" (código 94)
                    - "Projetos PMO" (código 96)
                    - "Projetos PROPEPE" (código 91)
                    - "Projetos Setor Financeiro" (código 148)
                    - "Publicações AVA" (código 117)
                    - "Pós EAD 2.0" (código 87)
                    - "Reformulação do SITE MPHU" (código 180)
                    - "RMGV" (código 76)
                    - "Sistemas Parceiros" (código 82)
                    - "Site Hospitalares" (código 179)
                    - "Situações acadêmicas da Pós-Graduação" (código 182)
                    - "Transformação Digital" (código 104)
                    - "Transformação digital - Aproveitamento/transferencia/segunda graduação" (código 161)
                    - "Transformação Digital - Reabertura de atividades do AVA" (código 163)
                    - "Transformação Digital - Reemissão de boletos (Refit 2024)" (código 162)
                    - "Universidade do Agro - Novo site" (código 183)
                    - "Universidade MV" (código 159)
                    - "Upgrade SO Windows Server 2012 - fim do suporte" (código 134)
                    - "Vertifical da Saúde Uniube (projeto)" (código 206)
                plaqueta (str | None): Plaqueta relacionado ao equipamento que está sendo atendido.

            Returns:
                str: XML formatado contendo:
                    - Em caso de sucesso: confirmação da edição com status "sucesso" 
                    - Em caso de atendimento não encontrado: status "erro" com orientação para buscar em outras funções 
                    - Em caso de outros erros de validação: detalhes do erro com valores válidos para o campo inválido 
                    - Em caso de outros erros de API: status "erro" com mensagem explicativa 
                    - Em caso de erro interno: mensagem de erro genérica
                  
                O XML sempre inclui os parâmetros enviados como atributos do elemento raiz.

            Raises:
                Não levanta exceções diretamente. Todos os erros são capturados e retornados como XML formatado com informações detalhadas do erro.

            Examples:
                >>> # Editar atendimento avulso básico
                >>> xml = await editar_atendimento_avulso_infraestrutura(
                ...     codigo_atendimento=123,
                ...     data_inicio="2024-01-15 09:00:00",
                ...     data_fim="2024-01-15 17:00:00",
                ...     matricula_solicitante="123456",
                ...     descricao_atendimento="Suporte ao sistema AVA",
                ...     codigo_analista=789
                ... )
                  
                >>> # Editar atendimento com projeto específico
                >>> xml = await editar_atendimento_avulso_infraestrutura(
                ...     codigo_atendimento=456,
                ...     data_inicio="hoje 09:00",
                ...     data_fim="hoje 17:00",
                ...     matricula_solicitante="654321",
                ...     descricao_atendimento="Manutenção preventiva do banco de dados",
                ...     codigo_analista=456,
                ...     tipo="Manutenção de Banco",
                ...     origem="E-mail",
                ...     categoria="Suporte/Dúvidas/Outros",
                ...     equipe="Help-Desk - Aeroporto",
                ...     projeto="Operação Help Desk",
                ...     plaqueta="222222"
                ... )
                  
                >>> # Exemplo quando não encontra (orienta busca automática)
                >>> xml = await editar_atendimento_avulso_infraestrutura(
                ...     codigo_atendimento=99999,
                ...     data_inicio="2024-01-15 09:00:00",
                ...     data_fim="2024-01-15 17:00:00",
                ...     matricula_solicitante="123456",
                ...     descricao_atendimento="Teste",
                ...     codigo_analista=789
                ... )
                  
                >>> # Exemplo com tipo inválido (retorna erro)
                >>> xml = await editar_atendimento_avulso_infraestrutura(
                ...     codigo_atendimento=789,
                ...     data_inicio="2024-01-15 09:00:00",
                ...     data_fim="2024-01-15 17:00:00",
                ...     matricula_solicitante="123456",
                ...     descricao_atendimento="Teste",
                ...     codigo_analista=789,
                ...     tipo="Tipo Inexistente" # Erro!
                ... )

            Notes:
                - **ATENÇÃO**: Esta operação modifica permanentemente os dados do atendimento
                - **DIFERENCIAÇÃO DE TIPOS**: Esta função é específica para atendimentos avulso infraestrutura. Para outros tipos, use as funções específicas
                - Para busca automática: Se não encontrar nesta função, use editar_atendimentos_os ou editar_atendimento_avulso_sistemas com os mesmos parâmetros
                - A função realiza validação case-insensitive de todos os campos (tipo, origem, categoria, equipe, projeto)
                - As datas são automaticamente convertidas usando converter_data_siga com manter_horas=True
                - Utiliza as constantes: TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA, ORIGEM_TO_NUMBER, CATEGORIA_TO_NUMBER, EQUIPE_INFRAESTRUTURA_TO_NUMBER, PROJETO_TO_NUMBER para mapear valores para códigos numéricos
                - Todos os parâmetros enviados são incluídos como atributos no XML de resposta
                - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
                - Em caso de falha na requisição HTTP, retorna erro interno formatado em XML
                - O resultado da API (1 = sucesso, outros valores = erro) é interpretado automaticamente
                - Campos opcionais como nomeSolicitante, centroCusto, etc. são enviados vazios por padrão
                - Esta função edita atendimentos avulsos independentes, não vinculados a nenhuma OS
            """)
