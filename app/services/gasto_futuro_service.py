"""
Service para lógica de negócios de Gastos Futuros (Cartão de Crédito)
"""
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GastoFuturo, GastoFuturoParcela, Usuario, Gasto
from app.schemas.gasto_futuro import (
    GastoFuturoCreate,
    GastoFuturoUpdate,
    ParcelaUpdate,
    GastoFuturoResumo,
    GastoFuturoProximosVencimentos,
    GastoFuturoDashboard,
)
from app.schemas.gasto import GastoCreate
from app.utils.exceptions import NotFoundException, BadRequestException


class GastoFuturoService:
    """Service para gerenciar gastos futuros"""

    @staticmethod
    async def create(db: AsyncSession, gasto_futuro_data: GastoFuturoCreate) -> GastoFuturo:
        """
        Cria um novo gasto futuro e suas parcelas (se parcelado)

        Args:
            db: Sessão do banco de dados
            gasto_futuro_data: Dados do gasto futuro a ser criado

        Returns:
            GastoFuturo: Gasto futuro criado com parcelas

        Raises:
            NotFoundException: Se usuário não encontrado
            BadRequestException: Se dados inválidos
        """
        # Verifica se usuário existe
        stmt = select(Usuario).where(Usuario.remotejid == gasto_futuro_data.usuario)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException(f"Usuário com remotejid '{gasto_futuro_data.usuario}' não encontrado")

        # Valida parcelas
        if gasto_futuro_data.numero_parcelas > 1:
            if not gasto_futuro_data.valor_parcela:
                raise BadRequestException("valor_parcela é obrigatório quando número de parcelas > 1")

        # Cria o gasto futuro
        gasto_futuro = GastoFuturo(**gasto_futuro_data.model_dump(exclude={'parcelas'}))
        db.add(gasto_futuro)
        await db.flush()
        await db.refresh(gasto_futuro)

        # Se parcelado, cria as parcelas automaticamente
        if gasto_futuro.numero_parcelas > 1:
            await GastoFuturoService._criar_parcelas(
                db=db,
                gasto_futuro=gasto_futuro,
                numero_parcelas=gasto_futuro.numero_parcelas,
                valor_parcela=gasto_futuro.valor_parcela,
                data_primeira_parcela=gasto_futuro.data_vencimento
            )

        await db.refresh(gasto_futuro)
        return gasto_futuro

    @staticmethod
    async def _criar_parcelas(
        db: AsyncSession,
        gasto_futuro: GastoFuturo,
        numero_parcelas: int,
        valor_parcela: Decimal,
        data_primeira_parcela: datetime
    ):
        """
        Cria as parcelas de um gasto futuro parcelado

        Args:
            db: Sessão do banco de dados
            gasto_futuro: Gasto futuro pai
            numero_parcelas: Quantidade de parcelas
            valor_parcela: Valor de cada parcela
            data_primeira_parcela: Data de vencimento da primeira parcela
        """
        parcelas = []

        for i in range(1, numero_parcelas + 1):
            # Calcula data de vencimento (soma meses)
            data_vencimento = data_primeira_parcela + relativedelta(months=i-1)

            parcela = GastoFuturoParcela(
                gasto_futuro_id=gasto_futuro.id,
                numero_parcela=i,
                total_parcelas=numero_parcelas,
                valor_parcela=valor_parcela,
                data_vencimento=data_vencimento,
                status='pendente'
            )
            parcelas.append(parcela)

        db.add_all(parcelas)
        await db.flush()

    @staticmethod
    async def get_by_id(db: AsyncSession, gasto_futuro_id: UUID) -> GastoFuturo:
        """
        Busca gasto futuro por ID

        Args:
            db: Sessão do banco de dados
            gasto_futuro_id: ID do gasto futuro

        Returns:
            GastoFuturo: Gasto futuro encontrado

        Raises:
            NotFoundException: Se gasto futuro não encontrado
        """
        stmt = select(GastoFuturo).where(GastoFuturo.id == gasto_futuro_id)
        result = await db.execute(stmt)
        gasto_futuro = result.scalar_one_or_none()

        if not gasto_futuro:
            raise NotFoundException(f"Gasto futuro com ID {gasto_futuro_id} não encontrado")

        return gasto_futuro

    @staticmethod
    async def list_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        usuario: Optional[str] = None,
        status: Optional[str] = None,
        categoria: Optional[str] = None,
        data_vencimento_inicio: Optional[datetime] = None,
        data_vencimento_fim: Optional[datetime] = None,
    ) -> Tuple[List[GastoFuturo], int]:
        """
        Lista gastos futuros com filtros e paginação

        Args:
            db: Sessão do banco de dados
            skip: Número de registros para pular
            limit: Limite de registros
            usuario: Filtro por remotejid do usuário
            status: Filtro por status
            categoria: Filtro por categoria
            data_vencimento_inicio: Data inicial de vencimento
            data_vencimento_fim: Data final de vencimento

        Returns:
            Tuple[List[GastoFuturo], int]: Lista de gastos futuros e total
        """
        # Query base
        query = select(GastoFuturo)
        count_query = select(func.count(GastoFuturo.id))

        # Filtros
        conditions = []

        if usuario:
            conditions.append(GastoFuturo.usuario == usuario)

        if status:
            conditions.append(GastoFuturo.status == status)

        if categoria:
            conditions.append(GastoFuturo.categoria == categoria)

        if data_vencimento_inicio:
            conditions.append(GastoFuturo.data_vencimento >= data_vencimento_inicio)

        if data_vencimento_fim:
            conditions.append(GastoFuturo.data_vencimento <= data_vencimento_fim)

        # Aplica filtros
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Ordena por data de vencimento (mais próximos primeiro)
        query = query.order_by(GastoFuturo.data_vencimento.asc())

        # Paginação
        query = query.offset(skip).limit(limit)

        # Executa queries
        result = await db.execute(query)
        gastos_futuros = result.scalars().all()

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        return gastos_futuros, total

    @staticmethod
    async def update(
        db: AsyncSession,
        gasto_futuro_id: UUID,
        gasto_futuro_data: GastoFuturoUpdate
    ) -> GastoFuturo:
        """
        Atualiza um gasto futuro

        Args:
            db: Sessão do banco de dados
            gasto_futuro_id: ID do gasto futuro
            gasto_futuro_data: Dados a serem atualizados

        Returns:
            GastoFuturo: Gasto futuro atualizado

        Raises:
            NotFoundException: Se gasto futuro não encontrado
        """
        gasto_futuro = await GastoFuturoService.get_by_id(db, gasto_futuro_id)

        # Atualiza apenas os campos fornecidos
        update_data = gasto_futuro_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(gasto_futuro, field, value)

        await db.flush()
        await db.refresh(gasto_futuro)

        return gasto_futuro

    @staticmethod
    async def delete(db: AsyncSession, gasto_futuro_id: UUID):
        """
        Deleta um gasto futuro e suas parcelas

        Args:
            db: Sessão do banco de dados
            gasto_futuro_id: ID do gasto futuro

        Raises:
            NotFoundException: Se gasto futuro não encontrado
        """
        gasto_futuro = await GastoFuturoService.get_by_id(db, gasto_futuro_id)
        await db.delete(gasto_futuro)
        await db.flush()

    @staticmethod
    async def marcar_como_pago(
        db: AsyncSession,
        gasto_futuro_id: UUID,
        data_pagamento: Optional[datetime] = None,
        criar_gasto: bool = True
    ) -> GastoFuturo:
        """
        Marca um gasto futuro como pago

        Args:
            db: Sessão do banco de dados
            gasto_futuro_id: ID do gasto futuro
            data_pagamento: Data do pagamento (padrão: agora)
            criar_gasto: Se deve criar um gasto normal

        Returns:
            GastoFuturo: Gasto futuro atualizado

        Raises:
            NotFoundException: Se gasto futuro não encontrado
            BadRequestException: Se gasto já está pago
        """
        gasto_futuro = await GastoFuturoService.get_by_id(db, gasto_futuro_id)

        if gasto_futuro.status == 'pago':
            raise BadRequestException("Gasto futuro já está marcado como pago")

        if data_pagamento is None:
            data_pagamento = datetime.now()

        # Atualiza status
        gasto_futuro.status = 'pago'
        gasto_futuro.data_pagamento = data_pagamento

        # Cria gasto normal se solicitado
        if criar_gasto:
            gasto_create = GastoCreate(
                usuario=gasto_futuro.usuario,
                descricao=gasto_futuro.descricao,
                valor=gasto_futuro.valor_total,
                categoria=gasto_futuro.categoria,
                data=data_pagamento
            )

            gasto = Gasto(**gasto_create.model_dump())
            db.add(gasto)
            await db.flush()
            await db.refresh(gasto)

            gasto_futuro.gasto_id = gasto.id

        await db.flush()
        await db.refresh(gasto_futuro)

        return gasto_futuro

    @staticmethod
    async def marcar_parcela_como_paga(
        db: AsyncSession,
        parcela_id: UUID,
        data_pagamento: Optional[datetime] = None,
        criar_gasto: bool = True
    ) -> GastoFuturoParcela:
        """
        Marca uma parcela como paga

        Args:
            db: Sessão do banco de dados
            parcela_id: ID da parcela
            data_pagamento: Data do pagamento
            criar_gasto: Se deve criar um gasto normal

        Returns:
            GastoFuturoParcela: Parcela atualizada

        Raises:
            NotFoundException: Se parcela não encontrada
            BadRequestException: Se parcela já está paga
        """
        stmt = select(GastoFuturoParcela).where(GastoFuturoParcela.id == parcela_id)
        result = await db.execute(stmt)
        parcela = result.scalar_one_or_none()

        if not parcela:
            raise NotFoundException(f"Parcela com ID {parcela_id} não encontrada")

        if parcela.status == 'pago':
            raise BadRequestException("Parcela já está marcada como paga")

        if data_pagamento is None:
            data_pagamento = datetime.now()

        # Busca gasto futuro pai
        gasto_futuro = await GastoFuturoService.get_by_id(db, parcela.gasto_futuro_id)

        # Atualiza parcela
        parcela.status = 'pago'
        parcela.data_pagamento = data_pagamento

        # Cria gasto normal se solicitado
        if criar_gasto:
            gasto_create = GastoCreate(
                usuario=gasto_futuro.usuario,
                descricao=f"{gasto_futuro.descricao} ({parcela.numero_parcela}/{parcela.total_parcelas})",
                valor=parcela.valor_parcela,
                categoria=gasto_futuro.categoria,
                data=data_pagamento
            )

            gasto = Gasto(**gasto_create.model_dump())
            db.add(gasto)
            await db.flush()
            await db.refresh(gasto)

            parcela.gasto_id = gasto.id

        await db.flush()
        await db.refresh(parcela)

        return parcela

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        usuario: str
    ) -> GastoFuturoDashboard:
        """
        Retorna dashboard de gastos futuros do usuário

        Args:
            db: Sessão do banco de dados
            usuario: RemoteJID do usuário

        Returns:
            GastoFuturoDashboard: Dashboard com resumo e próximos vencimentos
        """
        # Busca gastos futuros ativos
        stmt = select(GastoFuturo).where(
            and_(
                GastoFuturo.usuario == usuario,
                GastoFuturo.status == 'ativo'
            )
        )
        result = await db.execute(stmt)
        gastos_ativos = result.scalars().all()

        # Calcula resumo
        hoje = datetime.now()
        primeiro_dia_mes = hoje.replace(day=1)
        ultimo_dia_mes = (primeiro_dia_mes + relativedelta(months=1)) - timedelta(days=1)

        total_valor = sum(g.valor_total for g in gastos_ativos)
        quantidade_total = len(gastos_ativos)

        # Vencidos
        gastos_vencidos = [g for g in gastos_ativos if g.data_vencimento < hoje]
        quantidade_vencidos = len(gastos_vencidos)
        valor_vencido = sum(g.valor_total for g in gastos_vencidos)

        # Mês atual
        gastos_mes = [g for g in gastos_ativos if primeiro_dia_mes <= g.data_vencimento <= ultimo_dia_mes]
        quantidade_mes_atual = len(gastos_mes)
        valor_mes_atual = sum(g.valor_total for g in gastos_mes)

        resumo = GastoFuturoResumo(
            total_valor=total_valor,
            quantidade_total=quantidade_total,
            quantidade_vencidos=quantidade_vencidos,
            valor_vencido=valor_vencido,
            quantidade_mes_atual=quantidade_mes_atual,
            valor_mes_atual=valor_mes_atual
        )

        # Próximos vencimentos (7 dias)
        data_limite = hoje + timedelta(days=7)
        proximos = [
            GastoFuturoProximosVencimentos(
                id=g.id,
                descricao=g.descricao,
                valor_total=g.valor_total,
                data_vencimento=g.data_vencimento,
                dias_para_vencimento=(g.data_vencimento - hoje).days,
                status=g.status
            )
            for g in gastos_ativos
            if hoje <= g.data_vencimento <= data_limite
        ]

        # Ordena por data de vencimento
        proximos.sort(key=lambda x: x.data_vencimento)

        return GastoFuturoDashboard(
            resumo=resumo,
            proximos_vencimentos=proximos
        )

    @staticmethod
    async def atualizar_status_parcelas_vencidas(db: AsyncSession):
        """
        Atualiza status de parcelas vencidas para 'atrasado'

        Args:
            db: Sessão do banco de dados

        Returns:
            int: Quantidade de parcelas atualizadas
        """
        hoje = datetime.now()

        stmt = select(GastoFuturoParcela).where(
            and_(
                GastoFuturoParcela.status == 'pendente',
                GastoFuturoParcela.data_vencimento < hoje
            )
        )
        result = await db.execute(stmt)
        parcelas_vencidas = result.scalars().all()

        for parcela in parcelas_vencidas:
            parcela.status = 'atrasado'

        await db.flush()

        return len(parcelas_vencidas)
