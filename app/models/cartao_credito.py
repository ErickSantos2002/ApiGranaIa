"""
Model SQLAlchemy para Cartão de Crédito
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, Integer, Boolean, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CartaoCredito(Base):
    """Model para Cartão de Crédito"""

    __tablename__ = "cartoes_credito"

    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    usuario = Column(Text, ForeignKey("usuarios.remotejid", ondelete="CASCADE"), nullable=False, index=True)
    nome_cartao = Column(Text, nullable=False)
    nome_titular = Column(Text, nullable=False)
    dia_vencimento = Column(Integer, nullable=False)
    limite = Column(Numeric(precision=12, scale=2), nullable=True)
    cor = Column(Text, nullable=True, default="#3B82F6")
    ativo = Column(Boolean, nullable=False, default=True, index=True)
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    usuario_rel = relationship("Usuario", back_populates="cartoes_credito")
    gastos_futuros = relationship(
        "GastoFuturo",
        back_populates="cartao_credito",
        lazy="selectin"
    )

    # Índices
    __table_args__ = (
        Index('idx_cartoes_credito_usuario', 'usuario'),
        Index('idx_cartoes_credito_ativo', 'ativo'),
        Index('idx_cartoes_credito_usuario_ativo', 'usuario', 'ativo'),
        Index('idx_cartoes_credito_dia_vencimento', 'dia_vencimento'),
    )

    def __repr__(self):
        return f"<CartaoCredito(id={self.id}, nome_cartao='{self.nome_cartao}', usuario='{self.usuario}')>"
