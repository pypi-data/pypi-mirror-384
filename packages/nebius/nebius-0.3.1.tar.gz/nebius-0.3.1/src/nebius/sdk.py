from collections.abc import Iterable

from grpc import CallCredentials, Compression

from nebius.aio.channel import Channel
from nebius.aio.request import Request
from nebius.api.nebius.iam.v1 import (
    GetProfileRequest,
    GetProfileResponse,
    ProfileServiceClient,
)
from nebius.base.protos.unset import Unset, UnsetType


class SDK(Channel):
    def whoami(
        self,
        metadata: Iterable[tuple[str, str]] | None = None,
        timeout: float | None = None,
        credentials: CallCredentials | None = None,
        compression: Compression | None = None,
        retries: int | None = 3,
        per_retry_timeout: float | None = None,
        auth_timeout: float | None | UnsetType = Unset,
        auth_options: dict[str, str] | None = None,
    ) -> Request[GetProfileRequest, GetProfileResponse]:
        client = ProfileServiceClient(self)
        return client.get(
            GetProfileRequest(),
            metadata=metadata,
            auth_timeout=auth_timeout,
            auth_options=auth_options,
            timeout=timeout,
            credentials=credentials,
            compression=compression,
            retries=retries,
            per_retry_timeout=per_retry_timeout,
        )
