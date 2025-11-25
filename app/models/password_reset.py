"""
Model SQLAlchemy para Password Reset Token
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class PasswordResetToken(Base):
    """
    Model para tabela de tokens de recuperação de senha
    """
    __tablename__ = "password_reset_tokens"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False
    )
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=False), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False
    )

    # Relacionamento
    usuario = relationship("Usuario", backref="reset_tokens")

    # Índices adicionais
    __table_args__ = (
        Index('idx_password_reset_token', 'token'),
        Index('idx_password_reset_usuario', 'usuario_id'),
        Index('idx_password_reset_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, usuario_id={self.usuario_id}, used={self.used})>"

    @property
    def is_expired(self) -> bool:
        """
        Verifica se o token expirou
        """
        from app.utils.timezone import now_brasilia
        now = now_brasilia().replace(tzinfo=None)
        return self.expires_at < now

    @property
    def is_valid(self) -> bool:
        """
        Verifica se o token é válido (não usado e não expirado)
        """
        return not self.used and not self.is_expired
