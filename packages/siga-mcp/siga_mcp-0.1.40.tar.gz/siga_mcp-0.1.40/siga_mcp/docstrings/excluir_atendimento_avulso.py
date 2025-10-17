from textwrap import dedent


def docs() -> str:
    return dedent("""\
            Exclui um atendimento avulso específico do sistema SIGA.

            **INSTRUÇÃO PARA O AGENTE IA:**
            ANTES de executar esta função de exclusão:
            1. SEMPRE chame primeiro `buscar_informacoes_atendimento_avulso(codigo_atendimento, codigo_analista)`
            2. MOSTRE ao usuário TODAS as informações do atendimento que será EXCLUÍDO
            3. PEÇA confirmação explícita do usuário: "Confirma a exclusão? (sim/não)"
            4. SÓ EXECUTE esta função se o usuário confirmar explicitamente
            5. Se o usuário não confirmar, cancele a operação e informe que foi cancelada

            Esta função remove permanentemente um atendimento avulso do sistema SIGA (tanto Sistemas quanto Infraestrutura).
            Utiliza o código do atendimento e código do analista para garantir identificação precisa.
            **ATENÇÃO: Esta operação é irreversível.**
                  
            **ORIENTAÇÃO PARA SOLICITAÇÕES GENÉRICAS:**
            Quando o usuário solicitar "excluir um atendimento" sem especificar o tipo:
            1. **Primeiro**: Tente excluir_atendimentos_os 
            2. **Se não encontrar**: Use automaticamente esta função (excluir_atendimento_avulso)
            3. **Busca automática**: Use as funções buscar_informacoes_atendimentos_os e buscar_informacoes_atendimento_avulso para identificar o tipo
            4. **Confirmação**: Sempre mostre as informações do atendimento antes de excluir

            Esta função é específica para **Atendimentos Avulso** (tanto Sistemas quanto Infraestrutura). Para atendimentos OS, use:
            - `excluir_atendimentos_os` (vinculados a OS)
                  
            **Funcionalidade de busca automática:**
            Se o atendimento não for encontrado nesta função (atendimentos avulsos), a mensagem de erro orientará a buscar na função excluir_atendimentos_os, permitindo busca automática entre os tipos de atendimento.

            Funcionalidades:
            - Exclui atendimento avulso pelo código e analista responsável
            - Garante precisão na identificação do registro correto (evita ambiguidade entre códigos duplicados)
            - Retorna informações estruturadas em formato XML com status da operação
            - Inclui tratamento de erros para diferentes cenários de falha
            - Utiliza autenticação via API Key do AVA
            - Orienta busca automática em atendimentos OS quando não encontra o registro

            Endpoint utilizado:
            - URL: https://ava3.uniube.br/ava/api/atendimentosAvulsos/excluiAtendimentoAvulsoSigaIA/
            - Método: POST
            - Autenticação: API Key (AVA_API_KEY)

            **Estrutura do XML retornado:**

            **Sucesso:**
            ```xml
            <exclusões_atendimento_avulso atendimento="123" analista="3214" sistema="SIGA">
                <exclusão sistema="SIGA">
                    <status>sucesso</status>
                    <mensagem>Atendimento avulso excluído com sucesso!</mensagem>
                </exclusão>
            </exclusões_atendimento_avulso>
            ```

            **Em caso de erro (atendimento não encontrado):**
            ```xml
            <exclusões_atendimento_avulso atendimento="123" analista="3214" sistema="SIGA">
                <exclusão sistema="SIGA">
                    <status>erro</status>
                    <mensagem>Atendimento não encontrado em Avulso. Tente buscar na função excluir_atendimentos_os.</mensagem>
                </exclusão>
            </exclusões_atendimento_avulso>
            ```

            **Em caso de outros erros:**
            ```xml
            <exclusões_atendimento_avulso atendimento="123" analista="3214" sistema="SIGA">
                <exclusão sistema="SIGA">
                    <status>erro</status>
                    <mensagem>Erro ao excluir o atendimento avulso. Tente novamente.</mensagem>
                </exclusão>
            </exclusões_atendimento_avulso>
            ```

            Args:
                codigo_atendimento (int): Código único identificador do atendimento avulso. Obrigatório.
                    Deve ser um número inteiro válido correspondente a um atendimento existente no sistema SIGA.
                codigo_analista (str | Literal["CURRENT_USER"]): Matrícula do analista/usuário responsável pelo atendimento avulso. Obrigatório.
                    É necessário para garantir a identificação precisa do registro, evitando conflitos com códigos duplicados entre diferentes tipos de atendimento.

            Returns:
                str: XML bem formatado contendo o resultado da operação de exclusão.
                    - Em caso de sucesso: status "sucesso" com mensagem de confirmação
                    - Em caso de atendimento não encontrado: status "erro" com orientação para buscar em excluir_atendimentos_os
                    - Em caso de outros erros: status "erro" com mensagem explicativa
                    - Em caso de erro interno: mensagem de erro genérica

            Raises:
                Exception: Captura qualquer exceção durante a requisição HTTP ou processamento dos dados, retornando mensagem de erro amigável em formato XML.

            Example:
                >>> resultado = await excluir_atendimento_avulso(12345, "3214")
                >>> print(resultado)
                <?xml version="1.0" ?>
                <exclusões_atendimento_avulso atendimento="12345" analista="3214" sistema="SIGA">
                    <exclusão sistema="SIGA">
                        <status>sucesso</status>
                        <mensagem>Atendimento avulso excluído com sucesso!</mensagem>
                    </exclusão>
                </exclusões_atendimento_avulso>

                # Exemplo usando CURRENT_USER
                >>> resultado = await excluir_atendimento_avulso(12345, "CURRENT_USER")

                # Exemplo quando não encontra (orienta busca automática)
                >>> resultado = await excluir_atendimento_avulso(99999, "3214")
                >>> print(resultado)
                <?xml version="1.0" ?>
                <exclusões_atendimento_avulso atendimento="99999" analista="3214" sistema="SIGA">
                    <exclusão sistema="SIGA">
                        <status>erro</status>
                        <mensagem>Atendimento não encontrado em Avulso. Tente buscar na função excluir_atendimentos_os.</mensagem>
                    </exclusão>
                </exclusões_atendimento_avulso>

            Notes:
                 - **DIFERENCIAÇÃO DE FUNÇÃO**: Esta função exclui atendimentos avulsos (Sistemas e Infraestrutura). Para atendimentos OS, use excluir_atendimentos_os
                - **BUSCA AUTOMÁTICA**: Se não encontrar aqui, o sistema deve automaticamente tentar excluir_atendimentos_os
                - **ATENÇÃO**: Esta operação é irreversível. Uma vez excluído, o atendimento não pode ser recuperado
                - Para busca automática: Se não encontrar nesta função, use excluir_atendimentos_os com os mesmos parâmetros
                - Requer variável de ambiente AVA_API_KEY configurada
                - A função é assíncrona e deve ser chamada com await
                - Utiliza aiohttp para requisições HTTP assíncronas
                - O XML é formatado usando a classe XMLBuilder interna
                - Ambos os parâmetros (codigo_atendimento e codigo_analista) são obrigatórios para evitar conflitos com códigos duplicados em diferentes tabelas do sistema
                - Use com extrema cautela em ambientes de produção
            """)
