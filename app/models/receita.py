"""
Model SQLAlchemy para Receita
"""
from sqlalchemy import Column, Text, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Receita(Base):
    """
    Model para tabela de receitas
    """
    __tablename__ = "receitas"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False
    )
    usuario = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    descricao = Column(Text, nullable=False)
    valor = Column(Numeric(precision=12, scale=2), nullable=False)
    categoria = Column(Text, nullable=False, index=True)
    data = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relacionamento
    usuario_rel = relationship("Usuario", back_populates="receitas")

    # Índices adicionais
    __table_args__ = (
        Index('idx_receitas_usuario', 'usuario'),
        Index('idx_receitas_categoria', 'categoria'),
        Index('idx_receitas_data', 'data'),
        Index('idx_receitas_usuario_data', 'usuario', 'data'),
    )

    def __repr__(self):
        return f"<Receita(id={self.id}, descricao={self.descricao}, valor={self.valor})>"
