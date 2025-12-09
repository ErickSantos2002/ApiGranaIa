"""
Rotas da API
"""
from app.routes.usuarios import router as usuarios_router
from app.routes.gastos import router as gastos_router
from app.routes.receitas import router as receitas_router
from app.routes.gastos_futuros import router as gastos_futuros_router
from app.routes.cartoes_credito import router as cartoes_credito_router

__all__ = ["usuarios_router", "gastos_router", "receitas_router", "gastos_futuros_router", "cartoes_credito_router"]
