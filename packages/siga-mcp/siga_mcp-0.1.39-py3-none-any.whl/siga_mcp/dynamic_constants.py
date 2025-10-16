"""Este módulo contém funções que geram constantes dinâmicas a partir da API"""

import httpx
from os import getenv


# Obter usuário responsável para criação de OS Sistemas e Infraestrutura.
# Usado para montar o Docstring e validação na função, caso o usuário informa matrícula que não está na lista
def obter_usuarios_responsavel(area: int) -> tuple[str, set[int], list[str]]:
    # Determinar nome da área para mensagens de erro
    nome_area = "Sistemas" if area == 1 else "Infraestrutura"

    try:
        # Fazer requisição HTTP para buscar usuários responsáveis
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://ava3.uniube.br/ava/api/usuarios/buscarUsuarioResponsavelOsSigaIA/",
                json={
                    "apiKey": getenv("AVA_API_KEY"),
                    "area": area,
                },
            )

            # Extrair dados JSON da resposta
            json_data = response.json()
            data = (
                json_data
                if isinstance(json_data, list)
                else json_data.get("result", [])
            )

            # Validar se recebeu dados válidos
            if not data or not isinstance(data, list):
                return (
                    f"        - Erro ao carregar usuários responsáveis de {nome_area}",
                    set(),
                    [],
                )

            # Remover duplicatas usando dict (chave = ID do usuário)
            usuarios_unicos = {}
            for usuario in data:
                if (
                    isinstance(usuario, dict)
                    and "USUARIO" in usuario
                    and "NOME" in usuario
                ):
                    usuarios_unicos[usuario["USUARIO"]] = usuario

            # Verificar se encontrou usuários válidos
            if not usuarios_unicos:
                return (
                    f"        - Nenhum usuário responsável encontrado para {nome_area}",
                    set(),
                    [],
                )

            # 📝 GERAR LISTA FORMATADA PARA DOCSTRING (ordenada alfabeticamente)
            usuarios_ordenados = sorted(
                usuarios_unicos.values(), key=lambda x: x["NOME"]
            )
            docstring = "\n".join(
                [
                    f'        - "{usuario["NOME"]}" (ID: {usuario["USUARIO"]})'
                    for usuario in usuarios_ordenados
                ]
            )

            # 🔍 GERAR SET DE IDS PARA VALIDAÇÃO RÁPIDA SE O USUÁRIO ESTÁ NA LISTA DE RESPONSÁVEIS DA ÁREA
            ids_validacao = {
                str(usuario["USUARIO"]) for usuario in usuarios_unicos.values()
            }

            # 🔍 GERAR LISTA PARA MENSAGENS DE ERRO, PARA AVISAR QUE O USUÁRIO NÃO ESTÁ NA LISTA DE RESPONSÁVEIS DAQUELA ÁREA
            usuarios_para_erro = [
                f'"{usuario["NOME"]}" (ID: {usuario["USUARIO"]})'
                for usuario in usuarios_ordenados
            ]

            # Retorna 3 resultados, para docstring, set de ids para validação rápida e lista para mensagens de erro
            return (docstring, ids_validacao, usuarios_para_erro)

    except Exception:
        # Retornar erro em caso de falha na requisição ou processamento
        return (
            f"        - Erro ao carregar usuários responsáveis de {nome_area}",
            set(),
            [],
        )


# ✅ CONSTANTES CACHED - Executam uma vez quando o módulo é carregado
# 📊 Buscar dados para Sistemas (área 1)
USUARIOS_SISTEMAS_DOCSTRING, USUARIOS_SISTEMAS_IDS, USUARIOS_SISTEMAS_PARA_ERRO = (
    obter_usuarios_responsavel(1)
)
# 🔧 Buscar dados para Infraestrutura (área 2)
(
    USUARIOS_INFRAESTRUTURA_DOCSTRING,
    USUARIOS_INFRAESTRUTURA_IDS,
    USUARIOS_INFRAESTRUTURA_PARA_ERRO,
) = obter_usuarios_responsavel(2)
