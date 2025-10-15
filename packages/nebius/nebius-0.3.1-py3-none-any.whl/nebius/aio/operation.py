from asyncio import sleep
from collections.abc import Iterable
from datetime import datetime, timedelta
from time import time
from typing import Generic, TypeVar

from grpc import CallCredentials, Compression, StatusCode

from nebius.aio.abc import ClientChannelInterface
from nebius.aio.request import DEFAULT_TIMEOUT
from nebius.base.error import SDKError
from nebius.base.protos.unset import Unset, UnsetType
from nebius.base.protos.well_known import local_timezone

from .constant_channel import Constant
from .request_status import RequestStatus

OperationPb = TypeVar("OperationPb")
T = TypeVar("T")


class Operation(Generic[OperationPb]):
    def __init__(
        self,
        source_method: str,
        channel: ClientChannelInterface,
        operation: OperationPb,
    ) -> None:
        from nebius.api.nebius.common.v1 import (
            GetOperationRequest,
            Operation,
            OperationServiceClient,
        )
        from nebius.api.nebius.common.v1alpha1 import (
            GetOperationRequest as OldGet,
        )
        from nebius.api.nebius.common.v1alpha1 import (
            Operation as Old,
        )
        from nebius.api.nebius.common.v1alpha1 import (
            OperationServiceClient as OldClient,
        )

        self._channel = channel
        _operation: OperationPb | Operation | Old = operation
        if isinstance(_operation, Operation.__PB2_CLASS__):
            _operation = Operation(_operation)
        if isinstance(_operation, Old.__PB2_CLASS__):
            _operation = Old(_operation)

        if isinstance(_operation, Operation):
            self._service: OperationServiceClient | OldClient = OperationServiceClient(
                Constant(source_method, channel)
            )
            self._get_request_obj: type[GetOperationRequest | OldGet] = (
                GetOperationRequest
            )
        elif isinstance(_operation, Old):
            self._service = OldClient(Constant(source_method, channel))
            self._get_request_obj = OldGet
        else:
            raise SDKError(f"Operation type {type(_operation)} not supported.")

        self._operation: Operation | Old = _operation

    def __repr__(self) -> str:
        return (
            f"Operation({self.id}, resource_id: {self.resource_id}, "
            f"status: {self.status()})"
        )

    def status(self) -> RequestStatus | None:
        return self._operation.status

    def done(self) -> bool:
        return self.status() is not None

    async def update(
        self,
        metadata: Iterable[tuple[str, str]] | None = None,
        timeout: float | None | UnsetType = Unset,
        credentials: CallCredentials | None = None,
        compression: Compression | None = None,
        per_retry_timeout: float | None | UnsetType = Unset,
        retries: int | None = None,
    ) -> None:
        if self.done():
            return

        req = self._service.get(
            self._get_request_obj(id=self.id),  # type: ignore
            metadata=metadata,
            timeout=timeout,
            credentials=credentials,
            compression=compression,
            per_retry_timeout=per_retry_timeout,
            retries=retries,
        )
        new_op = await req
        self._set_new_operation(new_op._operation)  # type: ignore

    def sync_wait(
        self,
        interval: float | timedelta = 1,
        metadata: Iterable[tuple[str, str]] | None = None,
        timeout: float | None = None,
        credentials: CallCredentials | None = None,
        compression: Compression | None = None,
        poll_iteration_timeout: float | None | UnsetType = Unset,
        poll_per_retry_timeout: float | None | UnsetType = Unset,
        poll_retries: int | None = None,
    ) -> None:
        run_timeout = None if timeout is None else timeout + 0.2
        return self._channel.run_sync(
            self.wait(
                interval=interval,
                metadata=metadata,
                timeout=timeout,
                credentials=credentials,
                compression=compression,
                poll_iteration_timeout=poll_iteration_timeout,
                poll_per_retry_timeout=poll_per_retry_timeout,
                poll_retries=poll_retries,
            ),
            run_timeout,
        )

    def sync_update(
        self,
        metadata: Iterable[tuple[str, str]] | None = None,
        timeout: float | None | UnsetType = Unset,
        credentials: CallCredentials | None = None,
        compression: Compression | None = None,
        per_retry_timeout: float | None | UnsetType = Unset,
        retries: int | None = None,
    ) -> None:
        run_timeout: float | None = None
        if isinstance(timeout, (int, float)):
            run_timeout = timeout + 0.2
        elif isinstance(timeout, UnsetType):
            run_timeout = DEFAULT_TIMEOUT + 0.2
        return self._channel.run_sync(
            self.update(
                metadata=metadata,
                timeout=timeout,
                credentials=credentials,
                compression=compression,
                per_retry_timeout=per_retry_timeout,
                retries=retries,
            ),
            run_timeout,
        )

    async def wait(
        self,
        interval: float | timedelta = 1,
        metadata: Iterable[tuple[str, str]] | None = None,
        timeout: float | None = None,
        credentials: CallCredentials | None = None,
        compression: Compression | None = None,
        poll_iteration_timeout: float | UnsetType | None = Unset,
        poll_per_retry_timeout: float | UnsetType | None = Unset,
        poll_retries: int | None = None,
    ) -> None:
        start = time()
        if poll_iteration_timeout is None:
            if timeout is not None:
                poll_iteration_timeout = min(5, timeout)
        if isinstance(interval, timedelta):
            interval = interval.total_seconds()
        from nebius.aio.service_error import RequestError as ServiceRequestError

        def _is_ignorable(err: Exception) -> bool:
            # TimeoutError raised locally or RequestError with DEADLINE_EXCEEDED
            if isinstance(err, TimeoutError):
                return True
            if isinstance(err, ServiceRequestError):
                try:
                    return err.status.code == StatusCode.DEADLINE_EXCEEDED
                except Exception:  # pragma: no cover - defensive
                    return False
            return False

        async def _safe_update() -> None:
            try:
                await self.update(
                    metadata=metadata,
                    timeout=poll_iteration_timeout,
                    credentials=credentials,
                    compression=compression,
                    per_retry_timeout=poll_per_retry_timeout,
                    retries=poll_retries,
                )
            except Exception as e:  # noqa: S110
                if not _is_ignorable(e):
                    raise

        if not self.done():
            await _safe_update()
        while not self.done():
            current_time = time()
            if timeout is not None and current_time > timeout + start:
                raise TimeoutError("Operation wait timeout")
            await sleep(interval)
            await _safe_update()

    def _set_new_operation(self, operation: OperationPb) -> None:
        if isinstance(operation, self._operation.__class__):
            self._operation = operation  # type: ignore
        else:
            raise SDKError(f"Operation type {type(operation)} not supported.")

    @property
    def id(self) -> str:
        return self._operation.id

    @property
    def description(self) -> str:
        return self._operation.description

    @property
    def created_at(self) -> datetime:
        ca = self._operation.created_at
        if ca is None:  # type: ignore[unused-ignore]
            return datetime.now(local_timezone)
        return ca

    @property
    def created_by(self) -> str:
        return self._operation.created_by

    @property
    def finished_at(self) -> datetime | None:
        return self._operation.finished_at

    @property
    def resource_id(self) -> str:
        return self._operation.resource_id

    def successful(self) -> bool:
        s = self.status()
        return s is not None and s.code == StatusCode.OK

    def raw(self) -> OperationPb:
        return self._operation  # type: ignore
