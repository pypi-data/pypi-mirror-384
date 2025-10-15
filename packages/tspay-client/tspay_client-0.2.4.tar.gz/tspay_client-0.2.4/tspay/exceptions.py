class TsPayError(Exception):
    """TSPay xatolari uchun umumiy base exception"""

    def __init__(self, message: str, status_code: int = None, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def __str__(self):
        code = f" (status={self.status_code})" if self.status_code else ""
        return f"{self.message}{code}"


class AuthenticationError(TsPayError):
    """Noto‘g‘ri yoki faol bo‘lmagan access_token"""
    def __init__(self, message="Noto‘g‘ri yoki faol bo‘lmagan access_token", status_code=401, details=None):
        super().__init__(message, status_code, details)


class TransactionNotFound(TsPayError):
    """Berilgan cheque_id bilan tranzaksiya topilmadi"""
    def __init__(self, message="Berilgan cheque_id bilan tranzaksiya topilmadi", status_code=404, details=None):
        super().__init__(message, status_code, details)


class InvalidRequestError(TsPayError):
    """Yuborilgan so‘rov noto‘g‘ri (parametrlar xato, JSON error va hokazo)"""
    def __init__(self, message="So‘rov noto‘g‘ri", status_code=400, details=None):
        super().__init__(message, status_code, details)


class NetworkError(TsPayError):
    """Tarmoq bilan bog‘liq xato (timeout, DNS, internet yo‘q)"""
    def __init__(self, message="Tarmoq xatosi", status_code=None, details=None):
        super().__init__(message, status_code, details)


class ServerError(TsPayError):
    """TSPay serveridan 500+ javob qaytganda"""
    def __init__(self, message="Server xatosi", status_code=500, details=None):
        super().__init__(message, status_code, details)