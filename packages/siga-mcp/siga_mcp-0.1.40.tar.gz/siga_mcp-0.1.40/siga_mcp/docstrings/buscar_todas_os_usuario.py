def docs() -> str:
    return """
Busca Ordens de Serviço (OS) do sistema SIGA com filtros avançados e flexíveis.

Esta função oferece uma interface completa para consulta de OS no sistema SIGA,
permitindo filtros por matrícula, código de OS, status, e período. Suporta consultas
tanto individuais quanto em lote, sendo ideal para relatórios e análises.

Funcionalidades:
- Consulta por matrícula única ou múltiplas matrículas
- Busca por código de OS específico ou múltiplas OS
- Filtros por status predefinidos ou customizados
- Filtro por período (data início e fim)
- Grupo especial "Todas OS em Aberto" para consultas rápidas
- Suporte a linguagem natural para datas
- Validação de parâmetros obrigatórios

Endpoint utilizado:
- URL: https://ava3.uniube.br/ava/api/os/buscarTodasOsPorMatriculaSigaIA/
- Método: POST
- Autenticação: API Key (AVA_API_KEY)

Estrutura do XML retornado:
- Elemento raiz: <ordens_servico>
- Elemento item: <ordem_servico>
- Atributos do elemento raiz: matricula (matrícula consultada)
- Atributos customizados: sistema="SIGA"

Status de OS disponíveis:
- Pendente-Atendimento, Em Teste, Pendente-Teste, Em Atendimento
- Em Implantação, Pendente-Liberação, Concluída, Concluída por Encaminhamento
- Concluída por substituição, Não Planejada, Pendente-Sist. Administrativos
- Pendente-AVA, Pendente-Consultoria, Solicitação em Aprovação
- Pendente-Aprovação, Pendente-Sist. Acadêmicos, Pendente-Marketing
- Pendente-Equipe Manutenção, Pendente-Equipe Infraestrutura
- Pendente-Atualização de Versão, Pendente-Help-Desk
- Cancelamento DTI | Arquivado, Cancelada-Usuário
- Pendente-Fornecedor, Pendente-Usuário

Args:
    matricula (str | Sequence[str] | Literal["CURRENT_USER"] | None, optional): Matrícula(s) do(s) usuário(s).
                                                                - String única: "12345"
                                                                - Lista: ["12345", "67890"] para múltiplas
                                                                - None: busca de todos os usuários
                                                                - "CURRENT_USER": usar matrícula do usuário atual do .env
                                                                Defaults to None.
    os (str | Sequence[str] | None, optional): Código(s) da(s) OS para consulta específica.
                                                - String única: "98765"
                                                - Lista: ["98765", "54321"] para múltiplas
                                                - None: sem filtro por OS específica
                                                Defaults to None.
    filtrar_por (Sequence[Literal] | Literal["Todas OS em Aberto"] | str | None, optional):
                Status para filtrar as OS.
                - "Todas OS em Aberto": grupo pré-definido de status em aberto
                - Lista: ["Concluída", "Pendente-Teste"] para múltiplos status
                - String: status único
                - None: sem filtro de status
                Defaults to None.
    data_inicio (str | None, optional):
                Data de início do período de consulta.
                Aceita formatos de data padrão ou palavras-chave em português.
                Defaults to None.
    data_fim (str | None, optional):
                Data de fim do período de consulta.
                Aceita formatos de data padrão ou palavras-chave em português.
                Defaults to None.

Returns:
    str: XML bem formatado contendo as OS encontradas.
            Em caso de parâmetros inválidos, retorna:
            "Erro: É necessário informar pelo menos a matrícula ou o código da OS para realizar a consulta."
            Em caso de erro na requisição, retorna:
            "Erro ao consultar dados da(s) OS."

Raises:
    Exception: Captura qualquer exceção durante a requisição HTTP ou
                processamento dos dados, retornando mensagem de erro amigável.

Examples:
    Casos de uso principais:

    1. OS em aberto de uma matrícula:
    >>> resultado = await buscar_todas_os_usuario(
    ...     matricula="12345",
    ...     filtrar_por="Todas OS em Aberto"
    ... )

    2. OS em aberto de múltiplas matrículas:
    >>> resultado = await buscar_todas_os_usuario(
    ...     matricula=["12345", "67890"],
    ...     filtrar_por="Todas OS em Aberto"
    ... )

    3. OS por status específico:
    >>> resultado = await buscar_todas_os_usuario(
    ...     matricula="12345",
    ...     filtrar_por=["Concluída", "Concluída por Encaminhamento"]
    ... )

    4. OS específicas por código:
    >>> resultado = await buscar_todas_os_usuario(
    ...     os=["1001", "1002"],
    ...     matricula=None
    ... )

    5. OS com filtro de período:
    >>> resultado = await buscar_todas_os_usuario(
    ...     matricula="12345",
    ...     data_inicio="01/01/2024",
    ...     data_fim="hoje"
    ... )

Note:
    - Pelo menos 'matricula' ou 'os' deve ter valor válido para executar a consulta
    - Requer variável de ambiente AVA_API_KEY configurada
    - A função é assíncrona e deve ser chamada com await
    - Utiliza a função converter_data_siga() para processar datas
    - Suporte a linguagem natural para datas ("hoje", "ontem", "agora")
    - Utiliza aiohttp para requisições HTTP assíncronas
    - O XML é formatado usando a classe XMLBuilder interna
    - Parâmetros são keyword-only (uso obrigatório de nomes dos parâmetros)
    - O filtro "Todas OS em Aberto" é expandido automaticamente para todos os status em aberto

"""
