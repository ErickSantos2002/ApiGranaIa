"""
Model SQLAlchemy para Gasto Futuro (Cartão de Crédito)
"""
from sqlalchemy import Column, Text, DateTime, Numeric, ForeignKey, Index, Enum, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class GastoFuturo(Base):
    """
    Model para tabela de gastos futuros (cartão de crédito, débito futuro, etc)
    Gastos que ainda não impactaram o saldo do usuário
    """
    __tablename__ = "gastos_futuros"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False
    )
    usuario = Column(
        Text,
        ForeignKey("usuarios.remotejid", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Informações básicas
    descricao = Column(Text, nullable=False)
    valor_total = Column(Numeric(precision=12, scale=2), nullable=False)
    categoria = Column(
        Enum(
            'Alimentação',
            'Transporte',
            'Moradia',
            'Saúde',
            'Educação',
            'Lazer',
            'Compras',
            'Assinaturas',
            'Outros',
            name='categorias_financeiras',
            create_type=False
        ),
        nullable=False,
        index=True
    )

    # Datas
    data_compra = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    data_vencimento = Column(DateTime(timezone=False), nullable=False)
    data_pagamento = Column(DateTime(timezone=False), nullable=True)

    # Parcelas
    numero_parcelas = Column(Integer, default=1, nullable=False)
    valor_parcela = Column(Numeric(precision=12, scale=2), nullable=True)

    # Status e método
    status = Column(
        Enum('ativo', 'pago', 'cancelado', name='status_gasto_futuro', create_type=False),
        nullable=False,
        default='ativo',
        server_default='ativo',
        index=True
    )
    metodo_pagamento = Column(
        Enum('credito', 'debito_futuro', 'parcelado', name='metodo_pagamento', create_type=False),
        nullable=False,
        default='credito',
        server_default='credito'
    )

    # Observações
    observacoes = Column(Text, nullable=True)

    # ID do gasto criado quando marcar como pago
    gasto_id = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relacionamentos
    usuario_rel = relationship(
        "Usuario",
        back_populates="gastos_futuros",
        foreign_keys=[usuario]
    )

    parcelas = relationship(
        "GastoFuturoParcela",
        back_populates="gasto_futuro",
        cascade="all, delete-orphan",
        lazy="selectin"  # Carrega automaticamente as parcelas
    )

    # Constraints
    __table_args__ = (
        CheckConstraint('valor_total > 0', name='check_valor_total_positivo'),
        CheckConstraint('numero_parcelas >= 1', name='check_numero_parcelas_valido'),
        CheckConstraint(
            '(numero_parcelas = 1) OR (numero_parcelas > 1 AND valor_parcela IS NOT NULL)',
            name='check_valor_parcela_quando_parcelado'
        ),
        Index('idx_gastos_futuros_usuario', 'usuario'),
        Index('idx_gastos_futuros_status', 'status'),
        Index('idx_gastos_futuros_categoria', 'categoria'),
        Index('idx_gastos_futuros_data_vencimento', 'data_vencimento'),
        Index('idx_gastos_futuros_data_compra', 'data_compra'),
        Index('idx_gastos_futuros_usuario_status', 'usuario', 'status'),
        Index('idx_gastos_futuros_usuario_data_vencimento', 'usuario', 'data_vencimento'),
    )

    def __repr__(self):
        return f"<GastoFuturo(id={self.id}, descricao={self.descricao}, valor_total={self.valor_total}, status={self.status})>"


class GastoFuturoParcela(Base):
    """
    Model para parcelas de gastos futuros
    """
    __tablename__ = "gastos_futuros_parcelas"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False
    )
    gasto_futuro_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gastos_futuros.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Informações da parcela
    numero_parcela = Column(Integer, nullable=False)
    total_parcelas = Column(Integer, nullable=False)
    valor_parcela = Column(Numeric(precision=12, scale=2), nullable=False)

    # Datas
    data_vencimento = Column(DateTime(timezone=False), nullable=False)
    data_pagamento = Column(DateTime(timezone=False), nullable=True)

    # Status
    status = Column(
        Enum('pendente', 'pago', 'atrasado', name='status_parcela', create_type=False),
        nullable=False,
        default='pendente',
        server_default='pendente',
        index=True
    )

    # ID do gasto criado quando pagar esta parcela
    gasto_id = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relacionamento
    gasto_futuro = relationship(
        "GastoFuturo",
        back_populates="parcelas",
        foreign_keys=[gasto_futuro_id]
    )

    # Constraints
    __table_args__ = (
        CheckConstraint('numero_parcela >= 1', name='check_numero_parcela_positivo'),
        CheckConstraint('total_parcelas >= 1', name='check_total_parcelas_positivo'),
        CheckConstraint('numero_parcela <= total_parcelas', name='check_numero_parcela_valido'),
        CheckConstraint('valor_parcela > 0', name='check_valor_parcela_positivo'),
        Index('idx_parcelas_gasto_futuro_id', 'gasto_futuro_id'),
        Index('idx_parcelas_status', 'status'),
        Index('idx_parcelas_data_vencimento', 'data_vencimento'),
        Index('idx_parcelas_gasto_futuro_status', 'gasto_futuro_id', 'status'),
    )

    def __repr__(self):
        return f"<GastoFuturoParcela(id={self.id}, parcela={self.numero_parcela}/{self.total_parcelas}, valor={self.valor_parcela}, status={self.status})>"
