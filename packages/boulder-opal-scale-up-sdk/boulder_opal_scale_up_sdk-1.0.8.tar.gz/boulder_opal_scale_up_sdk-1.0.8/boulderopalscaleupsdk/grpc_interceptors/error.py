# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.

from __future__ import annotations

import inspect
import re
from typing import TYPE_CHECKING, Any

import grpc
import grpc.aio

from boulderopalscaleupsdk.errors import ScaleUpServerError

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator

# ------------------------
# Helpers
# ------------------------

_GRPC_MESSAGE_RE = re.compile(r'grpc_message:"([^"]+)"')


def _extract_peer_message(err: grpc.RpcError) -> str | None:
    dbg = getattr(err, "debug_error_string", None)
    if callable(dbg):
        try:
            s = dbg()
        except (AttributeError, TypeError, RuntimeError):
            return None
        if isinstance(s, str):
            m = _GRPC_MESSAGE_RE.search(s)
            if m:
                return m.group(1)
    return None


def _concise_error(err: grpc.RpcError, *, include_code: bool = False) -> str:
    msg = _extract_peer_message(err) or (err.details() or "An unknown error occurred.")
    if include_code:
        try:
            return f"{err.code().name}: {msg}"
        except (AttributeError, ValueError):
            pass
    return msg


# ------------------------
# SYNC wrappers
# ------------------------


class _UnaryUnaryCallWrapper:
    """Proxy that prettifies errors when .result() is called (sync)."""

    def __init__(self, inner: Any, include_code: bool) -> None:
        self._inner = inner
        self._include_code = include_code

    def result(self, timeout: float | None = None) -> Any:
        try:
            return self._inner.result(timeout)
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def __bool__(self) -> bool:
        return bool(self._inner)


class _SyncRespIterWrapper:
    """Wrap response-stream iterator to prettify RpcError during iteration (sync)."""

    def __init__(self, inner: Any, include_code: bool) -> None:
        self._inner = inner
        self._include_code = include_code

    def __iter__(self):
        try:
            yield from self._inner
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _SyncReqIterWrapper:
    """Wrap request-stream iterator to prettify RpcError while producing items (sync)."""

    def __init__(self, inner: Any, include_code: bool) -> None:
        self._inner = inner
        self._include_code = include_code

    def __iter__(self):
        try:
            yield from self._inner
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


# ------------------------
# ASYNC wrappers
# ------------------------


class _AioRespAsyncIterWrapper:
    """
    Async iterator proxy that prettifies errors from response streams (async).
    Accepts the Call object (UnaryStreamCall or StreamStreamCall).
    """

    def __init__(self, inner: Any, include_code: bool) -> None:
        self._inner = inner
        self._include_code = include_code

    def __aiter__(self) -> AsyncIterator[Any]:
        async def gen() -> AsyncIterator[Any]:
            try:
                async for item in self._inner:
                    yield item
            except grpc.RpcError as e:
                raise ScaleUpServerError(
                    _concise_error(e, include_code=self._include_code),
                ) from None

        return gen()

    async def initial_metadata(self) -> Any:
        try:
            return await self._inner.initial_metadata()
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    async def trailing_metadata(self) -> Any:
        try:
            return await self._inner.trailing_metadata()
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def cancel(self) -> None:
        return self._inner.cancel()

    def code(self) -> Any:
        return self._inner.code()

    def details(self) -> str:
        return self._inner.details()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _AioReqAsyncIterWrapper:
    """
    Async request iterator wrapper that prettifies errors when producing request items.
    Takes any AsyncIterable (not necessarily an AsyncIterator).
    """

    def __init__(self, inner: AsyncIterable[Any], include_code: bool) -> None:
        self._inner = inner
        self._include_code = include_code

    def __aiter__(self) -> AsyncIterator[Any]:
        async def gen() -> AsyncIterator[Any]:
            try:
                async for item in self._inner:
                    yield item
            except grpc.RpcError as e:
                raise ScaleUpServerError(
                    _concise_error(e, include_code=self._include_code),
                ) from None

        return gen()


# ------------------------
# Unified interceptor (sync + aio)
# ------------------------


class ErrorFormatterInterceptor(
    # sync interfaces
    grpc.UnaryUnaryClientInterceptor,
    grpc.UnaryStreamClientInterceptor,
    grpc.StreamUnaryClientInterceptor,
    grpc.StreamStreamClientInterceptor,
    # aio interfaces
    grpc.aio.UnaryUnaryClientInterceptor,
    grpc.aio.UnaryStreamClientInterceptor,
    grpc.aio.StreamUnaryClientInterceptor,
    grpc.aio.StreamStreamClientInterceptor,
):
    """
    Prettifies gRPC errors raised by the server into ScaleUpServerError.

    Works with both sync (grpc) and async (grpc.aio) channels.

    - Detects whether `continuation` is a coroutine function.
    - In async case, returns a coroutine that yields wrapped awaitable/async-iterable calls.
    - In sync case, returns wrapped blocking call objects/iterators.
    """

    def __init__(self, include_code: bool = False) -> None:
        self._include_code = include_code

    # ---------- UNARY -> UNARY ----------

    async def _async_unary_unary(self, continuation, client_call_details, request) -> Any:
        try:
            call = continuation(client_call_details, request)  # awaitable call
            # Await here so callers receive the *message*, mirroring AuthInterceptor.
            return await call
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def _sync_unary_unary(self, continuation, client_call_details, request) -> Any:
        try:
            call = continuation(client_call_details, request)  # blocking call
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None
        return _UnaryUnaryCallWrapper(call, self._include_code)

    def intercept_unary_unary(self, continuation, client_call_details, request):  # type: ignore[override]
        if inspect.iscoroutinefunction(continuation):
            return self._async_unary_unary(continuation, client_call_details, request)
        return self._sync_unary_unary(continuation, client_call_details, request)

    # ---------- UNARY -> STREAM ----------

    async def _async_unary_stream(self, continuation, client_call_details, request) -> Any:
        try:
            resp_call = continuation(client_call_details, request)  # async-iterable call
            # Do NOT await: return an iterator wrapper that prettifies stream errors.
            return _AioRespAsyncIterWrapper(resp_call, self._include_code)
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def _sync_unary_stream(self, continuation, client_call_details, request) -> Any:
        try:
            resp_iter = continuation(client_call_details, request)  # iterator
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None
        return _SyncRespIterWrapper(resp_iter, self._include_code)

    def intercept_unary_stream(self, continuation, client_call_details, request):  # type: ignore[override]
        if inspect.iscoroutinefunction(continuation):
            return self._async_unary_stream(continuation, client_call_details, request)
        return self._sync_unary_stream(continuation, client_call_details, request)

    # ---------- STREAM -> UNARY ----------

    async def _async_stream_unary(self, continuation, client_call_details, request_iterator) -> Any:
        try:
            wrapped_req = _AioReqAsyncIterWrapper(request_iterator, self._include_code)
            call = continuation(client_call_details, wrapped_req)  # awaitable call
            # Await and return the *message*.
            return await call
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def _sync_stream_unary(self, continuation, client_call_details, request_iterator) -> Any:
        try:
            wrapped_req = _SyncReqIterWrapper(request_iterator, self._include_code)
            call = continuation(client_call_details, wrapped_req)  # blocking call
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None
        return _UnaryUnaryCallWrapper(call, self._include_code)

    def intercept_stream_unary(self, continuation, client_call_details, request_iterator):  # type: ignore[override]
        if inspect.iscoroutinefunction(continuation):
            return self._async_stream_unary(continuation, client_call_details, request_iterator)
        return self._sync_stream_unary(continuation, client_call_details, request_iterator)

    # ---------- STREAM -> STREAM ----------

    async def _async_stream_stream(
        self,
        continuation,
        client_call_details,
        request_iterator,
    ) -> Any:
        try:
            wrapped_req = _AioReqAsyncIterWrapper(request_iterator, self._include_code)
            resp_call = continuation(client_call_details, wrapped_req)  # async-iterable call
            # Return iterator wrapper.
            return _AioRespAsyncIterWrapper(resp_call, self._include_code)
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None

    def _sync_stream_stream(self, continuation, client_call_details, request_iterator) -> Any:
        try:
            wrapped_req = _SyncReqIterWrapper(request_iterator, self._include_code)
            resp_iter = continuation(client_call_details, wrapped_req)  # iterator
        except grpc.RpcError as e:
            raise ScaleUpServerError(_concise_error(e, include_code=self._include_code)) from None
        return _SyncRespIterWrapper(resp_iter, self._include_code)

    def intercept_stream_stream(self, continuation, client_call_details, request_iterator):  # type: ignore[override]
        if inspect.iscoroutinefunction(continuation):
            return self._async_stream_stream(continuation, client_call_details, request_iterator)
        return self._sync_stream_stream(continuation, client_call_details, request_iterator)
