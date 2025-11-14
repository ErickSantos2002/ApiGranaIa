"""
Service para lógica de negócios de Receitas
"""
from typing import Optional, List, Tuple
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Receita, Usuario
from app.schemas.receita import (
    ReceitaCreate,
    ReceitaUpdate,
    ReceitaCategoriaSummary,
    ReceitaDashboard,
)
from app.utils.exceptions import NotFoundException, BadRequestException


class ReceitaService:
    """Service para gerenciar receitas"""

    @staticmethod
    async def create(db: AsyncSession, receita_data: ReceitaCreate) -> Receita:
        """
        Cria uma nova receita

        Args:
            db: Sessão do banco de dados
            receita_data: Dados da receita a ser criada

        Returns:
            Receita: Receita criada

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        # Verifica se usuário existe
        stmt = select(Usuario).where(Usuario.id == receita_data.usuario)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException(f"Usuário com ID {receita_data.usuario} não encontrado")

        # Cria a receita
        receita = Receita(**receita_data.model_dump())
        db.add(receita)
        await db.flush()
        await db.refresh(receita)

        return receita

    @staticmethod
    async def get_by_id(db: AsyncSession, receita_id: UUID) -> Receita:
        """
        Busca receita por ID

        Args:
            db: Sessão do banco de dados
            receita_id: ID da receita

        Returns:
            Receita: Receita encontrada

        Raises:
            NotFoundException: Se receita não encontrada
        """
        stmt = select(Receita).where(Receita.id == receita_id)
        result = await db.execute(stmt)
        receita = result.scalar_one_or_none()

        if not receita:
            raise NotFoundException(f"Receita com ID {receita_id} não encontrada")

        return receita

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
    ) -> Tuple[List[Receita], int]:
        """
        Lista receitas com filtros e paginação

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
            Tuple[List[Receita], int]: Lista de receitas e total de registros
        """
        # Query base
        stmt = select(Receita)
        count_stmt = select(func.count(Receita.id))

        # Aplicar filtros
        conditions = []

        if usuario_id:
            conditions.append(Receita.usuario == usuario_id)

        if categoria:
            conditions.append(Receita.categoria.ilike(f"%{categoria}%"))

        if data_inicio:
            conditions.append(Receita.data >= data_inicio)

        if data_fim:
            conditions.append(Receita.data <= data_fim)

        if valor_min is not None:
            conditions.append(Receita.valor >= valor_min)

        if valor_max is not None:
            conditions.append(Receita.valor <= valor_max)

        # Aplicar condições
        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        # Ordenar e paginar
        stmt = stmt.order_by(Receita.data.desc()).offset(skip).limit(limit)

        # Executar queries
        result = await db.execute(stmt)
        receitas = list(result.scalars().all())

        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        return receitas, total

    @staticmethod
    async def update(
        db: AsyncSession,
        receita_id: UUID,
        receita_data: ReceitaUpdate
    ) -> Receita:
        """
        Atualiza uma receita

        Args:
            db: Sessão do banco de dados
            receita_id: ID da receita
            receita_data: Dados para atualização

        Returns:
            Receita: Receita atualizada

        Raises:
            NotFoundException: Se receita não encontrada
        """
        receita = await ReceitaService.get_by_id(db, receita_id)

        # Atualiza apenas campos fornecidos
        update_data = receita_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(receita, field, value)

        await db.flush()
        await db.refresh(receita)

        return receita

    @staticmethod
    async def delete(db: AsyncSession, receita_id: UUID) -> None:
        """
        Deleta uma receita

        Args:
            db: Sessão do banco de dados
            receita_id: ID da receita

        Raises:
            NotFoundException: Se receita não encontrada
        """
        receita = await ReceitaService.get_by_id(db, receita_id)
        await db.delete(receita)
        await db.flush()

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        usuario_id: Optional[UUID] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> ReceitaDashboard:
        """
        Gera dashboard de receitas com estatísticas

        Args:
            db: Sessão do banco de dados
            usuario_id: Filtro por ID do usuário
            data_inicio: Data de início do período
            data_fim: Data de fim do período

        Returns:
            ReceitaDashboard: Dashboard com estatísticas
        """
        # Condições base
        conditions = []

        if usuario_id:
            conditions.append(Receita.usuario == usuario_id)

        if data_inicio:
            conditions.append(Receita.data >= data_inicio)

        if data_fim:
            conditions.append(Receita.data <= data_fim)

        # Query para total geral e quantidade
        stmt_total = select(
            func.coalesce(func.sum(Receita.valor), 0).label("total"),
            func.count(Receita.id).label("quantidade")
        )

        if conditions:
            stmt_total = stmt_total.where(and_(*conditions))

        result_total = await db.execute(stmt_total)
        total_row = result_total.one()

        # Query para receitas por categoria
        stmt_categoria = select(
            Receita.categoria,
            func.sum(Receita.valor).label("total"),
            func.count(Receita.id).label("quantidade")
        ).group_by(Receita.categoria).order_by(func.sum(Receita.valor).desc())

        if conditions:
            stmt_categoria = stmt_categoria.where(and_(*conditions))

        result_categoria = await db.execute(stmt_categoria)
        categorias = result_categoria.all()

        # Montar dashboard
        por_categoria = [
            ReceitaCategoriaSummary(
                categoria=row.categoria,
                total=Decimal(str(row.total)),
                quantidade=row.quantidade
            )
            for row in categorias
        ]

        dashboard = ReceitaDashboard(
            total_geral=Decimal(str(total_row.total)),
            quantidade_total=total_row.quantidade,
            por_categoria=por_categoria,
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
        )

        return dashboard
