"""
Schemas Pydantic para validação de requests/responses
"""
from app.schemas.common import (
    ResponseModel,
    PaginatedResponse,
    PaginationParams,
    create_pagination_meta,
)
from app.schemas.usuario import (
    UsuarioBase,
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListResponse,
)
from app.schemas.gasto import (
    GastoBase,
    GastoCreate,
    GastoCreateRequest,
    GastoUpdate,
    GastoResponse,
    GastoListResponse,
    GastoDashboard,
)
from app.schemas.receita import (
    ReceitaBase,
    ReceitaCreate,
    ReceitaCreateRequest,
    ReceitaUpdate,
    ReceitaResponse,
    ReceitaListResponse,
    ReceitaDashboard,
)
from app.schemas.auth import (
    UsuarioRegister,
    UsuarioLogin,
    TokenResponse,
    UsuarioProfile,
    RequestPasswordReset,
    PasswordResetResponse,
    ResetPassword,
)
from app.schemas.gasto_futuro import (
    GastoFuturoBase,
    GastoFuturoCreate,
    GastoFuturoCreateRequest,
    GastoFuturoUpdate,
    GastoFuturoResponse,
    GastoFuturoDashboard,
    ParcelaBase,
    ParcelaCreate,
    ParcelaUpdate,
    ParcelaResponse,
    MarcarComoPagoRequest,
)
from app.schemas.cartao_credito import (
    CartaoCreditoBase,
    CartaoCreditoCreate,
    CartaoCreditoCreateRequest,
    CartaoCreditoUpdate,
    CartaoCreditoResponse,
    CartaoCreditoComGastos,
    FaturaMensal,
    PagarFaturaRequest,
)

__all__ = [
    # Common
    "ResponseModel",
    "PaginatedResponse",
    "PaginationParams",
    "create_pagination_meta",
    # Usuario
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioUpdate",
    "UsuarioResponse",
    "UsuarioListResponse",
    # Gasto
    "GastoBase",
    "GastoCreate",
    "GastoCreateRequest",
    "GastoUpdate",
    "GastoResponse",
    "GastoListResponse",
    "GastoDashboard",
    # Receita
    "ReceitaBase",
    "ReceitaCreate",
    "ReceitaCreateRequest",
    "ReceitaUpdate",
    "ReceitaResponse",
    "ReceitaListResponse",
    "ReceitaDashboard",
    # Auth
    "UsuarioRegister",
    "UsuarioLogin",
    "TokenResponse",
    "UsuarioProfile",
    "RequestPasswordReset",
    "PasswordResetResponse",
    "ResetPassword",
    # Gasto Futuro
    "GastoFuturoBase",
    "GastoFuturoCreate",
    "GastoFuturoCreateRequest",
    "GastoFuturoUpdate",
    "GastoFuturoResponse",
    "GastoFuturoDashboard",
    "ParcelaBase",
    "ParcelaCreate",
    "ParcelaUpdate",
    "ParcelaResponse",
    "MarcarComoPagoRequest",
    # Cartão de Crédito
    "CartaoCreditoBase",
    "CartaoCreditoCreate",
    "CartaoCreditoCreateRequest",
    "CartaoCreditoUpdate",
    "CartaoCreditoResponse",
    "CartaoCreditoComGastos",
    "FaturaMensal",
    "PagarFaturaRequest",
]
