"""
Arquivo principal da aplicação FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine, Base
from app.middleware import LoggingMiddleware
from app.utils.exceptions import BaseAPIException
from app.routes import usuarios_router, gastos_router, receitas_router, gastos_futuros_router
from app.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Executado na inicialização e no shutdown.
    """
    # Startup
    print("🚀 Iniciando aplicação...")
    print(f"📝 Nome: {settings.APP_NAME}")
    print(f"📌 Versão: {settings.APP_VERSION}")
    print(f"🔧 Debug: {settings.DEBUG}")
    print("CORS carregado:", settings.get_cors_origins())

    # Criar tabelas (apenas em desenvolvimento - use Alembic em produção)
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tabelas criadas/verificadas")

    yield

    # Shutdown
    print("🛑 Encerrando aplicação...")
    await engine.dispose()
    print("✅ Conexões com banco encerradas")


# Inicializar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    API completa para gerenciamento financeiro pessoal com controle de usuários, gastos e receitas.

    ## Funcionalidades

    ### 👥 Usuários
    * Criar, listar, atualizar e deletar usuários
    * Buscar por ID ou remotejid
    * Gerenciar premium
    * Filtrar por status de premium

    ### 💸 Gastos
    * Criar, listar, atualizar e deletar gastos
    * Filtrar por usuário, categoria, período e valor
    * Dashboard com estatísticas e agrupamento por categoria

    ### 💰 Receitas
    * Criar, listar, atualizar e deletar receitas
    * Filtrar por usuário, categoria, período e valor
    * Dashboard com estatísticas e agrupamento por categoria

    ### 💳 Gastos Futuros (Cartão de Crédito)
    * Criar, listar, atualizar e deletar gastos futuros
    * Gerenciar parcelas de compras parceladas
    * Marcar gastos/parcelas como pagos
    * Dashboard com próximos vencimentos e resumo
    * Filtrar por status, categoria, período

    ## Recursos

    * Paginação em todas as listagens
    * Filtros dinâmicos
    * Validações robustas
    * Respostas padronizadas
    * Documentação interativa (Swagger/ReDoc)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middleware de logging
app.add_middleware(LoggingMiddleware)


# Exception Handlers
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """Handler para exceções customizadas da API"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "details": exc.details,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validação do Pydantic"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Erro de validação",
            "details": errors,
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handler para erros do SQLAlchemy"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Erro no banco de dados",
            "details": str(exc) if settings.DEBUG else "Erro interno do servidor",
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais não tratadas"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Erro interno do servidor",
            "details": str(exc) if settings.DEBUG else None,
        }
    )


# Rotas
@app.get(
    "/",
    tags=["Health Check"],
    summary="Health Check",
    description="Verifica se a API está funcionando"
)
async def health_check():
    """Endpoint de health check"""
    return {
        "success": True,
        "message": "API está funcionando!",
        "data": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy"
        }
    }


@app.get(
    "/info",
    tags=["Health Check"],
    summary="Informações da API",
    description="Retorna informações sobre a API"
)
async def api_info():
    """Endpoint com informações da API"""
    return {
        "success": True,
        "message": "Informações da API",
        "data": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": "API de gerenciamento financeiro",
            "endpoints": {
                "auth": f"{settings.API_PREFIX}/auth",
                "usuarios": f"{settings.API_PREFIX}/usuarios",
                "gastos": f"{settings.API_PREFIX}/gastos",
                "receitas": f"{settings.API_PREFIX}/receitas",
                "gastos_futuros": f"{settings.API_PREFIX}/gastos-futuros",
            },
            "docs": "/docs",
            "redoc": "/redoc",
        }
    }


# Incluir rotas com prefixo
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(usuarios_router, prefix=settings.API_PREFIX)
app.include_router(gastos_router, prefix=settings.API_PREFIX)
app.include_router(receitas_router, prefix=settings.API_PREFIX)
app.include_router(gastos_futuros_router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
