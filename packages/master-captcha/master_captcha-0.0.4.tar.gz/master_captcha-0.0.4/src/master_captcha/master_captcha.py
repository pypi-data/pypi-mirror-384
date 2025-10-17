from __future__ import annotations
from typing import Optional

from .dto.settings import ServiceSettings
from .services.capmonster.capmonster import CapMonsterService
from .services.anti_captcha.anti_captcha import AntiCaptchaService


class CaptchaManager:
    """
    Менеджер-«фасад»: доступ к конкретным сервисам как к свойствам.
    Пример: manager.ru_captcha.image_to_text(...)
    """
    def __init__(
        self,
        *,
        settings: Optional[ServiceSettings] = None,
        # можно прокинуть кастомные base_url при необходимости:
    ):
        self.settings = settings or ServiceSettings()

        # ИНИЦИАЛИЗИРУЕМ СЕРВИСЫ
        # self.ru_captcha = RuCaptchaService(settings=self.settings)
        self.capmonster = CapMonsterService(settings=self.settings)
        self.atni_captcha = AntiCaptchaService(settings=self.settings)

        # дальше добавишь:
        # self.cloud_captcha = CloudCaptchaService(base_url=..., settings=self.settings)
        # self.anti_captcha = AntiCaptchaService(base_url=..., settings=self.settings)
        # ...

    # Можно добавить удобные сеттеры для глобальных настроек:
    def set_polling(self, *, poll_interval: float | None = None, status_timeout: float | None = None):
        if poll_interval is not None:
            self.settings.polling.poll_interval = poll_interval
        if status_timeout is not None:
            self.settings.polling.status_timeout = status_timeout

    def set_retry(self, *, max_retries: int | None = None, retry_interval: float | None = None, backoff_factor: float | None = None):
        if max_retries is not None:
            self.settings.retry.max_retries = max_retries
        if retry_interval is not None:
            self.settings.retry.retry_interval = retry_interval
        if backoff_factor is not None:
            self.settings.retry.backoff_factor = backoff_factor

    def set_request(self, *, request_timeout: float | None = None, verify_ssl: bool | None = None, proxy: str | None = None):
        if request_timeout is not None:
            self.settings.request.request_timeout = request_timeout
        if verify_ssl is not None:
            self.settings.request.verify_ssl = verify_ssl
        if proxy is not None:
            self.settings.request.proxy = proxy
