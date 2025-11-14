"""
Service para lógica de negócios de Usuários
"""
from typing import Optional, List, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Usuario
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioUpdatePremium,
    UsuarioUpdateLastMessage,
)
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException


class UsuarioService:
    """Service para gerenciar usuários"""

    @staticmethod
    async def create(db: AsyncSession, usuario_data: UsuarioCreate) -> Usuario:
        """
        Cria um novo usuário

        Args:
            db: Sessão do banco de dados
            usuario_data: Dados do usuário a ser criado

        Returns:
            Usuario: Usuário criado

        Raises:
            ConflictException: Se remotejid já existe
        """
        # Verifica se remotejid já existe
        stmt = select(Usuario).where(Usuario.remotejid == usuario_data.remotejid)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ConflictException(f"Usuário com remotejid '{usuario_data.remotejid}' já existe")

        # Cria o usuário
        usuario = Usuario(**usuario_data.model_dump())
        db.add(usuario)
        await db.flush()
        await db.refresh(usuario)

        return usuario

    @staticmethod
    async def get_by_id(db: AsyncSession, usuario_id: UUID) -> Usuario:
        """
        Busca usuário por ID

        Args:
            db: Sessão do banco de dados
            usuario_id: ID do usuário

        Returns:
            Usuario: Usuário encontrado

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        stmt = select(Usuario).where(Usuario.id == usuario_id)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException(f"Usuário com ID {usuario_id} não encontrado")

        return usuario

    @staticmethod
    async def get_by_remotejid(db: AsyncSession, remotejid: str) -> Usuario:
        """
        Busca usuário por remotejid

        Args:
            db: Sessão do banco de dados
            remotejid: RemoteJID do usuário

        Returns:
            Usuario: Usuário encontrado

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        stmt = select(Usuario).where(Usuario.remotejid == remotejid)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException(f"Usuário com remotejid '{remotejid}' não encontrado")

        return usuario

    @staticmethod
    async def list_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        premium_active: Optional[bool] = None,
        premium_expired: Optional[bool] = None,
    ) -> Tuple[List[Usuario], int]:
        """
        Lista usuários com filtros e paginação

        Args:
            db: Sessão do banco de dados
            skip: Número de registros para pular
            limit: Limite de registros
            name: Filtro por nome (busca parcial)
            phone: Filtro por telefone (busca parcial)
            premium_active: Filtro por premium ativo
            premium_expired: Filtro por premium expirado

        Returns:
            Tuple[List[Usuario], int]: Lista de usuários e total de registros
        """
        # Query base
        stmt = select(Usuario)
        count_stmt = select(func.count(Usuario.id))

        # Aplicar filtros
        conditions = []

        if name:
            conditions.append(Usuario.name.ilike(f"%{name}%"))

        if phone:
            conditions.append(Usuario.phone.ilike(f"%{phone}%"))

        if premium_active is not None:
            now = datetime.utcnow()
            if premium_active:
                conditions.append(Usuario.premium_until > now)
            else:
                conditions.append(
                    or_(Usuario.premium_until.is_(None), Usuario.premium_until <= now)
                )

        if premium_expired is not None:
            now = datetime.utcnow()
            if premium_expired:
                conditions.append(Usuario.premium_until <= now)
                conditions.append(Usuario.premium_until.isnot(None))

        # Aplicar condições
        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        # Ordenar e paginar
        stmt = stmt.order_by(Usuario.created_at.desc()).offset(skip).limit(limit)

        # Executar queries
        result = await db.execute(stmt)
        usuarios = list(result.scalars().all())

        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        return usuarios, total

    @staticmethod
    async def update(
        db: AsyncSession,
        usuario_id: UUID,
        usuario_data: UsuarioUpdate
    ) -> Usuario:
        """
        Atualiza um usuário

        Args:
            db: Sessão do banco de dados
            usuario_id: ID do usuário
            usuario_data: Dados para atualização

        Returns:
            Usuario: Usuário atualizado

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        usuario = await UsuarioService.get_by_id(db, usuario_id)

        # Atualiza apenas campos fornecidos
        update_data = usuario_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(usuario, field, value)

        await db.flush()
        await db.refresh(usuario)

        return usuario

    @staticmethod
    async def update_premium(
        db: AsyncSession,
        usuario_id: UUID,
        premium_data: UsuarioUpdatePremium
    ) -> Usuario:
        """
        Atualiza a data de expiração do premium e tipo

        Args:
            db: Sessão do banco de dados
            usuario_id: ID do usuário
            premium_data: Nova data de expiração e tipo de premium

        Returns:
            Usuario: Usuário atualizado
        """
        usuario = await UsuarioService.get_by_id(db, usuario_id)
        usuario.premium_until = premium_data.premium_until
        if premium_data.tipo_premium:
            usuario.tipo_premium = premium_data.tipo_premium

        await db.flush()
        await db.refresh(usuario)

        return usuario

    @staticmethod
    async def update_last_message(
        db: AsyncSession,
        usuario_id: UUID,
        message_data: UsuarioUpdateLastMessage
    ) -> Usuario:
        """
        Atualiza a última mensagem do usuário

        Args:
            db: Sessão do banco de dados
            usuario_id: ID do usuário
            message_data: Nova mensagem

        Returns:
            Usuario: Usuário atualizado
        """
        usuario = await UsuarioService.get_by_id(db, usuario_id)
        usuario.last_message = message_data.last_message

        await db.flush()
        await db.refresh(usuario)

        return usuario

    @staticmethod
    async def delete(db: AsyncSession, usuario_id: UUID) -> None:
        """
        Deleta um usuário

        Args:
            db: Sessão do banco de dados
            usuario_id: ID do usuário

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        usuario = await UsuarioService.get_by_id(db, usuario_id)
        await db.delete(usuario)
        await db.flush()
