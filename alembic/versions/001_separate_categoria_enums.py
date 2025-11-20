"""Separar ENUMs de categorias para gastos e receitas

Revision ID: 001
Revises:
Create Date: 2025-11-20 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria ENUM separado para receitas e atualiza a tabela receitas
    """
    # 1. Criar novo ENUM para receitas
    categorias_receitas_enum = postgresql.ENUM(
        'Salário',
        'Freelance',
        'Investimentos',
        'Bonificação',
        'Presente',
        'Aluguel',
        'Venda',
        'Outros',
        name='categorias_receitas',
        create_type=True
    )
    categorias_receitas_enum.create(op.get_bind())

    # 2. Adicionar coluna temporária com o novo ENUM
    op.add_column(
        'receitas',
        sa.Column('categoria_nova', categorias_receitas_enum, nullable=True)
    )

    # 3. Migrar dados existentes para a nova coluna
    # Mapear categorias antigas para novas quando possível, senão usar 'Outros'
    op.execute("""
        UPDATE receitas
        SET categoria_nova =
            CASE
                WHEN categoria = 'Outros' THEN 'Outros'::categorias_receitas
                ELSE 'Outros'::categorias_receitas
            END
    """)

    # 4. Tornar a nova coluna NOT NULL
    op.alter_column('receitas', 'categoria_nova', nullable=False)

    # 5. Remover a coluna antiga
    op.drop_column('receitas', 'categoria')

    # 6. Renomear a nova coluna para 'categoria'
    op.alter_column('receitas', 'categoria_nova', new_column_name='categoria')

    # 7. Recriar o índice na nova coluna
    op.create_index('idx_receitas_categoria', 'receitas', ['categoria'])


def downgrade():
    """
    Reverter mudanças (restaurar ENUM original)
    """
    # 1. Adicionar coluna temporária com ENUM antigo
    op.add_column(
        'receitas',
        sa.Column(
            'categoria_antiga',
            postgresql.ENUM(
                'Alimentação',
                'Transporte',
                'Moradia',
                'Saúde',
                'Educação',
                'Lazer',
                'Compras',
                'Outros',
                name='categorias_financeiras',
                create_type=False
            ),
            nullable=True
        )
    )

    # 2. Migrar dados de volta (tudo vira 'Outros')
    op.execute("""
        UPDATE receitas
        SET categoria_antiga = 'Outros'::categorias_financeiras
    """)

    # 3. Remover índice
    op.drop_index('idx_receitas_categoria', table_name='receitas')

    # 4. Tornar coluna antiga NOT NULL
    op.alter_column('receitas', 'categoria_antiga', nullable=False)

    # 5. Remover coluna nova
    op.drop_column('receitas', 'categoria')

    # 6. Renomear coluna antiga de volta
    op.alter_column('receitas', 'categoria_antiga', new_column_name='categoria')

    # 7. Recriar índice
    op.create_index('idx_receitas_categoria', 'receitas', ['categoria'])

    # 8. Remover o ENUM de receitas
    op.execute('DROP TYPE categorias_receitas')
