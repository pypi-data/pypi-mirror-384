from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class PollingSettings:
    poll_interval: float = 2.0      # сек между запросами статуса
    status_timeout: float = 120.0   # общий таймаут ожидания решения

@dataclass
class RetrySettings:
    max_retries: int = 2            # ретраи при сетевых/транзитных ошибках
    retry_interval: float = 1.0     # пауза между ретраями
    backoff_factor: float = 2.0     # множитель задержки между ретраями

@dataclass
class RequestSettings:
    request_timeout: float = 30.0   # таймаут каждого HTTP-запроса
    verify_ssl: bool = True
    proxy: str | None = None

@dataclass
class ServiceSettings:
    # ВАЖНО: используем default_factory вместо прямого вызова конструктора
    polling: PollingSettings = field(default_factory=PollingSettings)
    retry: RetrySettings = field(default_factory=RetrySettings)
    request: RequestSettings = field(default_factory=RequestSettings)
