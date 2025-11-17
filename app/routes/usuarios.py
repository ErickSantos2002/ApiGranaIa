"""
Rotas para gerenciamento de Usuários
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import UsuarioService
from app.schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    ResponseModel,
    PaginatedResponse,
    PaginationParams,
    create_pagination_meta,
)
from app.schemas.usuario import (
    UsuarioUpdatePremium,
    UsuarioUpdateLastMessage,
)

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post(
    "",
    response_model=ResponseModel[UsuarioResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo usuário",
    description="Cria um novo usuário no sistema"
)
async def create_usuario(
    usuario_data: UsuarioCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo usuário com os dados fornecidos.

    - **name**: Nome do usuário (obrigatório)
    - **phone**: Telefone do usuário (opcional)
    - **remotejid**: Identificador único externo (obrigatório, único)
    - **last_message**: Última mensagem recebida (opcional)
    - **premium_until**: Data de expiração do premium (opcional)
    """
    usuario = await UsuarioService.create(db, usuario_data)

    return ResponseModel(
        success=True,
        message="Usuário criado com sucesso",
        data=UsuarioResponse.model_validate(usuario)
    )


@router.get(
    "",
    response_model=PaginatedResponse[UsuarioResponse],
    summary="Listar usuários",
    description="Lista todos os usuários com filtros e paginação"
)
async def list_usuarios(
    page: int = Query(default=1, ge=1, description="Número da página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    name: Optional[str] = Query(None, description="Filtrar por nome (busca parcial)"),
    phone: Optional[str] = Query(None, description="Filtrar por telefone (busca parcial)"),
    premium_active: Optional[bool] = Query(None, description="Filtrar por premium ativo"),
    premium_expired: Optional[bool] = Query(None, description="Filtrar por premium expirado"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista usuários com suporte a filtros e paginação.

    **Filtros disponíveis:**
    - **name**: Busca parcial no nome
    - **phone**: Busca parcial no telefone
    - **premium_active**: true para premium ativo, false para inativo
    - **premium_expired**: true para premium expirado
    """
    pagination = PaginationParams(page=page, page_size=page_size)

    usuarios, total = await UsuarioService.list_all(
        db=db,
        skip=pagination.offset,
        limit=pagination.limit,
        name=name,
        phone=phone,
        premium_active=premium_active,
        premium_expired=premium_expired,
    )

    usuarios_response = [UsuarioResponse.model_validate(u) for u in usuarios]
    meta = create_pagination_meta(page, page_size, total)

    return PaginatedResponse(
        success=True,
        message="Usuários listados com sucesso",
        data=usuarios_response,
        meta=meta
    )


@router.get(
    "/{usuario_id}",
    response_model=ResponseModel[UsuarioResponse],
    summary="Buscar usuário por ID",
    description="Retorna um usuário específico pelo ID"
)
async def get_usuario(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca um usuário específico pelo ID.
    """
    usuario = await UsuarioService.get_by_id(db, usuario_id)

    return ResponseModel(
        success=True,
        message="Usuário encontrado",
        data=UsuarioResponse.model_validate(usuario)
    )


@router.get(
    "/remotejid/{remotejid}",
    response_model=ResponseModel[UsuarioResponse],
    summary="Buscar usuário por remotejid",
    description="Retorna um usuário específico pelo remotejid"
)
async def get_usuario_by_remotejid(
    remotejid: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca um usuário específico pelo remotejid.
    """
    usuario = await UsuarioService.get_by_remotejid(db, remotejid)

    return ResponseModel(
        success=True,
        message="Usuário encontrado",
        data=UsuarioResponse.model_validate(usuario)
    )


@router.put(
    "/{usuario_id}",
    response_model=ResponseModel[UsuarioResponse],
    summary="Atualizar usuário",
    description="Atualiza os dados de um usuário"
)
async def update_usuario(
    usuario_id: UUID,
    usuario_data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza os dados de um usuário.

    Apenas os campos fornecidos serão atualizados.
    """
    usuario = await UsuarioService.update(db, usuario_id, usuario_data)

    return ResponseModel(
        success=True,
        message="Usuário atualizado com sucesso",
        data=UsuarioResponse.model_validate(usuario)
    )


@router.patch(
    "/{usuario_id}/premium",
    response_model=ResponseModel[UsuarioResponse],
    summary="Atualizar premium do usuário",
    description="Atualiza a data de expiração do premium"
)
async def update_usuario_premium(
    usuario_id: UUID,
    premium_data: UsuarioUpdatePremium,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza a data de expiração do premium de um usuário.
    """
    usuario = await UsuarioService.update_premium(db, usuario_id, premium_data)

    return ResponseModel(
        success=True,
        message="Premium atualizado com sucesso",
        data=UsuarioResponse.model_validate(usuario)
    )


@router.patch(
    "/{usuario_id}/last-message",
    response_model=ResponseModel[UsuarioResponse],
    summary="Atualizar última mensagem",
    description="Atualiza a última mensagem recebida do usuário"
)
async def update_usuario_last_message(
    usuario_id: UUID,
    message_data: UsuarioUpdateLastMessage,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza a última mensagem recebida do usuário.
    """
    usuario = await UsuarioService.update_last_message(db, usuario_id, message_data)

    return ResponseModel(
        success=True,
        message="Última mensagem atualizada com sucesso",
        data=UsuarioResponse.model_validate(usuario)
    )


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar usuário",
    description="Remove um usuário do sistema"
)
async def delete_usuario(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta um usuário do sistema.

    Esta ação também remove todos os gastos e receitas associados (cascade delete).
    """
    await UsuarioService.delete(db, usuario_id)
