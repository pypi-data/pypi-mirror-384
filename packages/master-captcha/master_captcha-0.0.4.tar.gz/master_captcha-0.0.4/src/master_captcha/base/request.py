from __future__ import annotations
import asyncio
import random
import ssl
from typing import Any, Optional, Tuple, Callable, Type, Dict
import aiohttp
import httpx
from aiohttp import ClientConnectorError, ServerDisconnectedError, ClientOSError, ClientPayloadError, ContentTypeError
from ..dto.enum import SolveResultDTO, StatusResponseDTO, FinalStatus, CaptchaState, \
    CreateTaskResponseDTO
from ..dto.settings import ServiceSettings
# небольшая алиас-функция для таймаута
def _build_timeout(request_timeout: float) -> httpx.Timeout:
    return httpx.Timeout(timeout=request_timeout, connect=request_timeout, read=request_timeout)

class BaseRequestHTTPX:
    def __init__(self, base_url: str, settings: ServiceSettings):
        self.base_url = base_url.rstrip("/")
        self.settings = settings

    def _verify_arg(self) -> Optional[str | bool]:
        if getattr(self.settings.request, "verify_ssl", True) is False:
            return False
        ca_file = getattr(self.settings.request, "ca_file", None)
        if ca_file:
            return ca_file
        return True

    def _proxies_arg(self) -> Optional[str | Dict[str, str]]:
        p = getattr(self.settings.request, "proxy", None)
        if not p:
            return None
        # Если пользователь передал строку — возвращаем её (httpx принимает строку — shorthand)
        if isinstance(p, str):
            return p
        # Если он передал dict-like с http/https — оставляем как есть (проверим тип)
        if isinstance(p, dict):
            # допустимые ключи: "http", "https"
            # приводим значения к строкам на всякий случай
            out = {}
            for k, v in p.items():
                if k.lower() in ("http", "https"):
                    out[k.lower()] = str(v)
            if out:
                return out
            # если dict есть, но не содержит http/https — попробуем взять поле "all"
            if "all" in p:
                return str(p["all"])
            # иначе — None
            return None
        # иначе — неизвестный тип
        return None


    async def _with_client(self, fn: Callable[[httpx.AsyncClient], Any]) -> Any:
        verify = self._verify_arg()
        proxies = self._proxies_arg()
        timeout = _build_timeout(self.settings.request.request_timeout)

        # httpx.AsyncClient принимает `proxies`:
        # - None
        # - строку (shorthand) - применится ко всем схемам
        # - dict {"http": "...", "https": "..."}
        async with httpx.AsyncClient(
                base_url=self.base_url,
                verify=verify,
                proxy=proxies,
                timeout=timeout,
                http2=False,
        ) as client:
            return await fn(client)

    async def _with_retries(self, coro_factory: Callable[[], Any]) -> Any:
        rset = self.settings.retry
        attempt = 0
        delay = rset.retry_interval

        retryable = (
            httpx.ReadError,
            httpx.NetworkError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.ProtocolError,
        )

        while True:
            try:
                return await coro_factory()
            except retryable as e:
                attempt += 1
                if attempt > rset.max_retries:
                    # пробросим оригинальную ошибку
                    raise
                await asyncio.sleep(delay * (1.0 + random.random() * 0.3))
                delay *= max(1.0, rset.backoff_factor)


class AbstractCaptchaService:
    """
    Базовый сервис: хранит настройки, общую логику poll'инга и хелперы валидации.
    Конкретный провайдер реализует методы под типы капч + методы запросов/валидаторов.
    """
    provider: str = "abstract"

    def __init__(self, settings: Optional[ServiceSettings] = None):
        self.settings = settings or ServiceSettings()

    # -------- Общая логика опроса статуса --------
    async def _poll_until_done(
        self,
        *,
        get_status_call: Callable[[], StatusResponseDTO],  # без аргументов, возвращает StatusResponseDTO
        task_id: str,
    ) -> SolveResultDTO:
        last_raw: Any = None
        last_errors: list[str] = []
        attempts = 0

        deadline = asyncio.get_event_loop().time() + self.settings.polling.status_timeout

        while True:
            attempts += 1
            status_dto: StatusResponseDTO = await get_status_call()
            last_raw = status_dto.raw_response
            last_errors = status_dto.errors or []

            if status_dto.done:
                if status_dto.state == CaptchaState.READY:
                    return SolveResultDTO(
                        status=FinalStatus.SUCCESS,
                        task_id=task_id,
                        solution=status_dto.solution,
                        attempts=attempts,
                        response=last_raw,     # ← только последний ответ get_task
                        errors=last_errors,
                    )
                final = FinalStatus.FAIL if status_dto.state == CaptchaState.FAILED else FinalStatus.TIMEOUT
                return SolveResultDTO(
                    status=final,
                    task_id=task_id,
                    solution=None,
                    attempts=attempts,
                    response=last_raw,
                    errors=last_errors,
                )

            if asyncio.get_event_loop().time() >= deadline:
                return SolveResultDTO(
                    status=FinalStatus.TIMEOUT,
                    task_id=task_id,
                    solution=None,
                    attempts=attempts,
                    response=last_raw,
                    errors=last_errors + ["status polling timeout reached"],
                )

            await asyncio.sleep(self.settings.polling.poll_interval)

    # -------- Валидационные хелперы (по желанию можно переопределять) --------
    @staticmethod
    def _validate_create_raw(
        raw: Any,
        task_id_key: str = "task_id",
        ok_key: str | None = "status",
        ok_value: str = "OK",
        error_key: str = "error_code",
    ) -> CreateTaskResponseDTO:
        if not isinstance(raw, dict):
            return CreateTaskResponseDTO(False, None, raw, ["bad create response format"])
        ok = True
        if ok_key is not None:
            ok = str(raw.get(ok_key, "")).upper() == ok_value
        task_id = str(raw[task_id_key]) if raw.get(task_id_key) else None
        errors: list[str] = []
        if not ok or not task_id:
            errors.append(str(raw.get(error_key) or "create failed"))
        return CreateTaskResponseDTO(ok, task_id, raw, errors)

    @staticmethod
    def _validate_status_raw(
        raw: Any,
        status_key: str = "status",
        ready_value: str = "READY",
        processing_values: tuple[str, ...] = ("QUEUED", "PROCESSING", "INQUEUE", "INPROCESS", "IDLE"),
        failed_values: tuple[str, ...] = ("FAILED",),
        expired_values: tuple[str, ...] = ("EXPIRED",),
        solution_key: str = "solution",
        error_key: str = "error_code",
    ) -> StatusResponseDTO:
        if not isinstance(raw, dict):
            return StatusResponseDTO(CaptchaState.FAILED, None, raw, ["bad status response format"])
        status = str(raw.get(status_key, "")).upper()
        if status in processing_values:
            return StatusResponseDTO(CaptchaState.PROCESSING, None, raw, [])
        if status == ready_value:
            return StatusResponseDTO(CaptchaState.READY, raw.get(solution_key), raw, [])
        if status in expired_values:
            return StatusResponseDTO(CaptchaState.EXPIRED, None, raw, [str(raw.get(error_key) or "expired")])
        # всё остальное считаем FAIL
        return StatusResponseDTO(CaptchaState.FAILED, None, raw, [str(raw.get(error_key) or "failed")])
