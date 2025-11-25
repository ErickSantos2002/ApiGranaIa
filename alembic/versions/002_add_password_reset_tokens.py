"""Add password reset tokens table

Revision ID: 002
Revises: 001
Create Date: 2025-11-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria a tabela password_reset_tokens
    """
    op.create_table(
        'password_reset_tokens',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            primary_key=True
        ),
        sa.Column(
            'usuario_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('usuarios.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False)
    )

    # Criar índices
    op.create_index('idx_password_reset_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_password_reset_usuario', 'password_reset_tokens', ['usuario_id'])
    op.create_index('idx_password_reset_expires', 'password_reset_tokens', ['expires_at'])


def downgrade():
    """
    Remove a tabela password_reset_tokens
    """
    op.drop_index('idx_password_reset_expires', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_usuario', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_token', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
