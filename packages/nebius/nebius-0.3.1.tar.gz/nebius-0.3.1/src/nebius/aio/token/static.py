import os
from logging import getLogger

from nebius.base.constants import TOKEN_ENV
from nebius.base.error import SDKError

from .token import Bearer as ParentBearer
from .token import Receiver as ParentReceiver
from .token import Token

log = getLogger(__name__)


class NoTokenInEnvError(SDKError):
    pass


class Receiver(ParentReceiver):
    def __init__(self, token: Token) -> None:
        super().__init__()
        self._latest = token

    async def _fetch(
        self, timeout: float | None = None, options: dict[str, str] | None = None
    ) -> Token:
        if self._latest is None:
            raise Exception("Token has to be set")
        log.debug("static token fetched")
        return self._latest

    def can_retry(
        self,
        err: Exception,
        options: dict[str, str] | None = None,
    ) -> bool:
        return False


class Bearer(ParentBearer):
    def __init__(self, token: Token | str) -> None:
        if isinstance(token, str):
            token = Token(token)
        if token.token == "":
            raise SDKError("empty token provided")
        super().__init__()
        self._tok = token

    def receiver(self) -> Receiver:
        return Receiver(self._tok)


class EnvBearer(Bearer):
    def __init__(self, env_var_name: str = TOKEN_ENV) -> None:
        val = os.environ.get(env_var_name, "")
        if val == "":
            raise NoTokenInEnvError(f"no token in env {env_var_name}")
        super().__init__(val)
