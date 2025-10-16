# import asyncio

# from siga_mcp.tools import inserir_os_infraestrutura
from siga_mcp.dynamic_constants import obter_usuarios_responsavel
# from siga_mcp.tools import listar_usuarios_responsaveis_os_siga


"""def main() -> str:
return listar_usuarios_responsaveis_os_siga(
    **{
        "area": "1",
    }
)"""


def main() -> str:
    # Testar Sistemas (área 1)
    docstring_sistemas, ids_sistemas, erro_sistemas = obter_usuarios_responsavel(1)

    # Testar Infraestrutura (área 2)
    docstring_infra, ids_infra, erro_infra = obter_usuarios_responsavel(2)

    return f"""
        === SISTEMAS ===
        {docstring_sistemas}
        IDs: {ids_sistemas}
        Erro: {erro_sistemas}
        === INFRAESTRUTURA ===
        {docstring_infra}
        IDs: {ids_infra}
        Erro: {erro_infra}
        """


if __name__ == "__main__":
    resultado = main()
print(resultado)


""" async def main() -> str:
    return await inserir_os_infraestrutura(
        **{
            "data_solicitacao": "03/10/2025 08:31:17",
            "assunto": "Teste de gravação Infra",
            "descricao": "Este é apenas um teste de gravação Infra",
            "matSolicitante": "24142",
            "criada_por": "24142",
            "responsavel": "24142",
            "responsavel_atual": "24142",
        }
    )


if __name__ == "__main__":
    resultado = asyncio.run(main())
    print(resultado) """


""" async def main() -> str:
    return await listar_usuarios_responsaveis_os_siga(
        **{
            "area": "2",
        }
    )


if __name__ == "__main__":
    resultado = asyncio.run(main())
    print(resultado) """
