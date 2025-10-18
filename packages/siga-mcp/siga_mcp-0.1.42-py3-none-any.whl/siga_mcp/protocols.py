from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ConfidentialClientProtocol(Protocol):
    """Subset of MSAL ConfidentialClientApplication used here.

    Return type allows None to match msal's untyped stubs and avoid incompatibilities.
    """

    def acquire_token_for_client(
        self,
        scopes: list[str],
        claims_challenge: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | None: ...
