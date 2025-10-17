from textwrap import dedent


def docs() -> str:
    return dedent("""\
            Busca informações detalhadas de um atendimento avulso específico.

            Esta função realiza uma consulta ao sistema SIGA através da API do AVA para obter
            todas as informações relacionadas a um atendimento avulso específico. 
            **Com busca automática**: Se não encontrar em avulsos, busca automaticamente em atendimentos OS.
            É especialmente útil para consultar dados antes de realizar qualquer operação no atendimento.
                  
            **ORIENTAÇÃO PARA SOLICITAÇÕES GENÉRICAS:**
            Esta função é específica para **Atendimentos Avulsos**, mas com busca automática em:
            - `buscar_informacoes_atendimentos_os` se não encontrar em avulsos
                  
            **Funcionalidade de busca automática:**
            Se o atendimento não for encontrado nos registros de avulsos, a função automaticamente
            tentará buscar nas tabelas de atendimentos OS, fornecendo uma experiência
            transparente ao usuário.

            Funcionalidades:
            - Consulta dados completos de um atendimento avulso pelo código e analista responsável
            - **BUSCA AUTOMÁTICA** em atendimentos OS se não encontrar em avulsos
            - Garante precisão na identificação do registro correto (evita ambiguidade entre códigos duplicados)
            - Retorna informações estruturadas em formato XML
            - Inclui tratamento de erros para requisições mal-sucedidas
            - Utiliza autenticação via API Key do AVA

            Endpoint utilizado:
            - URL: https://ava3.uniube.br/ava/api/atendimentosAvulsos/buscarInfoAtendimentoAvulsoSigaIA/
            - Método: POST
            - Autenticação: API Key (AVA_API_KEY)

            Estrutura do XML retornado:
            - Elemento raiz: <info_atendimentos_avulsos> (se encontrado em avulsos) ou resultado da busca automática em OS
            - Atributos do elemento raiz: atendimento (código do atendimento) e analista (código do analista) 
            - Atributos customizados: sistema="SIGA"
            - Contém todos os dados do atendimento retornados pela API

            Args:
                codigo_atendimento (int): Código único identificador do atendimento avulso. Obrigatório. 
                    Deve ser um número inteiro válido correspondente a um atendimento existente no sistema SIGA.
                codigo_analista (str | Literal["CURRENT_USER"]): Matrícula do analista/usuário responsável pelo atendimento avulso. Obrigatório.
                    É necessário para garantir a identificação precisa do registro, evitando conflitos com códigos duplicados entre diferentes tipos de atendimento.

            Returns:
                str: XML bem formatado contendo as informações do atendimento encontrado.
                    - Se encontrado em avulsos: XML com estrutura de atendimentos avulsos
                    - Se encontrado em OS: XML com estrutura de atendimentos OS
                    - Em caso de erro: "Erro ao buscar as informações do atendimento em ambas as tabelas (Avulso e OS)."

            Raises:
                Exception: Captura qualquer exceção durante a requisição HTTP ou
                        processamento dos dados, retornando mensagem de erro amigável.

            Example:
                >>> # Busca atendimento (encontrado em avulsos)
                >>> resultado = await buscar_informacoes_atendimento_avulso(12345, "3214")
                >>> print(resultado)
                <?xml version="1.0" ?>
                <info_atendimentos_avulsos atendimento="12345" analista="3214" sistema="SIGA">
                    <campo1>valor1</campo1>
                    <campo2>valor2</campo2>
                    ...
                </info_atendimentos_avulsos>


                # Exemplo usando CURRENT_USER
                >>> resultado = await buscar_informacoes_atendimento_avulso(12345, "CURRENT_USER")
                  
                # Exemplo: não encontrado em avulsos, busca automaticamente em OS
                >>> resultado = await buscar_informacoes_atendimento_avulso(67890, "3214")

            Notes:
                - **DIFERENCIAÇÃO DE FUNÇÃO**: Esta função busca primeiro em avulsos, depois automaticamente em OS
                - **BUSCA AUTOMÁTICA**: Transparente ao usuário - retorna o atendimento independente do tipo
                - Requer variável de ambiente AVA_API_KEY configurada
                - A função é assíncrona e deve ser chamada com await
                - Utiliza aiohttp para requisições HTTP assíncronas
                - O XML é formatado usando a classe XMLBuilder interna
                - Ambos os parâmetros (codigo_atendimento e codigo_analista) são obrigatórios para evitar conflitos com códigos duplicados em diferentes tabelas do sistema
            """)
