# from __future__ import annotations
# from typing import Any, Dict, Optional, Callable
# import aiohttp
#
# from src.master_captcha.base.request import AbstractCaptchaService, BaseRequestHTTPX
# from src.master_captcha.dto.enum import SolveResultDTO, CreateTaskResponseDTO, FinalStatus
#
#
# class RuCaptchaRequest(BaseRequestHTTPX):
#     """
#     Низкоуровневые запросы: create/status под разные типы капч RuCaptcha.
#     Сессии создаются ВНУТРИ методов.
#     """
#
#     # --- image_to_text ---
#
#     async def create_image_to_text(self, api_key: str, *, body_base64: str, language: str | None = None, **params) -> Any:
#         url = f"{self.base_url}/create"
#         payload: Dict[str, Any] = {
#             "key": api_key,
#             "method": "post",   # пример: RuCaptcha принимает body/base64 (псевдо, подставишь реальное)
#             "body": body_base64,
#         }
#         if language:
#             payload["language"] = language
#         payload.update(params)
#
#         async def do(session: aiohttp.ClientSession):
#             async with session.post(
#                 url, json=payload, timeout=self.settings.request.request_timeout,
#                 proxy=self.settings.request.proxy, ssl=self.settings.request.verify_ssl
#             ) as resp:
#                 try:
#                     return await resp.json(content_type=None)
#                 except Exception:
#                     return {"http_status": resp.status, "text": await resp.text()}
#
#         return await self._with_retries(lambda: self._with_session(do))
#
#     async def get_task(self, api_key: str, task_id: str) -> Any:
#         url = f"{self.base_url}/status"
#         params = {"key": api_key, "id": task_id}
#
#         async def do(session: aiohttp.ClientSession):
#             async with session.get(
#                 url, params=params, timeout=self.settings.request.request_timeout,
#                 proxy=self.settings.request.proxy, ssl=self.settings.request.verify_ssl
#             ) as resp:
#                 try:
#                     return await resp.json(content_type=None)
#                 except Exception:
#                     return {"http_status": resp.status, "text": await resp.text()}
#
#         return await self._with_retries(lambda: self._with_session(do))
#
#
# class RuCaptchaService(AbstractCaptchaService):
#     provider = "rucaptcha"
#
#     def __init__(self, *, base_url: str = "https://api.rucaptcha.example", settings: Optional[ServiceSettings] = None):
#         super().__init__(settings)
#         self.req = RuCaptchaRequest(base_url, self.settings)
#
#     # ---------- Методы типа капчи ----------
#     async def image_to_text(
#         self,
#         *,
#         api_key: str,
#         body_base64: str,
#         language: str | None = None,
#         **extra_params
#     ) -> SolveResultDTO:
#         """
#         Пользователь передаёт только аргументы. Мы сами формируем правильный payload.
#         """
#         # 1) CREATE
#         raw_create = await self.req.create_image_to_text(api_key, body_base64=body_base64, language=language, **extra_params)
#         create_dto: CreateTaskResponseDTO = self._validate_create_raw(
#             raw_create,
#             task_id_key="task_id",  # подставишь реальные ключи сервиса
#             ok_key="status",
#             ok_value="OK",
#             error_key="error_code",
#         )
#         history = [raw_create]
#
#         if not create_dto.ok or not create_dto.task_id:
#             return SolveResultDTO(
#                 status=FinalStatus.FAIL,
#                 provider=self.provider,
#                 captcha_method="image_to_text",
#                 task_id=create_dto.task_id,
#                 solution=None,
#                 attempts=0,
#                 responses=history,
#                 errors=create_dto.errors or ["create failed"],
#             )
#
#         task_id = create_dto.task_id
#
#         # 2) POLL STATUS
#         async def get_status_call():
#             raw_status = await self.req.get_task(api_key, task_id)
#             return self._validate_status_raw(
#                 raw_status,
#                 status_key="status",
#                 ready_value="READY",
#                 processing_values=("QUEUED", "PROCESSING", "INQUEUE", "INPROCESS", "IDLE"),
#                 failed_values=("FAILED",),
#                 expired_values=("EXPIRED",),
#                 solution_key="solution",
#                 error_key="error_code",
#             )
#
#         result = await self._poll_until_done(
#             get_status_call=get_status_call,
#             captcha_method="image_to_text",
#             task_id=task_id,
#         )
#         result.responses = history + result.responses
#         return result
#
#     # Заглушки под будущие методы (реализуешь позже, сигнатуры такие же — только свои аргументы):
#     async def recaptcha_v2(self, *, api_key: str, site_key: str, page_url: str, **extra) -> SolveResultDTO:
#         raise NotImplementedError("recaptcha_v2: implement по аналогии с image_to_text")
#
#     async def recaptcha_enterprise(self, *, api_key: str, site_key: str, page_url: str, **extra) -> SolveResultDTO:
#         raise NotImplementedError("recaptcha_enterprise: implement по аналогии")
#
#     async def hcaptcha(self, *, api_key: str, site_key: str, page_url: str, **extra) -> SolveResultDTO:
#         raise NotImplementedError("hcaptcha: implement по аналогии")
