def docs() -> str:
    return """
Busca pendências de lançamentos de atendimentos no sistema SIGA para um analista específico.

Esta função identifica os dias em que o usuário (analista) não efetuou nenhum tipo de
registro no sistema SIGA, incluindo criação de OS, Atendimentos OS ou Atendimentos Avulsos.
É uma ferramenta essencial para controle de produtividade e identificação de lacunas
nos registros de trabalho.

Funcionalidades:
- Identifica dias sem registros de atividades no SIGA
- Suporte a diferentes formatos de data (incluindo linguagem natural)
- Filtragem por período específico (data início e fim)
- Tratamento robusto de erros HTTP e de processamento
- Retorno estruturado em formato XML

Endpoint utilizado:
- URL: https://ava3.uniube.br/ava/api/atendimentosAvulsos/buscarPendenciasRegistroAtendimentosSigaIA/
- Método: POST
- Autenticação: API Key (AVA_API_KEY)

Estrutura do XML retornado:
- Elemento raiz: <pendencias_lançamentos>
- Atributos do elemento raiz: matricula (matrícula do analista)
- Atributos customizados: sistema="SIGA"
- Contém lista de dias/períodos sem registros

Tipos de registros verificados:
- Criação de Ordens de Serviço (OS)
- Atendimentos de OS
- Atendimentos Avulsos
- Qualquer outro tipo de lançamento no SIGA

Args:
    matricula (str | int | Literal["CURRENT_USER"], optional): Matrícula do analista para consulta.
                                                Pode ser string, número inteiro ou "CURRENT_USER".
                                                Se "CURRENT_USER", utiliza matrícula do usuário atual do arquivo .env.
                                                Defaults to "CURRENT_USER".
    dataIni (str): Data de início do período de consulta.
                                                        Aceita formatos de data padrão ou
                                                        palavras-chave em português.
    dataFim (str): Data de fim do período de consulta.
                                                        Aceita formatos de data padrão ou
                                                        palavras-chave em português.

Returns:
    str: XML bem formatado contendo as pendências de lançamentos encontradas.
            Em caso de erro na requisição ou processamento, retorna a mensagem:
            "Erro ao consultar todas as pendências de registros SIGA do usuário."

Raises:
    Exception: Captura qualquer exceção durante a requisição HTTP ou
                processamento dos dados, retornando mensagem de erro amigável.

Example:
    >>> resultado = await buscar_pendencias_lancamentos_atendimentos(
    ...     matricula="12345",
    ...     dataIni="01/01/2024",
    ...     dataFim="hoje"
    ... )
    >>> print(resultado)
    <?xml version="1.0" ?>
    <pendencias_lançamentos matricula="12345" sistema="SIGA">
        <pendencia>
        <data>02/01/2024</data>
        <tipo>Sem registros</tipo>
        </pendencia>
        ...
    </pendencias_lançamentos>

Note:
    - Requer variável de ambiente AVA_API_KEY configurada
    - A função é assíncrona e deve ser chamada com await
    - Utiliza a função converter_data_siga() para processar datas
    - Suporte a linguagem natural para datas ("hoje", "ontem", "agora")
    - Utiliza aiohttp para requisições HTTP assíncronas
    - O XML é formatado usando a classe XMLBuilder interna
    - Parâmetros são keyword-only (uso obrigatório de nomes dos parâmetros)
"""
