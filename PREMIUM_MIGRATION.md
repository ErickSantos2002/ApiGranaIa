# Migração de Verificação de Premium

Este arquivo documenta as mudanças necessárias para implementar a verificação de premium nas rotas da API.

## Arquivos Já Criados/Atualizados

### Frontend
✅ `GranaIA/src/components/PremiumExpiredModal.tsx` - Modal de premium expirado
✅ `GranaIA/src/pages/Dashboard.tsx` - Verificação e bloqueio no frontend

### Backend
✅ `ApiGranaIa/app/utils/premium.py` - Utilitários de verificação de premium
✅ `ApiGranaIa/app/utils/timezone.py` - Utilitários de timezone (Brasília)
✅ `ApiGranaIa/app/models/usuario.py` - Model atualizado com ENUM tipo_plano
✅ `ApiGranaIa/app/services/auth_service.py` - Registro com valores padrão de premium

## Mudanças Pendentes nas Rotas

### 1. app/routes/gastos.py

Adicione no início do arquivo (linha 25, após os imports):
```python
from app.utils.premium import require_premium
```

Substitua `Depends(get_current_user)` por `Depends(require_premium)` nas funções:
- Linha 68: `create_gasto` - já tem `current_user`, só mudar de `get_current_user` para `require_premium`
- Linha 139: `list_gastos` - ADICIONAR `current_user: Usuario = Depends(require_premium),` antes de `db`
- Linha 187: `get_gastos_dashboard` - ADICIONAR `current_user: Usuario = Depends(require_premium),` antes de `db`
- Linha 248: `update_gasto` - ADICIONAR `current_user: Usuario = Depends(require_premium),` antes de `db`
- Linha 272: `delete_gasto` - ADICIONAR `current_user: Usuario = Depends(require_premium),` antes de `db`

### 2. app/routes/receitas.py

Mesmas mudanças que gastos.py:

Adicione no início:
```python
from app.utils.premium import require_premium
```

Substitua nas funções (encontre as linhas equivalentes):
- `create_receita` - mudar `get_current_user` para `require_premium`
- `list_receitas` - ADICIONAR `current_user: Usuario = Depends(require_premium),`
- `get_receitas_dashboard` - ADICIONAR `current_user: Usuario = Depends(require_premium),`
- `update_receita` - ADICIONAR `current_user: Usuario = Depends(require_premium),`
- `delete_receita` - ADICIONAR `current_user: Usuario = Depends(require_premium),`

## Como Aplicar

### Opção 1: Manualmente
Abra os arquivos e faça as mudanças descritas acima.

### Opção 2: Via Script (Recomendado)
Execute o script que vou criar em seguida.

## O que a Verificação Faz

Quando um usuário SEM premium ativo tentar:
- Criar gasto/receita
- Listar gastos/receitas
- Atualizar gasto/receita
- Deletar gasto/receita
- Ver dashboard

A API retornará erro 403 com:
```json
{
  "detail": {
    "error": "premium_expired",
    "message": "Seu plano expirou. Assine um plano para continuar usando o sistema.",
    "premium_until": "2025-11-20T10:00:00",
    "tipo_premium": "free"
  }
}
```

E o frontend automaticamente:
1. Mostra o modal de premium expirado
2. Bloqueia botões de criar/editar
3. Não carrega dados do dashboard
