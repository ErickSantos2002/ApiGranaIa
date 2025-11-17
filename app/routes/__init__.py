"""
Rotas da API
"""
from app.routes.usuarios import router as usuarios_router
from app.routes.gastos import router as gastos_router
from app.routes.receitas import router as receitas_router

__all__ = ["usuarios_router", "gastos_router", "receitas_router"]
