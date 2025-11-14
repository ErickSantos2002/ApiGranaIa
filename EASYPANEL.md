# Deploy no Easypanel

## Configuração do Easypanel

### 1. Variáveis de Ambiente Obrigatórias

Configure as seguintes variáveis de ambiente no Easypanel:

```env
DATABASE_URL=postgresql+asyncpg://usuario:senha@host:porta/database
DATABASE_URL_SYNC=postgresql://usuario:senha@host:porta/database
POSTGRES_USER=usuario
POSTGRES_PASSWORD=senha
POSTGRES_DB=database
POSTGRES_HOST=host
POSTGRES_PORT=5432
SECRET_KEY=seu-secret-key-super-secreto-aqui
DEBUG=False
API_PREFIX=/api/v1
```

### 2. Configuração do Container

**Build Settings:**
- Dockerfile: `Dockerfile`
- Build context: `.` (root do repositório)

**Runtime:**
- Port: `8000` (a aplicação escuta nesta porta)
- Health check: Automático (já configurado no Dockerfile)

### 3. Banco de Dados PostgreSQL

Se você ainda não tem um banco PostgreSQL configurado:

1. Crie um novo serviço PostgreSQL no Easypanel
2. Anote as credenciais (host, porta, usuário, senha, database)
3. Configure as variáveis de ambiente acima com essas credenciais

### 4. Comandos Importantes

**Não precisa configurar comando de inicialização!** O Dockerfile já inclui tudo.

O script `start.sh` é executado automaticamente e:
- Aguarda o banco de dados
- Executa migrations do Alembic
- Inicia o servidor Uvicorn

### 5. Verificação

Após o deploy:

1. Acesse: `https://seu-dominio.com/`
   - Deve retornar um health check

2. Acesse: `https://seu-dominio.com/docs`
   - Documentação Swagger da API

3. Acesse: `https://seu-dominio.com/api/v1/usuarios`
   - Endpoint de usuários

### 6. Troubleshooting

**Container reiniciando constantemente:**
- Verifique se as variáveis de ambiente estão corretas
- Verifique se o banco PostgreSQL está acessível
- Veja os logs do container no Easypanel

**Erro "cannot connect to database":**
- Verifique `DATABASE_URL` e `DATABASE_URL_SYNC`
- Certifique-se que o banco PostgreSQL está rodando
- Verifique se o host/porta estão corretos

**Erro "Module not found":**
- Rebuilde a imagem do Docker
- Verifique se todos os arquivos foram commitados no git

### 7. Migrations

As migrations são executadas automaticamente no startup via `start.sh`.

Para criar novas migrations:
```bash
alembic revision --autogenerate -m "Descrição"
alembic upgrade head
```

### 8. Modo Produção

Em produção, configure:

```env
DEBUG=False
SECRET_KEY=<chave-secreta-forte-aleatória>
CORS_ORIGINS=["https://seu-frontend.com"]
```

### 9. Dockerfiles Disponíveis

- `Dockerfile` - Multi-stage build otimizado (RECOMENDADO)
- `Dockerfile.simple` - Versão simplificada (alternativa)

Para usar o `Dockerfile.simple`, configure no Easypanel:
- Dockerfile: `Dockerfile.simple`
