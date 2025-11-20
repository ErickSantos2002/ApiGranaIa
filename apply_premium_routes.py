"""
Script para aplicar verificação de premium nas rotas de gastos e receitas

Execute: python apply_premium_routes.py
"""
import re

def apply_premium_to_route_file(filepath: str):
    """Aplica as mudanças de premium em um arquivo de rotas"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Adiciona import se não existir
    if 'from app.utils.premium import require_premium' not in content:
        # Encontra a linha de import get_current_user
        content = content.replace(
            'from app.utils.security import get_current_user',
            'from app.utils.security import get_current_user\nfrom app.utils.premium import require_premium'
        )

    # Substitui get_current_user por require_premium nas funções principais
    # Padrão: current_user: Usuario = Depends(get_current_user)
    content = re.sub(
        r'current_user: Usuario = Depends\(get_current_user\)',
        r'current_user: Usuario = Depends(require_premium)',
        content
    )

    # Adiciona current_user nas funções que não têm (list, dashboard, update, delete)
    # Padrão: db: AsyncSession = Depends(get_db)\n):
    # Substitui por: current_user: Usuario = Depends(require_premium),\n    db: AsyncSession = Depends(get_db)\n):

    # Para funções list_* e get_*_dashboard e update_* e delete_*
    functions_to_update = [
        r'(async def (?:list_gastos|list_receitas)\([^)]+)',
        r'(async def (?:get_gastos_dashboard|get_receitas_dashboard)\([^)]+)',
        r'(async def (?:update_gasto|update_receita)\([^)]+)',
        r'(async def (?:delete_gasto|delete_receita)\([^)]+)',
    ]

    for pattern in functions_to_update:
        # Procura funções que NÃO têm current_user ainda
        matches = re.finditer(pattern + r'(\s+db: AsyncSession = Depends\(get_db\)\s*\))', content, re.DOTALL)

        for match in matches:
            old_text = match.group(0)
            # Verifica se já tem current_user
            if 'current_user' not in old_text:
                # Adiciona current_user antes do db
                new_text = old_text.replace(
                    '    db: AsyncSession = Depends(get_db)\n)',
                    '    current_user: Usuario = Depends(require_premium),\n    db: AsyncSession = Depends(get_db)\n)'
                )
                content = content.replace(old_text, new_text, 1)

    # Salva o arquivo
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Arquivo atualizado: {filepath}")


if __name__ == '__main__':
    print("Aplicando verificação de premium nas rotas...")
    print("-" * 60)

    try:
        # Aplica nas rotas de gastos
        apply_premium_to_route_file('app/routes/gastos.py')

        # Aplica nas rotas de receitas
        apply_premium_to_route_file('app/routes/receitas.py')

        print("-" * 60)
        print("✨ Todas as rotas foram atualizadas com sucesso!")
        print("\nPróximos passos:")
        print("1. Reinicie a API")
        print("2. Teste criar um gasto/receita com premium expirado")
        print("3. Verifique se o modal aparece no frontend")

    except Exception as e:
        print(f"❌ Erro: {e}")
        print("\nSe o script falhar, aplique manualmente seguindo PREMIUM_MIGRATION.md")
