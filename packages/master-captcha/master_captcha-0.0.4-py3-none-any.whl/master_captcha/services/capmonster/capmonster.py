# src/master_captcha/services/capmonster/anti_captcha.py
from __future__ import annotations
from typing import Any, Dict, Optional, Callable, Awaitable
from loguru import logger
import httpx

from ...base.request import AbstractCaptchaService, BaseRequestHTTPX
from ...dto.enum import CreateTaskResponseDTO, FinalStatus, StatusResponseDTO, CaptchaState, \
    SolveResultDTO
from ...dto.settings import ServiceSettings

class CapMonsterRequestHTTPX(BaseRequestHTTPX):

    async def _post_json(self, client: httpx.AsyncClient, url: str, payload: Dict[str, Any]) -> Any:
        headers = {"Connection": "close", "Accept-Encoding": "identity"}
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"http_status": r.status_code, "text": r.text}

    async def create_image_to_text(
        self,
        api_key: str,
        *,
        body_base64: str,
        capMonsterModule: Optional[str] = None,
        recognizingThreshold: Optional[int] = None,
        case: Optional[bool] = None,
        numeric: Optional[int] = None,
        math: Optional[bool] = None,
        **extra_params,
    ) -> Any:
        url = "/createTask"
        task: Dict[str, Any] = {"type": "ImageToTextTask", "body": body_base64}
        if capMonsterModule is not None:
            task["capMonsterModule"] = capMonsterModule
        if recognizingThreshold is not None:
            task["recognizingThreshold"] = recognizingThreshold
        if case is not None:
            task["case"] = bool(case)
        if numeric is not None:
            task["numeric"] = int(numeric)
        if math is not None:
            task["math"] = bool(math)
        task.update(extra_params or {})

        payload = {"clientKey": api_key, "task": task}

        async def do(client: httpx.AsyncClient):
            headers = {"Connection": "close", "Accept-Encoding": "identity"}
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            try:
                return r.json()
            except Exception:
                return {"http_status": r.status_code, "text": r.text}

        return await self._with_retries(lambda: self._with_client(do))

    async def create_recaptcha_v2(
            self,
            api_key: str,
            *,
            websiteURL: str,
            websiteKey: str,
            recaptchaDataSValue: Optional[str] = None,
            userAgent: Optional[str] = None,
            isInvisible: Optional[bool] = None,
            cookies: Optional[str] = None,
            proxy: Optional[Dict[str, Any]] = None,  # proxyType, proxyAddress, proxyPort, proxyLogin, proxyPassword
            **extra,
    ) -> Any:
        """
        type: RecaptchaV2Task
        Обязательные: websiteURL, websiteKey
        Необязательные: recaptchaDataSValue, userAgent, isInvisible, cookies, proxy*
        Результат: solution.gRecaptchaResponse (и иногда userAgent/cookies) :contentReference[oaicite:12]{index=12}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaV2Task",
            "websiteURL": websiteURL,
            "websiteKey": websiteKey,
        }
        if recaptchaDataSValue is not None:
            task["recaptchaDataSValue"] = recaptchaDataSValue
        if userAgent is not None:
            task["userAgent"] = userAgent
        if isInvisible is not None:
            task["isInvisible"] = bool(isInvisible)
        if cookies is not None:
            task["cookies"] = cookies
        if proxy:
            task.update(proxy)
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}

        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_recaptcha_v3(
            self,
            api_key: str,
            *,
            websiteURL: str,
            websiteKey: str,
            minScore: float,
            pageAction: str,
            userAgent: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        type: RecaptchaV3TaskProxyless (proxyless по докам)
        Обязательные: websiteURL, websiteKey, minScore, pageAction
        Необязательные: userAgent
        Результат: solution.gRecaptchaResponse (+возможен userAgent) :contentReference[oaicite:13]{index=13}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": websiteURL,
            "websiteKey": websiteKey,
            "minScore": float(minScore),
            "pageAction": pageAction,
        }
        if userAgent is not None:
            task["userAgent"] = userAgent
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_recaptcha_v2_enterprise(
            self,
            api_key: str,
            *,
            websiteURL: str,
            websiteKey: str,
            enterprisePayload: Optional[Dict[str, Any]] = None,
            userAgent: Optional[str] = None,
            cookies: Optional[str] = None,
            proxy: Optional[Dict[str, Any]] = None,
            **extra,
    ) -> Any:
        """
        type: RecaptchaV2EnterpriseTask
        Обязательные: websiteURL, websiteKey
        Необязательные: enterprisePayload, userAgent, cookies, proxy*
        Результат: solution.gRecaptchaResponse (+возможны userAgent/cookies) :contentReference[oaicite:14]{index=14}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaV2EnterpriseTask",
            "websiteURL": websiteURL,
            "websiteKey": websiteKey,
        }
        if enterprisePayload is not None:
            task["enterprisePayload"] = enterprisePayload
        if userAgent is not None:
            task["userAgent"] = userAgent
        if cookies is not None:
            task["cookies"] = cookies
        if proxy:
            task.update(proxy)
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_turnstile_token(
            self,
            api_key: str,
            *,
            websiteURL: str,
            websiteKey: str,
            userAgent: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        type: TurnstileTask (вариант токена)
        Обязательные: websiteURL, websiteKey
        Необязательные: userAgent
        Результат: solution.token (или структура) :contentReference[oaicite:15]{index=15}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "TurnstileTask",
            "websiteURL": websiteURL,
            "websiteKey": websiteKey,
        }
        if userAgent:
            task["userAgent"] = userAgent
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_geetest(
            self,
            api_key: str,
            *,
            websiteURL: str,
            gt: str,
            challenge: str,
            geetestApiServerSubdomain: Optional[str] = None,
            version: Optional[str] = None,  # "v3"|"v4" — если нужно
            **extra,
    ) -> Any:
        """
        type: GeeTestTask
        Обязательные: websiteURL, gt, challenge
        Необязательные: geetestApiServerSubdomain, version
        Результат: обычно токен/набор полей решения (верну целиком solution) :contentReference[oaicite:16]{index=16}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "GeeTestTask",
            "websiteURL": websiteURL,
            "gt": gt,
            "challenge": challenge,
        }
        if geetestApiServerSubdomain:
            task["geetestApiServerSubdomain"] = geetestApiServerSubdomain
        if version:
            task["version"] = version
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_funcaptcha(
            self,
            api_key: str,
            *,
            websiteURL: str,
            websitePublicKey: str,
            serviceUrl: Optional[str] = None,
            data: Optional[Dict[str, Any]] = None,  # blob/arkose init params, если есть
            userAgent: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        type: FunCaptchaTask (Arkose Labs)
        Обязательные: websiteURL, websitePublicKey (pk)
        Необязательные: serviceUrl, data, userAgent
        Результат: обычно solution.token (верну целиком solution)
        (официальная страница в каталоге — общий паттерн, см. список поддерживаемых типов) :contentReference[oaicite:17]{index=17}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "FunCaptchaTask",
            "websiteURL": websiteURL,
            "websitePublicKey": websitePublicKey,
        }
        if serviceUrl:
            task["serviceUrl"] = serviceUrl
        if data:
            task["data"] = data
        if userAgent:
            task["userAgent"] = userAgent
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_mtcaptcha(
            self,
            api_key: str,
            *,
            websiteURL: str,
            websiteKey: str,
            pageAction: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        type: MTCaptchaTask
        Обязательные: websiteURL, websiteKey
        Необязательные: pageAction
        Результат: solution.token (верну целиком solution) :contentReference[oaicite:18]{index=18}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "MTCaptchaTask",
            "websiteURL": websiteURL,
            "websiteKey": websiteKey,
        }
        if pageAction:
            task["pageAction"] = pageAction
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_recaptcha_click(
            self,
            api_key: str,
            *,
            websiteURL: str,
            websiteKey: str,
            **extra,
    ) -> Any:
        """
        type: ComplexImageTask (reCAPTCHA-click)
        Обязательные: websiteURL, websiteKey
        Результат: solution (контент кликов/сабмишна — верну целиком) :contentReference[oaicite:19]{index=19}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "RecaptchaComplexImageTask",
            "websiteURL": websiteURL,
            "websiteKey": websiteKey,
        }
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    async def create_datadome(
            self,
            api_key: str,
            *,
            websiteURL: str,
            datadomeCookie: Optional[str] = None,
            userAgent: Optional[str] = None,
            **extra,
    ) -> Any:
        """
        type: DataDomeTask (название в доках по Datadome)
        Обязательные: websiteURL
        Необязательные: datadomeCookie, userAgent
        Результат: solution (куки/токен для прохождения) — верну целиком solution. :contentReference[oaicite:20]{index=20}
        """
        url = "/createTask"
        task: Dict[str, Any] = {
            "type": "DataDomeTask",
            "websiteURL": websiteURL,
        }
        if datadomeCookie:
            task["datadomeCookie"] = datadomeCookie
        if userAgent:
            task["userAgent"] = userAgent
        task.update(extra or {})
        payload = {"clientKey": api_key, "task": task}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

    # ---- getTaskResult (общий) ----
    async def get_task_result(self, api_key: str, task_id: int | str) -> Any:
        url = "/getTaskResult"
        payload = {"clientKey": api_key, "taskId": int(task_id)}
        return await self._with_retries(lambda: self._with_client(lambda c: self._post_json(c, url, payload)))

 


# ---------- Service слой (с обёрткой и логами) ----------
class CapMonsterService(AbstractCaptchaService):
    """CapMonster: методы под разные типы капч (без дублирования)."""

    def __init__(self, *, base_url: str = "https://api.capmonster.cloud", settings: Optional[ServiceSettings] = None):
        super().__init__(settings or ServiceSettings())
        self.req = CapMonsterRequestHTTPX(base_url, self.settings)

    # общий валидатор create-ответа
    @staticmethod
    def _cm_validate_create(raw: Any) -> CreateTaskResponseDTO:
        if not isinstance(raw, dict):
            return CreateTaskResponseDTO(False, None, raw, ["bad create response format"])
        ok = (raw.get("errorId") == 0) and ("taskId" in raw)
        task_id = str(raw.get("taskId")) if raw.get("taskId") is not None else None
        errors: list[str] = []
        if not ok:
            err = raw.get("errorCode") or raw.get("errorDescription") or "create failed"
            errors.append(str(err))
        return CreateTaskResponseDTO(ok, task_id, raw, errors)

    # извлекаем «главное» значение из solution (если есть)
    @staticmethod
    def _extract_solution_value(sol: Any) -> Any:
        if isinstance(sol, dict):
            for k in ("gRecaptchaResponse", "token", "text", "captcha", "captchaKey", "value", "answer"):
                if k in sol:
                    return sol[k]
        return sol

    @staticmethod
    def _cm_validate_status(raw: Any) -> StatusResponseDTO:
        if not isinstance(raw, dict):
            return StatusResponseDTO(CaptchaState.FAILED, None, raw, ["bad status response format"])
        if raw.get("errorId") not in (None, 0):
            return StatusResponseDTO(CaptchaState.FAILED, None, raw, [str(raw.get("errorCode") or "failed")])

        status = str(raw.get("status", "")).lower()
        if status in ("processing", "queued", "inprocess", "inqueue", "idle"):
            return StatusResponseDTO(CaptchaState.PROCESSING, None, raw, [])
        if status == "ready":
            sol = raw.get("solution")
            return StatusResponseDTO(CaptchaState.READY, CapMonsterService._extract_solution_value(sol), raw, [])
        if status == "expired":
            return StatusResponseDTO(CaptchaState.EXPIRED, None, raw, [str(raw.get("errorCode") or "expired")])
        return StatusResponseDTO(CaptchaState.FAILED, None, raw, [str(raw.get("errorCode") or f"bad status: {status}")])

    # --------- ЕДИНАЯ ОБЁРТКА ----------
    async def _run_capmonster_flow(
        self,
        *,
        api_key: str,
        create_call: Callable[[], Awaitable[Any]],  # функция без аргументов, создаёт задачу и возвращает raw_create
    ) -> SolveResultDTO:
        """
        Единый сценарий:
        1) create
        2) validate create
        3) poll until done
        4) логирование результата
        """
        raw_create = await create_call()
        create_dto = self._cm_validate_create(raw_create)

        if not create_dto.ok or not create_dto.task_id:
            result = SolveResultDTO(
                status=FinalStatus.FAIL,
                task_id=create_dto.task_id,
                solution=None,
                attempts=0,
                response=raw_create,  # create-ответ, get_task ещё не вызывался
                errors=create_dto.errors or ["create failed"],
            )
            logger.warning("CapMonster create failed: {}", result.errors)
            return result

        task_id = create_dto.task_id

        async def get_status_call():
            raw_status = await self.req.get_task_result(api_key, task_id)
            return self._cm_validate_status(raw_status)

        result = await self._poll_until_done(get_status_call=get_status_call, task_id=str(task_id))

        if result.status == FinalStatus.SUCCESS:
            # solution превратим в строку и обрежем
            s = str(result.solution) if result.solution is not None else ""
            logger.info("Капча успешно решена (task_id={}): {}", task_id, s[:30])
        else:
            logger.error("Капча НЕ решена (task_id={}, status={}, errors={})", task_id, result.status, result.errors)

        return result

    # --------- ПУБЛИЧНЫЕ МЕТОДЫ (тонкие фасады) ----------

    async def image_to_text(
        self,
        *,
        api_key: str,
        body_base64: str,
        capMonsterModule: Optional[str] = None,
        recognizingThreshold: Optional[int] = None,  # 0..100
        case: Optional[bool] = None,
        numeric: Optional[int] = None,               # 0|1
        math: Optional[bool] = None,
        **extra_params,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_image_to_text(
                api_key,
                body_base64=body_base64,
                capMonsterModule=capMonsterModule,
                recognizingThreshold=recognizingThreshold,
                case=case,
                numeric=numeric,
                math=math,
                **extra_params,
            ),
        )

    async def recaptcha_v2(
        self,
        *,
        api_key: str,
        websiteURL: str,
        websiteKey: str,
        recaptchaDataSValue: Optional[str] = None,
        userAgent: Optional[str] = None,
        isInvisible: Optional[bool] = None,
        cookies: Optional[str] = None,
        proxy: Optional[Dict[str, Any]] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_recaptcha_v2(
                api_key,
                websiteURL=websiteURL,
                websiteKey=websiteKey,
                recaptchaDataSValue=recaptchaDataSValue,
                userAgent=userAgent,
                isInvisible=isInvisible,
                cookies=cookies,
                proxy=proxy,
                **extra,
            ),
        )

    async def recaptcha_v3(
        self,
        *,
        api_key: str,
        websiteURL: str,
        websiteKey: str,
        minScore: float,
        pageAction: str,
        userAgent: Optional[str] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_recaptcha_v3(
                api_key,
                websiteURL=websiteURL,
                websiteKey=websiteKey,
                minScore=minScore,
                pageAction=pageAction,
                userAgent=userAgent,
                **extra,
            ),
        )

    async def recaptcha_v2_enterprise(
        self,
        *,
        api_key: str,
        websiteURL: str,
        websiteKey: str,
        enterprisePayload: Optional[Dict[str, Any]] = None,
        userAgent: Optional[str] = None,
        cookies: Optional[str] = None,
        proxy: Optional[Dict[str, Any]] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_recaptcha_v2_enterprise(
                api_key,
                websiteURL=websiteURL,
                websiteKey=websiteKey,
                enterprisePayload=enterprisePayload,
                userAgent=userAgent,
                cookies=cookies,
                proxy=proxy,
                **extra,
            ),
        )

    async def turnstile_token(
        self,
        *,
        api_key: str,
        websiteURL: str,
        websiteKey: str,
        userAgent: Optional[str] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_turnstile_token(
                api_key,
                websiteURL=websiteURL,
                websiteKey=websiteKey,
                userAgent=userAgent,
                **extra,
            ),
        )

    async def geetest(
        self,
        *,
        api_key: str,
        websiteURL: str,
        gt: str,
        challenge: str,
        geetestApiServerSubdomain: Optional[str] = None,
        version: Optional[str] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_geetest(
                api_key,
                websiteURL=websiteURL,
                gt=gt,
                challenge=challenge,
                geetestApiServerSubdomain=geetestApiServerSubdomain,
                version=version,
                **extra,
            ),
        )

    async def funcaptcha(
        self,
        *,
        api_key: str,
        websiteURL: str,
        websitePublicKey: str,
        serviceUrl: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        userAgent: Optional[str] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_funcaptcha(
                api_key,
                websiteURL=websiteURL,
                websitePublicKey=websitePublicKey,
                serviceUrl=serviceUrl,
                data=data,
                userAgent=userAgent,
                **extra,
            ),
        )

    async def mtcaptcha(
        self,
        *,
        api_key: str,
        websiteURL: str,
        websiteKey: str,
        pageAction: Optional[str] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_mtcaptcha(
                api_key,
                websiteURL=websiteURL,
                websiteKey=websiteKey,
                pageAction=pageAction,
                **extra,
            ),
        )

    async def recaptcha_click(
        self,
        *,
        api_key: str,
        websiteURL: str,
        websiteKey: str,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_recaptcha_click(
                api_key,
                websiteURL=websiteURL,
                websiteKey=websiteKey,
                **extra,
            ),
        )

    async def datadome(
        self,
        *,
        api_key: str,
        websiteURL: str,
        datadomeCookie: Optional[str] = None,
        userAgent: Optional[str] = None,
        **extra,
    ) -> SolveResultDTO:
        return await self._run_capmonster_flow(
            api_key=api_key,
            create_call=lambda: self.req.create_datadome(
                api_key,
                websiteURL=websiteURL,
                datadomeCookie=datadomeCookie,
                userAgent=userAgent,
                **extra,
            ),
        )
