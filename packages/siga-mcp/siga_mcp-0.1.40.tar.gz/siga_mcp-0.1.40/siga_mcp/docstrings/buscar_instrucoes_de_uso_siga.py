from textwrap import dedent


def docs() -> str:
    return dedent("""\
            **IMPORTANTE**
            Antes de chamar outra função, chame esta para obter as instruções de uso do SIGA.
            É impresscindível SEMPRE chamar essa função antes de qualquer outra. Não chame
            essa função mais de uma vez por conversa.
            """)
