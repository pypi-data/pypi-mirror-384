def docs() -> str:
    return """
Insere um novo atendimento avulso no sistema SIGA.

**INSTRUÇÃO PARA O AGENTE IA:**
ANTES de executar esta função de inserção:
1. MOSTRE ao usuário TODAS as informações que serão criadas/inseridas no sistema
2. APRESENTE os dados de forma clara e organizada (datas, descrição, tipo, origem, sistema, equipe, projeto, analista, etc.)
3. PEÇA confirmação explícita do usuário: "Confirma a criação? (sim/não)"
4. SÓ EXECUTE esta função se o usuário confirmar explicitamente
5. Se o usuário não confirmar, cancele a operação e informe que foi cancelada

Esta função cria um novo registro de atendimento avulso independente de qualquer Ordem de Serviço,
incluindo informações como datas, descrição, tipo, origem, sistema, equipe e projeto.
Realiza validação de todos os campos obrigatórios e conversão automática de datas.

**ORIENTAÇÃO PARA SOLICITAÇÕES GENÉRICAS:**
Quando o usuário solicitar "inserir/criar um atendimento" sem especificar o tipo:
1. **Perguntar qual tipo**: Atendimento OS, Atendimento Avulso Sistemas, ou Atendimento Avulso Infraestrutura
2. **Se escolher "Avulso"**: Perguntar se é de Sistemas ou Infraestrutura
3. **Depois de definir o tipo**: Direcionar para a função específica correspondente

Esta função é específica para **Atendimentos Avulso Sistemas**. Para outros tipos, use:
- `inserir_atendimentos_os` (vinculados a OS)  
- `inserir_atendimento_avulso_infraestrutura` (área de Infraestrutura)

**Endpoint utilizado:** `inserirAtendimentoAvulsoSigaIA`

**Estrutura do XML retornado:**
```xml
<atendimentos_avulsos dataIni="2024-01-15 09:00:00" dataFim="2024-01-15 17:00:00"
                        matSolicitante="123456" tipo="19" descricao="Descrição"
                        origem="3" equipe="AVA" analista="789" projeto="73" sistema="271">
    <atendimento_avulso sistema="SIGA">
        <status>sucesso</status>
        <mensagem>Atendimento avulso cadastrado com sucesso!</mensagem>
    </atendimento_avulso>
</atendimentos_avulsos>
```

**Em caso de erro de validação:**
```xml
<erro_validacao sistema="SIGA" funcao="inserir_atendimento_avulso_sistemas">
    <erro sistema="SIGA">
        <status>erro</status>
        <tipo_erro>tipo_invalido</tipo_erro>
        <tipo_informado>Tipo Inválido</tipo_informado>
        <mensagem>Tipo 'Tipo Inválido' não encontrado na constante TIPO_TO_NUMBER_ATENDIMENTO_AVULSO</mensagem>
        <tipos_validos>['Suporte Sistema', 'Manutenção de Banco', 'Atividade Interna']</tipos_validos>
    </erro>
</erro_validacao>
```

**Em caso de erro de validação (analista obrigatório):**
```xml
<erro_validacao sistema="SIGA" funcao="inserir_atendimento_avulso_sistemas">
    <erro sistema="SIGA">
        <status>erro</status>
        <tipo_erro>analista_obrigatorio</tipo_erro>
        <campo_invalido>codigo_analista</campo_invalido>
        <valor_informado>0</valor_informado>
        <mensagem>Campo 'codigo_analista' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: 0</mensagem>
    </erro>
</erro_validacao>
```

**Em caso de erro (dados inválidos):**
```xml
<atendimentos_avulsos dataIni="2024-01-15 09:00:00" dataFim="2024-01-15 17:00:00"
                        matSolicitante="123456" tipo="19" descricao="Descrição"
                        origem="3" equipe="AVA" analista="789" projeto="67" sistema="271">
    <atendimento_avulso sistema="SIGA">
        <status>erro</status>
        <mensagem>Não foi possível salvar o atendimento avulso. Verifique as informações digitadas.</mensagem>
    </atendimento_avulso>
</atendimentos_avulsos>
```

**Em caso de outros erros:**
```xml
<atendimentos_avulsos dataIni="2024-01-15 09:00:00" dataFim="2024-01-15 17:00:00"
                        matSolicitante="123456" tipo="19" descricao="Descrição"
                        origem="3" equipe="AVA" analista="789" projeto="67" sistema="271">
    <atendimento_avulso sistema="SIGA">
        <status>erro</status>
        <mensagem>Erro ao gravar o atendimento avulso. Tente novamente.</mensagem>
    </atendimento_avulso>
</atendimentos_avulsos>
```

Args:
    data_inicio (str): Data e hora de início do atendimento avulso.
        Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
    data_fim (str): Data e hora de fim do atendimento avulso.
        Aceita formatos de data ou palavras-chave como "hoje", "agora", "ontem"
    matricula_solicitante (str | Literal["CURRENT_USER"]): Matrícula do usuário que está solicitando o atendimento avulso
    descricao_atendimento (str): Descrição detalhada do atendimento avulso a ser realizado
    codigo_analista (str | Literal["CURRENT_USER"]): **[OBRIGATÓRIO]** Matrícula do analista/usuário responsável pelo atendimento avulso.
    Deve ser "CURRENT_USER" ou um número válido maior que zero. Não aceita valores vazios, "0" ou não-numéricos.
    tipo (Literal): Tipo do atendimento avulso, deve ser um dos valores válidos:
        - "Suporte Sistema" (código 1)
        - "Manutenção de Banco" (código 10)
        - "Atividade Interna" (código 19) - padrão
    origem (Literal): Canal/origem do atendimento avulso, deve ser um dos valores válidos:
        - "E-mail" (código 1)
        - "Pessoalmente" (código 2)
        - "Teams" (código 3) - padrão
        - "Telefone" (código 4)
        - "WhatsApp" (código 5)
        - "Plantão" (código 7)
        - "SAE" (código 11)
    sistema (Literal): Sistema relacionado ao atendimento avulso, deve ser um dos valores válidos:
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
    equipe (Literal): Equipe responsável pelo atendimento avulso, deve ser uma das equipes válidas:
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
        - "Operação AVA" (código 67) - padrão
        - "Operação Banco de Dados" (código 207)
        - "Operação Biblioteca" (código 30)
        - "Operação Clínicas" (código 2)
        - "Operação Compras" (código 3)
        - "Operação Financeiro/Contabilidade" (código 4)
        - "Operação Gestão de Relacionamento" (código 72)
        - "Operação Help Desk" (código 61)
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

Returns:
    str: XML formatado contendo:
        - Em caso de sucesso: confirmação da inserção com status "sucesso"
        - Em caso de erro de validação: detalhes do erro (tipo inválido, analista obrigatório, origem inválida, etc.)
        - Em caso de erro de API: mensagem de erro específica
        - Em caso de erro interno: mensagem de erro genérica

        O XML sempre inclui os parâmetros enviados como atributos do elemento raiz.

Raises:
    Não levanta exceções diretamente. Todos os erros são capturados e retornados
    como XML formatado com informações detalhadas do erro.

Examples:
    >>> # Inserir atendimento avulso básico
    >>> xml = await inserir_atendimento_avulso_sistemas(
    ...     data_inicio="2024-01-15 09:00:00",
    ...     data_fim="2024-01-15 17:00:00",
    ...     matricula_solicitante="123456",
    ...     descricao_atendimento="Suporte ao sistema AVA",
    ...     codigo_analista=789
    ... )

    >>> # Inserir atendimento com projeto específico
    >>> xml = await inserir_atendimento_avulso_sistemas(
    ...     data_inicio="hoje 09:00",
    ...     data_fim="hoje 17:00",
    ...     matricula_solicitante="654321",
    ...     descricao_atendimento="Manutenção preventiva do banco de dados",
    ...     codigo_analista=456,
    ...     tipo="Manutenção de Banco",
    ...     origem="E-mail",
    ...     sistema="MV - Sistema de Apoio",
    ...     equipe="Administador de Banco de Dados",
    ...     projeto="Operação Banco de Dados"
    ... )

    >>> # Exemplo com tipo inválido (retorna erro)
    >>> xml = await inserir_atendimento_avulso_sistemas(
    ...     data_inicio="2024-01-15 09:00:00",
    ...     data_fim="2024-01-15 17:00:00",
    ...     matricula_solicitante="123456",
    ...     descricao_atendimento="Teste",
    ...     codigo_analista=789,
    ...     tipo="Tipo Inexistente"  # Erro!
    ... )

    >>> # Exemplo com codigo_analista inválido (retorna erro)
    >>> xml = await inserir_atendimento_avulso_sistemas(
    ...     data_inicio="2024-01-15 09:00:00",
    ...     data_fim="2024-01-15 17:00:00",
    ...     matricula_solicitante="123456",
    ...     descricao_atendimento="Teste",
    ...     codigo_analista="0",  # Erro!
    ...     tipo="Atividade Interna"
    ... )

Notes:
    - **DIFERENCIAÇÃO DE FUNÇÃO**: Esta função cria novos atendimentos avulso sistemas. Para editar, use editar_atendimento_avulso_sistemas 
    - **VALIDAÇÃO OBRIGATÓRIA**: Campo codigo_analista deve ser "CURRENT_USER" ou um número válido maior que zero (não aceita valores vazios, "0" ou não-numéricos)
    - Esta função é específica para ÁREA SISTEMAS (área=1)
    - A função realiza validação case-insensitive de todos os campos (tipo, origem, sistema, equipe, projeto)
    - As datas são automaticamente convertidas usando converter_data_siga com manter_horas=True
    - Utiliza as constantes: TIPO_TO_NUMBER_ATENDIMENTO_AVULSO, ORIGEM_TO_NUMBER, SISTEMA_TO_NUMBER,
        EQUIPE_TO_NUMBER, PROJETO_TO_NUMBER para mapear valores para códigos numéricos
    - Todos os parâmetros enviados são incluídos como atributos no XML de resposta
    - A API key é obtida automaticamente da variável de ambiente AVA_API_KEY
    - Em caso de falha na requisição HTTP, retorna erro interno formatado em XML
    - O resultado da API (1 = sucesso, outros valores = erro) é interpretado automaticamente
    - Campos opcionais como nomeSolicitante, centroCusto, etc. são enviados vazios por padrão
    - Esta função cria atendimentos avulsos independentes, não vinculados a nenhuma OS
"""
