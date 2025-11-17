"""
Rotas para Autenticação (Registro e Login)
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas import (
    UsuarioRegister,
    UsuarioLogin,
    TokenResponse,
    UsuarioProfile,
    ResponseModel,
)
from app.schemas.usuario import UsuarioResponse
from app.models.usuario import Usuario
from app.utils.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/register",
    response_model=ResponseModel[UsuarioResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo usuário",
    description="Registra um novo usuário no sistema"
)
async def register(
    user_data: UsuarioRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Cadastra um novo usuário com os dados fornecidos.

    - **name**: Nome completo (obrigatório)
    - **email**: Email único (obrigatório)
    - **phone**: Telefone (obrigatório)
    - **senha**: Senha com mínimo 6 caracteres (obrigatório)

    O sistema automaticamente:
    - Gera o remotejid a partir do telefone
    - Faz hash seguro da senha
    - Valida se email e telefone já não existem
    """
    usuario = await AuthService.register(db, user_data)

    return ResponseModel(
        success=True,
        message="Usuário cadastrado com sucesso",
        data=UsuarioResponse(
            id=usuario.id,
            name=usuario.name,
            phone=usuario.phone,
            remotejid=usuario.remotejid,
            last_message=usuario.last_message,
            premium_until=usuario.premium_until,
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
            is_premium_active=usuario.is_premium_active
        )
    )


@router.post(
    "/login",
    response_model=ResponseModel[TokenResponse],
    summary="Fazer login",
    description="Autentica usuário e retorna token JWT"
)
async def login(
    login_data: UsuarioLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica um usuário e retorna token de acesso JWT.

    - **email**: Email do usuário (obrigatório)
    - **senha**: Senha do usuário (obrigatório)

    Retorna:
    - **access_token**: Token JWT para autenticação
    - **token_type**: Tipo do token (bearer)
    - **user_id**: ID do usuário
    - **email**: Email do usuário
    - **name**: Nome do usuário
    - **remotejid**: RemoteJID do usuário

    O token deve ser usado no header Authorization:
    ```
    Authorization: Bearer {access_token}
    ```
    """
    token_response = await AuthService.login(db, login_data)

    return ResponseModel(
        success=True,
        message="Login realizado com sucesso",
        data=token_response
    )


@router.get(
    "/me",
    response_model=ResponseModel[UsuarioProfile],
    summary="Obter perfil do usuário autenticado",
    description="Retorna informações do usuário logado"
)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna o perfil do usuário autenticado.

    **Requer autenticação via token JWT.**

    Retorna informações completas do usuário incluindo:
    - Dados pessoais
    - Status do premium
    - RemoteJID
    - Email

    O token JWT deve ser enviado no header Authorization:
    ```
    Authorization: Bearer {access_token}
    ```
    """
    return ResponseModel(
        success=True,
        message="Perfil do usuário obtido com sucesso",
        data=UsuarioProfile(
            id=str(current_user.id),
            name=current_user.name,
            email=current_user.email,
            phone=current_user.phone,
            remotejid=current_user.remotejid,
            premium_until=current_user.premium_until.isoformat() if current_user.premium_until else None,
            tipo_premium=current_user.tipo_premium,
            is_premium_active=current_user.is_premium_active
        )
    )
