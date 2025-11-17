"""
Exceções customizadas da aplicação
"""
from typing import Any, Optional


class BaseAPIException(Exception):
    """Exceção base para a API"""

    def __init__(
        self,
        message: str = "Erro na API",
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(BaseAPIException):
    """Exceção para recurso não encontrado (404)"""

    def __init__(self, message: str = "Recurso não encontrado", details: Optional[Any] = None):
        super().__init__(message=message, status_code=404, details=details)


class BadRequestException(BaseAPIException):
    """Exceção para requisição inválida (400)"""

    def __init__(self, message: str = "Requisição inválida", details: Optional[Any] = None):
        super().__init__(message=message, status_code=400, details=details)


class UnauthorizedException(BaseAPIException):
    """Exceção para não autorizado (401)"""

    def __init__(self, message: str = "Não autorizado", details: Optional[Any] = None):
        super().__init__(message=message, status_code=401, details=details)


class ForbiddenException(BaseAPIException):
    """Exceção para acesso proibido (403)"""

    def __init__(self, message: str = "Acesso proibido", details: Optional[Any] = None):
        super().__init__(message=message, status_code=403, details=details)


class ConflictException(BaseAPIException):
    """Exceção para conflito (409)"""

    def __init__(self, message: str = "Conflito de dados", details: Optional[Any] = None):
        super().__init__(message=message, status_code=409, details=details)


class ValidationException(BaseAPIException):
    """Exceção para erro de validação (422)"""

    def __init__(self, message: str = "Erro de validação", details: Optional[Any] = None):
        super().__init__(message=message, status_code=422, details=details)
