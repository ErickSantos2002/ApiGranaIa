"""
Service para lógica de negócios de Gastos
"""
from typing import Optional, List, Tuple
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Gasto, Usuario
from app.schemas.gasto import (
    GastoCreate,
    GastoUpdate,
    GastoCategoriaSummary,
    GastoDashboard,
)
from app.utils.exceptions import NotFoundException, BadRequestException


class GastoService:
    """Service para gerenciar gastos"""

    @staticmethod
    async def create(db: AsyncSession, gasto_data: GastoCreate) -> Gasto:
        """
        Cria um novo gasto

        Args:
            db: Sessão do banco de dados
            gasto_data: Dados do gasto a ser criado

        Returns:
            Gasto: Gasto criado

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        # Verifica se usuário existe
        stmt = select(Usuario).where(Usuario.id == gasto_data.usuario)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException(f"Usuário com ID {gasto_data.usuario} não encontrado")

        # Cria o gasto
        gasto = Gasto(**gasto_data.model_dump())
        db.add(gasto)
        await db.flush()
        await db.refresh(gasto)

        return gasto

    @staticmethod
    async def get_by_id(db: AsyncSession, gasto_id: UUID) -> Gasto:
        """
        Busca gasto por ID

        Args:
            db: Sessão do banco de dados
            gasto_id: ID do gasto

        Returns:
            Gasto: Gasto encontrado

        Raises:
            NotFoundException: Se gasto não encontrado
        """
        stmt = select(Gasto).where(Gasto.id == gasto_id)
        result = await db.execute(stmt)
        gasto = result.scalar_one_or_none()

        if not gasto:
            raise NotFoundException(f"Gasto com ID {gasto_id} não encontrado")

        return gasto

    @staticmethod
    async def list_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        usuario_id: Optional[UUID] = None,
        categoria: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        valor_min: Optional[Decimal] = None,
        valor_max: Optional[Decimal] = None,
    ) -> Tuple[List[Gasto], int]:
        """
        Lista gastos com filtros e paginação

        Args:
            db: Sessão do banco de dados
            skip: Número de registros para pular
            limit: Limite de registros
            usuario_id: Filtro por ID do usuário
            categoria: Filtro por categoria
            data_inicio: Data de início do período
            data_fim: Data de fim do período
            valor_min: Valor mínimo
            valor_max: Valor máximo

        Returns:
            Tuple[List[Gasto], int]: Lista de gastos e total de registros
        """
        # Query base
        stmt = select(Gasto)
        count_stmt = select(func.count(Gasto.id))

        # Aplicar filtros
        conditions = []

        if usuario_id:
            conditions.append(Gasto.usuario == usuario_id)

        if categoria:
            conditions.append(Gasto.categoria.ilike(f"%{categoria}%"))

        if data_inicio:
            conditions.append(Gasto.data >= data_inicio)

        if data_fim:
            conditions.append(Gasto.data <= data_fim)

        if valor_min is not None:
            conditions.append(Gasto.valor >= valor_min)

        if valor_max is not None:
            conditions.append(Gasto.valor <= valor_max)

        # Aplicar condições
        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        # Ordenar e paginar
        stmt = stmt.order_by(Gasto.data.desc()).offset(skip).limit(limit)

        # Executar queries
        result = await db.execute(stmt)
        gastos = list(result.scalars().all())

        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        return gastos, total

    @staticmethod
    async def update(
        db: AsyncSession,
        gasto_id: UUID,
        gasto_data: GastoUpdate
    ) -> Gasto:
        """
        Atualiza um gasto

        Args:
            db: Sessão do banco de dados
            gasto_id: ID do gasto
            gasto_data: Dados para atualização

        Returns:
            Gasto: Gasto atualizado

        Raises:
            NotFoundException: Se gasto não encontrado
        """
        gasto = await GastoService.get_by_id(db, gasto_id)

        # Atualiza apenas campos fornecidos
        update_data = gasto_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(gasto, field, value)

        await db.flush()
        await db.refresh(gasto)

        return gasto

    @staticmethod
    async def delete(db: AsyncSession, gasto_id: UUID) -> None:
        """
        Deleta um gasto

        Args:
            db: Sessão do banco de dados
            gasto_id: ID do gasto

        Raises:
            NotFoundException: Se gasto não encontrado
        """
        gasto = await GastoService.get_by_id(db, gasto_id)
        await db.delete(gasto)
        await db.flush()

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        usuario_id: Optional[UUID] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> GastoDashboard:
        """
        Gera dashboard de gastos com estatísticas

        Args:
            db: Sessão do banco de dados
            usuario_id: Filtro por ID do usuário
            data_inicio: Data de início do período
            data_fim: Data de fim do período

        Returns:
            GastoDashboard: Dashboard com estatísticas
        """
        # Condições base
        conditions = []

        if usuario_id:
            conditions.append(Gasto.usuario == usuario_id)

        if data_inicio:
            conditions.append(Gasto.data >= data_inicio)

        if data_fim:
            conditions.append(Gasto.data <= data_fim)

        # Query para total geral e quantidade
        stmt_total = select(
            func.coalesce(func.sum(Gasto.valor), 0).label("total"),
            func.count(Gasto.id).label("quantidade")
        )

        if conditions:
            stmt_total = stmt_total.where(and_(*conditions))

        result_total = await db.execute(stmt_total)
        total_row = result_total.one()

        # Query para gastos por categoria
        stmt_categoria = select(
            Gasto.categoria,
            func.sum(Gasto.valor).label("total"),
            func.count(Gasto.id).label("quantidade")
        ).group_by(Gasto.categoria).order_by(func.sum(Gasto.valor).desc())

        if conditions:
            stmt_categoria = stmt_categoria.where(and_(*conditions))

        result_categoria = await db.execute(stmt_categoria)
        categorias = result_categoria.all()

        # Montar dashboard
        por_categoria = [
            GastoCategoriaSummary(
                categoria=row.categoria,
                total=Decimal(str(row.total)),
                quantidade=row.quantidade
            )
            for row in categorias
        ]

        dashboard = GastoDashboard(
            total_geral=Decimal(str(total_row.total)),
            quantidade_total=total_row.quantidade,
            por_categoria=por_categoria,
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
        )

        return dashboard
