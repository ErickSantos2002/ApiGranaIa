"""
Service para lógica de negócios de Cartões de Crédito
"""
from typing import Optional, List, Tuple
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CartaoCredito, GastoFuturo, GastoFuturoParcela, Usuario, Gasto
from app.schemas.cartao_credito import (
    CartaoCreditoCreate,
    CartaoCreditoUpdate,
    FaturaMensal,
    CartaoCreditoComGastos,
)
from app.schemas.gasto import GastoCreate
from app.utils.exceptions import NotFoundException, BadRequestException


class CartaoCreditoService:
    """Service para gerenciar cartões de crédito"""

    @staticmethod
    async def create(db: AsyncSession, cartao_data: CartaoCreditoCreate) -> CartaoCredito:
        """
        Cria um novo cartão de crédito

        Args:
            db: Sessão do banco de dados
            cartao_data: Dados do cartão a ser criado

        Returns:
            CartaoCredito: Cartão criado

        Raises:
            NotFoundException: Se usuário não encontrado
            BadRequestException: Se dados inválidos
        """
        # Verifica se usuário existe
        stmt = select(Usuario).where(Usuario.remotejid == cartao_data.usuario)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException(f"Usuário com remotejid '{cartao_data.usuario}' não encontrado")

        # Cria o cartão
        cartao = CartaoCredito(**cartao_data.model_dump())
        db.add(cartao)
        await db.flush()
        await db.refresh(cartao)

        return cartao

    @staticmethod
    async def get_by_id(db: AsyncSession, cartao_id: UUID) -> CartaoCredito:
        """
        Busca cartão por ID

        Args:
            db: Sessão do banco de dados
            cartao_id: ID do cartão

        Returns:
            CartaoCredito: Cartão encontrado

        Raises:
            NotFoundException: Se cartão não encontrado
        """
        stmt = select(CartaoCredito).where(CartaoCredito.id == cartao_id)
        result = await db.execute(stmt)
        cartao = result.scalar_one_or_none()

        if not cartao:
            raise NotFoundException(f"Cartão de crédito com ID {cartao_id} não encontrado")

        return cartao

    @staticmethod
    async def list_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        usuario: Optional[str] = None,
        ativo: Optional[bool] = None,
    ) -> Tuple[List[CartaoCredito], int]:
        """
        Lista cartões com filtros e paginação

        Args:
            db: Sessão do banco de dados
            skip: Número de registros para pular
            limit: Limite de registros
            usuario: Filtro por remotejid do usuário
            ativo: Filtro por status ativo

        Returns:
            Tuple[List[CartaoCredito], int]: Lista de cartões e total
        """
        # Query base
        query = select(CartaoCredito)
        count_query = select(func.count(CartaoCredito.id))

        # Filtros
        conditions = []

        if usuario:
            conditions.append(CartaoCredito.usuario == usuario)

        if ativo is not None:
            conditions.append(CartaoCredito.ativo == ativo)

        # Aplica filtros
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Ordena por created_at desc
        query = query.order_by(CartaoCredito.created_at.desc())

        # Paginação
        query = query.offset(skip).limit(limit)

        # Executa queries
        result = await db.execute(query)
        cartoes = result.scalars().all()

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        return cartoes, total

    @staticmethod
    async def update(
        db: AsyncSession,
        cartao_id: UUID,
        cartao_data: CartaoCreditoUpdate
    ) -> CartaoCredito:
        """
        Atualiza um cartão de crédito

        Args:
            db: Sessão do banco de dados
            cartao_id: ID do cartão
            cartao_data: Dados a serem atualizados

        Returns:
            CartaoCredito: Cartão atualizado

        Raises:
            NotFoundException: Se cartão não encontrado
        """
        cartao = await CartaoCreditoService.get_by_id(db, cartao_id)

        # Atualiza apenas os campos fornecidos
        update_data = cartao_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(cartao, field, value)

        await db.flush()
        await db.refresh(cartao)

        return cartao

    @staticmethod
    async def delete(db: AsyncSession, cartao_id: UUID):
        """
        Deleta um cartão de crédito

        Args:
            db: Sessão do banco de dados
            cartao_id: ID do cartão

        Raises:
            NotFoundException: Se cartão não encontrado
        """
        cartao = await CartaoCreditoService.get_by_id(db, cartao_id)
        await db.delete(cartao)
        await db.flush()

    @staticmethod
    async def get_with_info(db: AsyncSession, cartao_id: UUID) -> CartaoCreditoComGastos:
        """
        Busca cartão com informações adicionais de gastos

        Args:
            db: Sessão do banco de dados
            cartao_id: ID do cartão

        Returns:
            CartaoCreditoComGastos: Cartão com informações de gastos

        Raises:
            NotFoundException: Se cartão não encontrado
        """
        cartao = await CartaoCreditoService.get_by_id(db, cartao_id)

        # Busca total de gastos ativos
        stmt_total = select(func.count(GastoFuturo.id)).where(
            and_(
                GastoFuturo.cartao_credito_id == cartao_id,
                GastoFuturo.status == 'ativo'
            )
        )
        result_total = await db.execute(stmt_total)
        total_gastos_ativos = result_total.scalar() or 0

        # Busca valor total pendente (soma das parcelas pendentes)
        stmt_valor = select(func.sum(GastoFuturoParcela.valor_parcela)).select_from(
            GastoFuturoParcela
        ).join(
            GastoFuturo, GastoFuturoParcela.gasto_futuro_id == GastoFuturo.id
        ).where(
            and_(
                GastoFuturo.cartao_credito_id == cartao_id,
                GastoFuturoParcela.status == 'pendente'
            )
        )
        result_valor = await db.execute(stmt_valor)
        valor_total_pendente = result_valor.scalar() or Decimal(0)

        # Busca próxima fatura (menor mes_referencia com parcelas pendentes)
        stmt_proxima = select(GastoFuturoParcela.mes_referencia).select_from(
            GastoFuturoParcela
        ).join(
            GastoFuturo, GastoFuturoParcela.gasto_futuro_id == GastoFuturo.id
        ).where(
            and_(
                GastoFuturo.cartao_credito_id == cartao_id,
                GastoFuturoParcela.status == 'pendente',
                GastoFuturoParcela.mes_referencia.isnot(None)
            )
        ).order_by(GastoFuturoParcela.mes_referencia.asc()).limit(1)
        result_proxima = await db.execute(stmt_proxima)
        proxima_fatura = result_proxima.scalar_one_or_none()

        return CartaoCreditoComGastos(
            **cartao.__dict__,
            total_gastos_ativos=total_gastos_ativos,
            valor_total_pendente=valor_total_pendente,
            proxima_fatura=proxima_fatura
        )

    @staticmethod
    async def get_faturas_mensais(
        db: AsyncSession,
        cartao_id: UUID,
        mes_inicio: Optional[str] = None,
        mes_fim: Optional[str] = None,
    ) -> List[FaturaMensal]:
        """
        Busca faturas mensais de um cartão

        Args:
            db: Sessão do banco de dados
            cartao_id: ID do cartão
            mes_inicio: Mês inicial (YYYY-MM) opcional
            mes_fim: Mês final (YYYY-MM) opcional

        Returns:
            List[FaturaMensal]: Lista de faturas mensais

        Raises:
            NotFoundException: Se cartão não encontrado
        """
        # Verifica se cartão existe
        cartao = await CartaoCreditoService.get_by_id(db, cartao_id)

        # Query usando a view faturas_mensais
        query = text("""
            SELECT
                cartao_credito_id,
                mes_referencia,
                nome_cartao,
                dia_vencimento,
                total_compras,
                total_parcelas,
                valor_pendente,
                valor_pago,
                valor_atrasado,
                valor_total_fatura
            FROM faturas_mensais
            WHERE cartao_credito_id = :cartao_id
        """)

        params = {"cartao_id": str(cartao_id)}

        if mes_inicio:
            query = text(str(query) + " AND mes_referencia >= :mes_inicio")
            params["mes_inicio"] = mes_inicio

        if mes_fim:
            query = text(str(query) + " AND mes_referencia <= :mes_fim")
            params["mes_fim"] = mes_fim

        query = text(str(query) + " ORDER BY mes_referencia DESC")

        result = await db.execute(query, params)
        rows = result.fetchall()

        faturas = []
        for row in rows:
            faturas.append(FaturaMensal(
                cartao_id=row[0],
                mes_referencia=row[1],
                nome_cartao=row[2],
                dia_vencimento=row[3],
                total_compras=row[4],
                total_parcelas=row[5],
                valor_pendente=row[6] or Decimal(0),
                valor_pago=row[7] or Decimal(0),
                valor_atrasado=row[8] or Decimal(0),
                valor_total_fatura=row[9] or Decimal(0),
            ))

        return faturas

    @staticmethod
    async def pagar_fatura_mensal(
        db: AsyncSession,
        cartao_id: UUID,
        mes_referencia: str,
        data_pagamento: Optional[datetime] = None,
        criar_gasto: bool = True
    ) -> dict:
        """
        Paga todas as parcelas de uma fatura mensal

        Args:
            db: Sessão do banco de dados
            cartao_id: ID do cartão
            mes_referencia: Mês de referência (YYYY-MM)
            data_pagamento: Data do pagamento
            criar_gasto: Se deve criar um gasto normal

        Returns:
            dict: Informações do pagamento

        Raises:
            NotFoundException: Se cartão não encontrado
            BadRequestException: Se não há parcelas pendentes
        """
        # Verifica se cartão existe
        cartao = await CartaoCreditoService.get_by_id(db, cartao_id)

        if data_pagamento is None:
            data_pagamento = datetime.now()

        # Busca todas as parcelas pendentes do mês
        stmt = select(GastoFuturoParcela).join(
            GastoFuturo, GastoFuturoParcela.gasto_futuro_id == GastoFuturo.id
        ).where(
            and_(
                GastoFuturo.cartao_credito_id == cartao_id,
                GastoFuturoParcela.mes_referencia == mes_referencia,
                GastoFuturoParcela.status == 'pendente'
            )
        )
        result = await db.execute(stmt)
        parcelas_pendentes = result.scalars().all()

        if not parcelas_pendentes:
            raise BadRequestException(
                f"Não há parcelas pendentes para o cartão no mês {mes_referencia}"
            )

        # Calcula valor total
        valor_total_fatura = sum(p.valor_parcela for p in parcelas_pendentes)

        # Marca todas as parcelas como pagas
        for parcela in parcelas_pendentes:
            parcela.status = 'pago'
            parcela.data_pagamento = data_pagamento

        # Cria um gasto único para a fatura completa se solicitado
        gasto_id = None
        if criar_gasto:
            # Busca o usuário do cartão
            gasto_create = GastoCreate(
                usuario=cartao.usuario,
                descricao=f"Fatura {cartao.nome_cartao} - {mes_referencia}",
                valor=valor_total_fatura,
                categoria="Outros",  # Pode ser ajustado
                data=data_pagamento
            )

            gasto = Gasto(**gasto_create.model_dump())
            db.add(gasto)
            await db.flush()
            await db.refresh(gasto)
            gasto_id = gasto.id

            # Associa o gasto às parcelas
            for parcela in parcelas_pendentes:
                parcela.gasto_id = gasto_id

        await db.flush()

        return {
            "cartao_id": str(cartao_id),
            "nome_cartao": cartao.nome_cartao,
            "mes_referencia": mes_referencia,
            "parcelas_pagas": len(parcelas_pendentes),
            "valor_total": float(valor_total_fatura),
            "data_pagamento": data_pagamento.isoformat(),
            "gasto_criado": criar_gasto,
            "gasto_id": str(gasto_id) if gasto_id else None,
        }
