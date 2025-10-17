class CaptchaError(Exception):
    pass

class ValidationError(CaptchaError):
    pass

class ApiError(CaptchaError):
    pass

class TimeoutError(CaptchaError):
    pass
