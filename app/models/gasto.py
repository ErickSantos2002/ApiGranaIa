"""
Model SQLAlchemy para Gasto
"""
from sqlalchemy import Column, Text, DateTime, Numeric, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Gasto(Base):
    """
    Model para tabela de gastos
    """
    __tablename__ = "gastos"

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
    descricao = Column(Text, nullable=False)
    valor = Column(Numeric(precision=12, scale=2), nullable=False)
    categoria = Column(
        Enum(
            'Alimentação',
            'Transporte',
            'Moradia',
            'Saúde',
            'Educação',
            'Lazer',
            'Compras',
            'Outros',
            name='categorias_financeiras',
            create_type=False  # Não criar o tipo, ele já existe no banco
        ),
        nullable=False,
        index=True
    )
    data = Column(DateTime(timezone=False), server_default=func.now(), nullable=True)
    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=True
    )
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )

    # Relacionamento
    usuario_rel = relationship(
        "Usuario",
        back_populates="gastos",
        foreign_keys=[usuario]
    )

    # Índices adicionais
    __table_args__ = (
        Index('idx_gastos_usuario', 'usuario'),
        Index('idx_gastos_categoria', 'categoria'),
        Index('idx_gastos_data', 'data'),
        Index('idx_gastos_usuario_data', 'usuario', 'data'),
    )

    def __repr__(self):
        return f"<Gasto(id={self.id}, descricao={self.descricao}, valor={self.valor})>"
