# src/master_captcha/services/anticaptcha/anti_captcha.py
from __future__ import annotations
from typing import Any, Dict, Optional, Callable, Awaitable
from loguru import logger
import httpx

from ...base.request import AbstractCaptchaService, BaseRequestHTTPX
from ...dto.enum import CreateTaskResponseDTO, FinalStatus, StatusResponseDTO, CaptchaState, \
    SolveResultDTO
from ...dto.settings import ServiceSettings


class AntiCaptchaRequest(BaseRequestHTTPX):
    """HTTP-клиент для Anti-Captcha API"""

    async def _post_json(self, client: httpx.AsyncClient, url: str, payload: Dict[str, Any]) -> Any:
        """Общий метод для POST-запросов с JSON"""
        headers = {"Content-Type": "application/json"}
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"http_status": r.status_code, "text": r.text}

    # ==================== IMAGE TO TEXT ====================
    async def create_image_to_text(
            self,
            client_key: str,
            *,
            body_base64: str,
            phrase: Optional[bool] = None,  # капча содержит 2-3 слова
            case: Optional[bool] = None,  # регистрозависимая
            numeric: Optional[int] = None,  # 0=без ограничений, 1=только цифры, 2=без цифр
            math: Optional[bool] = None,  # математическая операция
            min_length: Optional[int] = None,  # минимальная длина ответа
            max_length: Optional[int] = None,  # максимальная длина ответа
            comment: Optional[str] = None,  # комментарий для работника
            **extra_params,
    ) -> Any:
        """
        Создание задачи ImageToTextTask
        Документация: https://anti-captcha.com/apidoc/task-types/ImageToTextTask
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "ImageToTextTask",
            "body": body_base64
        }

        if phrase is not None:
            task["phrase"] = bool(phrase)
        if case is not None:
            task["case"] = bool(case)
        if numeric is not None:
            task["numeric"] = int(numeric)
        if math is not None:
            task["math"] = bool(math)
        if min_length is not None:
            task["minLength"] = int(min_length)
        if max_length is not None:
            task["maxLength"] = int(max_length)
        if comment is not None:
            task["comment"] = str(comment)

        task.update(extra_params or {})

        payload = {"clientKey": client_key, "task": task}

        async def do(client: httpx.AsyncClient):
            return await self._post_json(client, url, payload)

        return await self._with_retries(lambda: self._with_client(do))

    # ==================== RECAPTCHA V2 ====================
    async def create_recaptcha_v2_proxyless(
            self,
            client_key: str,
            *,
            website_url: str,
            website_key: str,
            recaptcha_data_s_value: Optional[str] = None,
            is_invisible: Optional[bool] = None,
            **extra,
    ) -> Any:
        """
        Создание задачи RecaptchaV2TaskProxyless
        Документация: https://anti-captcha.com/apidoc/task-types/RecaptchaV2TaskProxyless
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": website_url,
            "websiteKey": website_key,
        }

        if recaptcha_data_s_value is not None:
            task["recaptchaDataSValue"] = recaptcha_data_s_value
        if is_invisible is not None:
            task["isInvisible"] = bool(is_invisible)

        task.update(extra or {})
        payload = {"clientKey": client_key, "task": task}

        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_recaptcha_v2(
            self,
            client_key: str,
            *,
            website_url: str,
            website_key: str,
            recaptcha_data_s_value: Optional[str] = None,
            is_invisible: Optional[bool] = None,
            proxy_type: Optional[str] = None,  # http, socks4, socks5
            proxy_address: Optional[str] = None,
            proxy_port: Optional[int] = None,
            proxy_login: Optional[str] = None,
            proxy_password: Optional[str] = None,
            user_agent: Optional[str] = None,
            cookies: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        Создание задачи RecaptchaV2Task (с прокси)
        Документация: https://anti-captcha.com/apidoc/task-types/RecaptchaV2Task
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaV2Task",
            "websiteURL": website_url,
            "websiteKey": website_key,
        }

        if recaptcha_data_s_value is not None:
            task["recaptchaDataSValue"] = recaptcha_data_s_value
        if is_invisible is not None:
            task["isInvisible"] = bool(is_invisible)
        if proxy_type is not None:
            task["proxyType"] = proxy_type
        if proxy_address is not None:
            task["proxyAddress"] = proxy_address
        if proxy_port is not None:
            task["proxyPort"] = int(proxy_port)
        if proxy_login is not None:
            task["proxyLogin"] = proxy_login
        if proxy_password is not None:
            task["proxyPassword"] = proxy_password
        if user_agent is not None:
            task["userAgent"] = user_agent
        if cookies is not None:
            task["cookies"] = cookies

        task.update(extra or {})
        payload = {"clientKey": client_key, "task": task}

        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    # ==================== RECAPTCHA V3 ====================
    async def create_recaptcha_v3_proxyless(
            self,
            client_key: str,
            *,
            website_url: str,
            website_key: str,
            page_action: str,
            min_score: Optional[float] = None,  # 0.3, 0.5, 0.7, 0.9
            **extra,
    ) -> Any:
        """
        Создание задачи RecaptchaV3TaskProxyless
        Документация: https://anti-captcha.com/apidoc/task-types/RecaptchaV3TaskProxyless
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": website_url,
            "websiteKey": website_key,
            "pageAction": page_action,
        }

        if min_score is not None:
            task["minScore"] = float(min_score)

        task.update(extra or {})
        payload = {"clientKey": client_key, "task": task}

        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    # ==================== RECAPTCHA V2 ENTERPRISE ====================
    async def create_recaptcha_v2_enterprise_proxyless(
            self,
            client_key: str,
            *,
            website_url: str,
            website_key: str,
            enterprise_payload: Optional[Dict[str, Any]] = None,
            is_invisible: Optional[bool] = None,
            api_domain: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        Создание задачи RecaptchaV2EnterpriseTaskProxyless
        Документация: https://anti-captcha.com/apidoc/task-types/RecaptchaV2EnterpriseTaskProxyless
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaV2EnterpriseTaskProxyless",
            "websiteURL": website_url,
            "websiteKey": website_key,
        }

        if enterprise_payload is not None:
            task["enterprisePayload"] = enterprise_payload
        if is_invisible is not None:
            task["isInvisible"] = bool(is_invisible)
        if api_domain is not None:
            task["apiDomain"] = api_domain

        task.update(extra or {})
        payload = {"clientKey": client_key, "task": task}

        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    # ==================== TURNSTILE ====================
    async def create_turnstile_proxyless(
            self,
            client_key: str,
            *,
            website_url: str,
            website_key: str,
            action: Optional[str] = None,
            cdata: Optional[str] = None,
            chlpagedata: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        Создание задачи TurnstileTaskProxyless
        Документация: https://anti-captcha.com/apidoc/task-types/TurnstileTaskProxyless
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "TurnstileTaskProxyless",
            "websiteURL": website_url,
            "websiteKey": website_key,
        }

        if action is not None:
            task["action"] = action
        if cdata is not None:
            task["cData"] = cdata
        if chlpagedata is not None:
            task["chlPageData"] = chlpagedata

        task.update(extra or {})
        payload = {"clientKey": client_key, "task": task}

        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_turnstile(
            self,
            client_key: str,
            *,
            website_url: str,
            website_key: str,
            action: Optional[str] = None,
            cdata: Optional[str] = None,
            chlpagedata: Optional[str] = None,
            proxy_type: Optional[str] = None,
            proxy_address: Optional[str] = None,
            proxy_port: Optional[int] = None,
            proxy_login: Optional[str] = None,
            proxy_password: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        Создание задачи TurnstileTask (с прокси)
        Документация: https://anti-captcha.com/apidoc/task-types/TurnstileTask
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "TurnstileTask",
            "websiteURL": website_url,
            "websiteKey": website_key,
        }

        if action is not None:
            task["action"] = action
        if cdata is not None:
            task["cData"] = cdata
        if chlpagedata is not None:
            task["chlPageData"] = chlpagedata
        if proxy_type is not None:
            task["proxyType"] = proxy_type
        if proxy_address is not None:
            task["proxyAddress"] = proxy_address
        if proxy_port is not None:
            task["proxyPort"] = int(proxy_port)
        if proxy_login is not None:
            task["proxyLogin"] = proxy_login
        if proxy_password is not None:
            task["proxyPassword"] = proxy_password

        task.update(extra or {})
        payload = {"clientKey": client_key, "task": task}

        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    # ==================== GET TASK RESULT ====================
    async def get_task_result(self, client_key: str, task_id: int | str) -> Any:
        """
        Получение результата задачи
        Документация: https://anti-captcha.com/apidoc/methods/getTaskResult
        """
        url = "/getTaskResult"
        payload = {"clientKey": client_key, "taskId": int(task_id)}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    # ==================== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ====================
    async def get_balance(self, client_key: str) -> Any:
        """Получить баланс аккаунта"""
        url = "/getBalance"
        payload = {"clientKey": client_key}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))


# ==================== SERVICE СЛОЙ ====================
class AntiCaptchaService(AbstractCaptchaService):
    """Anti-Captcha сервис с поддержкой всех основных типов капч"""

    def __init__(self, *, base_url: str = "http://65.108.2.48:80", settings: Optional[ServiceSettings] = None):
        super().__init__(settings or ServiceSettings())
        self.req = AntiCaptchaRequest(base_url, self.settings)

    # ==================== ВАЛИДАТОРЫ ====================
    @staticmethod
    def _ac_validate_create(raw: Any) -> CreateTaskResponseDTO:
        """
        Валидатор для createTask
        Формат ответа: {"errorId": 0, "taskId": 123456}
        При ошибке: {"errorId": 1, "errorCode": "ERROR_KEY_DOES_NOT_EXIST"}
        """
        if not isinstance(raw, dict):
            return CreateTaskResponseDTO(False, None, raw, ["bad create response format"])

        error_id = raw.get("errorId", 0)
        ok = (error_id == 0) and ("taskId" in raw)
        task_id = str(raw.get("taskId")) if raw.get("taskId") is not None else None

        errors: list[str] = []
        if not ok:
            err = raw.get("errorCode") or raw.get("errorDescription") or "create failed"
            errors.append(str(err))

        return CreateTaskResponseDTO(ok, task_id, raw, errors)

    @staticmethod
    def _extract_solution_value(sol: Any) -> Any:
        """
        Извлекаем главное значение из solution
        - для ImageToTextTask: solution.text
        - для RecaptchaV2: solution.gRecaptchaResponse
        - для Turnstile: solution.token
        """
        if isinstance(sol, dict):
            # Порядок важен: более специфичные ключи сначала
            for k in ("text", "gRecaptchaResponse", "token", "captcha", "answer", "value"):
                if k in sol:
                    return sol[k]
        return sol

    @staticmethod
    def _ac_validate_status(raw: Any) -> StatusResponseDTO:
        """
        Валидатор для getTaskResult
        Формат ответа:
        - processing: {"errorId": 0, "status": "processing"}
        - ready: {"errorId": 0, "status": "ready", "solution": {...}}
        - ошибка: {"errorId": 1, "errorCode": "ERROR_CAPTCHA_UNSOLVABLE"}
        """
        if not isinstance(raw, dict):
            return StatusResponseDTO(CaptchaState.FAILED, None, raw, ["bad status response format"])

        error_id = raw.get("errorId", 0)

        # Если errorId != 0, то это ошибка
        if error_id != 0:
            err_code = raw.get("errorCode", "unknown error")
            # ERROR_CAPTCHA_UNSOLVABLE - капча не решена
            if "UNSOLVABLE" in str(err_code).upper():
                return StatusResponseDTO(CaptchaState.FAILED, None, raw, [str(err_code)])
            return StatusResponseDTO(CaptchaState.FAILED, None, raw, [str(err_code)])

        status = str(raw.get("status", "")).lower()

        if status == "processing":
            return StatusResponseDTO(CaptchaState.PROCESSING, None, raw, [])

        if status == "ready":
            sol = raw.get("solution")
            return StatusResponseDTO(
                CaptchaState.READY,
                AntiCaptchaService._extract_solution_value(sol),
                raw,
                []
            )

        # Неизвестный статус
        return StatusResponseDTO(
            CaptchaState.FAILED,
            None,
            raw,
            [f"unknown status: {status}"]
        )

    # ==================== ЕДИНАЯ ОБЕРТКА ====================
    async def _run_anticaptcha_flow(
            self,
            *,
            client_key: str,
            create_call: Callable[[], Awaitable[Any]],
    ) -> SolveResultDTO:
        """
        Единый сценарий:
        1) createTask
        2) validate create
        3) poll until done
        4) логирование
        """
        raw_create = await create_call()
        create_dto = self._ac_validate_create(raw_create)

        if not create_dto.ok or not create_dto.task_id:
            result = SolveResultDTO(
                status=FinalStatus.FAIL,
                task_id=create_dto.task_id,
                solution=None,
                attempts=0,
                response=raw_create,
                errors=create_dto.errors or ["create failed"],
            )
            logger.warning("Anti-Captcha create failed: {}", result.errors)
            return result

        task_id = create_dto.task_id

        async def get_status_call():
            raw_status = await self.req.get_task_result(client_key, task_id)
            return self._ac_validate_status(raw_status)

        result = await self._poll_until_done(get_status_call=get_status_call, task_id=str(task_id))

        if result.status == FinalStatus.SUCCESS:
            s = str(result.solution) if result.solution is not None else ""
            logger.info("Капча успешно решена (task_id={}): {}", task_id, s[:50])
        else:
            logger.error("Капча НЕ решена (task_id={}, status={}, errors={})", task_id, result.status, result.errors)

        return result

    # ==================== ПУБЛИЧНЫЕ МЕТОДЫ ====================

    async def image_to_text(
            self,
            *,
            client_key: str,
            body_base64: str,
            phrase: Optional[bool] = None,
            case: Optional[bool] = None,
            numeric: Optional[int] = None,
            math: Optional[bool] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            comment: Optional[str] = None,
            **extra_params,
    ) -> SolveResultDTO:
        """
        Решение обычной капчи-картинки
        Результат в solution будет текст капчи
        """
        return await self._run_anticaptcha_flow(
            client_key=client_key,
            create_call=lambda: self.req.create_image_to_text(
                client_key,
                body_base64=body_base64,
                phrase=phrase,
                case=case,
                numeric=numeric,
                math=math,
                min_length=min_length,
                max_length=max_length,
                comment=comment,
                **extra_params,
            ),
        )

    async def recaptcha_v2_proxyless(
            self,
            *,
            client_key: str,
            website_url: str,
            website_key: str,
            recaptcha_data_s_value: Optional[str] = None,
            is_invisible: Optional[bool] = None,
            **extra,
    ) -> SolveResultDTO:
        """
        Решение reCAPTCHA V2 без прокси
        Результат в solution будет gRecaptchaResponse токен
        """
        return await self._run_anticaptcha_flow(
            client_key=client_key,
            create_call=lambda: self.req.create_recaptcha_v2_proxyless(
                client_key,
                website_url=website_url,
                website_key=website_key,
                recaptcha_data_s_value=recaptcha_data_s_value,
                is_invisible=is_invisible,
                **extra,
            ),
        )

    async def recaptcha_v2(
            self,
            *,
            client_key: str,
            website_url: str,
            website_key: str,
            recaptcha_data_s_value: Optional[str] = None,
            is_invisible: Optional[bool] = None,
            proxy_type: Optional[str] = None,
            proxy_address: Optional[str] = None,
            proxy_port: Optional[int] = None,
            proxy_login: Optional[str] = None,
            proxy_password: Optional[str] = None,
            user_agent: Optional[str] = None,
            cookies: Optional[str] = None,
            **extra,
    ) -> SolveResultDTO:
        """
        Решение reCAPTCHA V2 через прокси
        Результат в solution будет gRecaptchaResponse токен
        """
        return await self._run_anticaptcha_flow(
            client_key=client_key,
            create_call=lambda: self.req.create_recaptcha_v2(
                client_key,
                website_url=website_url,
                website_key=website_key,
                recaptcha_data_s_value=recaptcha_data_s_value,
                is_invisible=is_invisible,
                proxy_type=proxy_type,
                proxy_address=proxy_address,
                proxy_port=proxy_port,
                proxy_login=proxy_login,
                proxy_password=proxy_password,
                user_agent=user_agent,
                cookies=cookies,
                **extra,
            ),
        )

    async def recaptcha_v3_proxyless(
            self,
            *,
            client_key: str,
            website_url: str,
            website_key: str,
            page_action: str,
            min_score: Optional[float] = None,
            **extra,
    ) -> SolveResultDTO:
        """
        Решение reCAPTCHA V3 без прокси
        Результат в solution будет gRecaptchaResponse токен
        """
        return await self._run_anticaptcha_flow(
            client_key=client_key,
            create_call=lambda: self.req.create_recaptcha_v3_proxyless(
                client_key,
                website_url=website_url,
                website_key=website_key,
                page_action=page_action,
                min_score=min_score,
                **extra,
            ),
        )

    async def recaptcha_v2_enterprise_proxyless(
            self,
            *,
            client_key: str,
            website_url: str,
            website_key: str,
            enterprise_payload: Optional[Dict[str, Any]] = None,
            is_invisible: Optional[bool] = None,
            api_domain: Optional[str] = None,
            **extra,
    ) -> SolveResultDTO:
        """
        Решение reCAPTCHA V2 Enterprise без прокси
        Результат в solution будет gRecaptchaResponse токен
        """
        return await self._run_anticaptcha_flow(
            client_key=client_key,
            create_call=lambda: self.req.create_recaptcha_v2_enterprise_proxyless(
                client_key,
                website_url=website_url,
                website_key=website_key,
                enterprise_payload=enterprise_payload,
                is_invisible=is_invisible,
                api_domain=api_domain,
                **extra,
            ),
        )

    async def turnstile_proxyless(
            self,
            *,
            client_key: str,
            website_url: str,
            website_key: str,
            action: Optional[str] = None,
            cdata: Optional[str] = None,
            chlpagedata: Optional[str] = None,
            **extra,
    ) -> SolveResultDTO:
        """
        Решение Cloudflare Turnstile без прокси
        Результат в solution будет token
        """
        return await self._run_anticaptcha_flow(
            client_key=client_key,
            create_call=lambda: self.req.create_turnstile_proxyless(
                client_key,
                website_url=website_url,
                website_key=website_key,
                action=action,
                cdata=cdata,
                chlpagedata=chlpagedata,
                **extra,
            ),
        )

    async def turnstile(
            self,
            *,
            client_key: str,
            website_url: str,
            website_key: str,
            action: Optional[str] = None,
            cdata: Optional[str] = None,
            chlpagedata: Optional[str] = None,
            proxy_type: Optional[str] = None,
            proxy_address: Optional[str] = None,
            proxy_port: Optional[int] = None,
            proxy_login: Optional[str] = None,
            proxy_password: Optional[str] = None,
            **extra,
    ) -> SolveResultDTO:
        """
        Решение Cloudflare Turnstile через прокси
        Результат в solution будет token
        """
        return await self._run_anticaptcha_flow(
            client_key=client_key,
            create_call=lambda: self.req.create_turnstile(
                client_key,
                website_url=website_url,
                website_key=website_key,
                action=action,
                cdata=cdata,
                chlpagedata=chlpagedata,
                proxy_type=proxy_type,
                proxy_address=proxy_address,
                proxy_port=proxy_port,
                proxy_login=proxy_login,
                proxy_password=proxy_password,
                **extra,
            ),
        )

    async def get_balance(self, client_key: str) -> float:
        """
        Получить баланс аккаунта
        Возвращает число (float) или 0 при ошибке
        """
        try:
            raw = await self.req.get_balance(client_key)
            if isinstance(raw, dict) and raw.get("errorId") == 0:
                return float(raw.get("balance", 0))
            return 0.0
        except Exception as e:
            logger.error("Failed to get balance: {}", e)
            return 0.0