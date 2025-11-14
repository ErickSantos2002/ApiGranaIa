"""
Model SQLAlchemy para Usuário
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Usuario(Base):
    """
    Model para tabela de usuários
    """
    __tablename__ = "usuarios"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False
    )
    name = Column(Text, nullable=False, index=True)
    phone = Column(Text, nullable=True)
    remotejid = Column(Text, unique=True, nullable=False)
    last_message = Column(Text, nullable=True)
    premium_until = Column(DateTime(timezone=True), nullable=True)
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

    # Relacionamentos
    gastos = relationship(
        "Gasto",
        back_populates="usuario_rel",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    receitas = relationship(
        "Receita",
        back_populates="usuario_rel",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Índices adicionais
    __table_args__ = (
        Index('idx_usuarios_phone', 'phone'),
        Index('idx_usuarios_premium_until', 'premium_until'),
        Index('idx_usuarios_remotejid', 'remotejid'),
    )

    def __repr__(self):
        return f"<Usuario(id={self.id}, name={self.name}, remotejid={self.remotejid})>"

    @property
    def is_premium_active(self) -> bool:
        """Verifica se o usuário tem premium ativo"""
        if not self.premium_until:
            return False
        return self.premium_until > datetime.now(self.premium_until.tzinfo)
