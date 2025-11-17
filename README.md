# Grana IA API

API completa e profissional para gerenciamento financeiro pessoal, construída com FastAPI e PostgreSQL.

## Sobre o Projeto

Esta API fornece um sistema robusto para gerenciar usuários, gastos e receitas, com recursos avançados como:

- Autenticação JWT
- Paginação em todas as listagens
- Filtros dinâmicos e avançados
- Dashboard com estatísticas
- Validações robustas
- Respostas padronizadas
- Documentação interativa (Swagger/ReDoc)
- Migrations com Alembic
- Docker e Docker Compose

## Tecnologias Utilizadas

- **FastAPI** - Framework web moderno e de alta performance
- **PostgreSQL** - Banco de dados relacional
- **SQLAlchemy 2.0** - ORM assíncrono
- **Alembic** - Migrations de banco de dados
- **Pydantic** - Validação de dados
- **JWT** - Autenticação
- **Docker** - Containerização
- **Uvicorn** - Servidor ASGI

## Estrutura do Banco de Dados

### Tabela: usuarios

| Campo          | Tipo      | Descrição                         |
|----------------|-----------|-----------------------------------|
| id             | UUID      | Chave primária                    |
| name           | TEXT      | Nome do usuário                   |
| phone          | TEXT      | Telefone (opcional)               |
| remotejid      | TEXT      | Identificador único (UNIQUE)      |
| last_message   | TEXT      | Última mensagem recebida          |
| premium_until  | TIMESTAMP | Data de expiração do premium      |
| created_at     | TIMESTAMP | Data de criação                   |
| updated_at     | TIMESTAMP | Data de atualização               |

### Tabela: gastos

| Campo       | Tipo      | Descrição                    |
|-------------|-----------|------------------------------|
| id          | UUID      | Chave primária               |
| usuario     | UUID      | FK para usuarios.id          |
| descricao   | TEXT      | Descrição do gasto           |
| valor       | NUMERIC   | Valor do gasto               |
| categoria   | TEXT      | Categoria                    |
| data        | TIMESTAMP | Data do gasto                |
| created_at  | TIMESTAMP | Data de criação              |
| updated_at  | TIMESTAMP | Data de atualização          |

### Tabela: receitas

| Campo       | Tipo      | Descrição                    |
|-------------|-----------|------------------------------|
| id          | UUID      | Chave primária               |
| usuario     | UUID      | FK para usuarios.id          |
| descricao   | TEXT      | Descrição da receita         |
| valor       | NUMERIC   | Valor da receita             |
| categoria   | TEXT      | Categoria                    |
| data        | TIMESTAMP | Data da receita              |
| created_at  | TIMESTAMP | Data de criação              |
| updated_at  | TIMESTAMP | Data de atualização          |

## Instalação e Configuração

### Requisitos

- Python 3.11+
- PostgreSQL 15+
- Docker e Docker Compose (opcional)

### Opção 1: Instalação Local

1. Clone o repositório:
```bash
git clone <repository-url>
cd ApiGranaIa
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Execute as migrations:
```bash
alembic upgrade head
```

6. Inicie o servidor:
```bash
uvicorn app.main:app --reload
```

A API estará disponível em: `http://localhost:8000`

### Opção 2: Docker Compose (Recomendado)

1. Clone o repositório:
```bash
git clone <repository-url>
cd ApiGranaIa
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env se necessário
```

3. Inicie os containers:
```bash
docker-compose up -d
```

Serviços disponíveis:
- **API**: http://localhost:8000
- **Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **PgAdmin**: http://localhost:5050 (email: admin@admin.com, senha: admin)

4. Para parar os containers:
```bash
docker-compose down
```

## Documentação da API

### Swagger UI
Acesse: http://localhost:8000/docs

### ReDoc
Acesse: http://localhost:8000/redoc

## Endpoints Principais

### Usuários (`/api/v1/usuarios`)

| Método | Endpoint                          | Descrição                           |
|--------|-----------------------------------|-------------------------------------|
| POST   | `/usuarios`                       | Criar novo usuário                  |
| GET    | `/usuarios`                       | Listar usuários (com filtros)       |
| GET    | `/usuarios/{id}`                  | Buscar usuário por ID               |
| GET    | `/usuarios/remotejid/{remotejid}` | Buscar por remotejid                |
| PUT    | `/usuarios/{id}`                  | Atualizar usuário                   |
| PATCH  | `/usuarios/{id}/premium`          | Atualizar premium                   |
| PATCH  | `/usuarios/{id}/last-message`     | Atualizar última mensagem           |
| DELETE | `/usuarios/{id}`                  | Deletar usuário                     |

### Gastos (`/api/v1/gastos`)

| Método | Endpoint                | Descrição                           |
|--------|-------------------------|-------------------------------------|
| POST   | `/gastos`               | Criar novo gasto                    |
| GET    | `/gastos`               | Listar gastos (com filtros)         |
| GET    | `/gastos/dashboard`     | Dashboard de gastos                 |
| GET    | `/gastos/{id}`          | Buscar gasto por ID                 |
| PUT    | `/gastos/{id}`          | Atualizar gasto                     |
| DELETE | `/gastos/{id}`          | Deletar gasto                       |

### Receitas (`/api/v1/receitas`)

| Método | Endpoint                | Descrição                           |
|--------|-------------------------|-------------------------------------|
| POST   | `/receitas`             | Criar nova receita                  |
| GET    | `/receitas`             | Listar receitas (com filtros)       |
| GET    | `/receitas/dashboard`   | Dashboard de receitas               |
| GET    | `/receitas/{id}`        | Buscar receita por ID               |
| PUT    | `/receitas/{id}`        | Atualizar receita                   |
| DELETE | `/receitas/{id}`        | Deletar receita                     |

## Exemplos de Uso

### Criar um Usuário

```bash
curl -X POST "http://localhost:8000/api/v1/usuarios" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "phone": "+5511999999999",
    "remotejid": "5511999999999@s.whatsapp.net",
    "premium_until": "2025-12-31T23:59:59Z"
  }'
```

### Listar Gastos com Filtros

```bash
curl -X GET "http://localhost:8000/api/v1/gastos?page=1&page_size=20&categoria=alimentacao&data_inicio=2025-01-01T00:00:00Z"
```

### Dashboard de Receitas

```bash
curl -X GET "http://localhost:8000/api/v1/receitas/dashboard?data_inicio=2025-01-01T00:00:00Z&data_fim=2025-12-31T23:59:59Z"
```

## Filtros Disponíveis

### Usuários
- `name` - Busca parcial no nome
- `phone` - Busca parcial no telefone
- `premium_active` - Filtrar por premium ativo (true/false)
- `premium_expired` - Filtrar por premium expirado (true/false)
- `page` - Número da página (padrão: 1)
- `page_size` - Itens por página (padrão: 20, máximo: 100)

### Gastos e Receitas
- `usuario_id` - Filtrar por ID do usuário
- `categoria` - Busca parcial na categoria
- `data_inicio` - Data de início do período
- `data_fim` - Data de fim do período
- `valor_min` - Valor mínimo
- `valor_max` - Valor máximo
- `page` - Número da página (padrão: 1)
- `page_size` - Itens por página (padrão: 20, máximo: 100)

## Migrações (Alembic)

### Criar uma nova migration

```bash
alembic revision --autogenerate -m "Descrição da migration"
```

### Aplicar migrations

```bash
alembic upgrade head
```

### Reverter última migration

```bash
alembic downgrade -1
```

### Ver histórico de migrations

```bash
alembic history
```

## Estrutura do Projeto

```
ApiGranaIa/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicação principal
│   ├── config.py               # Configurações
│   ├── database.py             # Conexão com banco
│   ├── models/                 # Models SQLAlchemy
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── gasto.py
│   │   └── receita.py
│   ├── schemas/                # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── usuario.py
│   │   ├── gasto.py
│   │   └── receita.py
│   ├── routes/                 # Rotas da API
│   │   ├── __init__.py
│   │   ├── usuarios.py
│   │   ├── gastos.py
│   │   └── receitas.py
│   ├── services/               # Lógica de negócios
│   │   ├── __init__.py
│   │   ├── usuario_service.py
│   │   ├── gasto_service.py
│   │   └── receita_service.py
│   ├── utils/                  # Utilitários
│   │   ├── __init__.py
│   │   ├── security.py
│   │   └── exceptions.py
│   └── middleware/             # Middlewares
│       ├── __init__.py
│       └── logging.py
├── alembic/                    # Migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini                 # Config do Alembic
├── requirements.txt            # Dependências Python
├── .env.example                # Exemplo de variáveis de ambiente
├── Dockerfile                  # Dockerfile da aplicação
├── docker-compose.yml          # Orquestração de containers
├── .dockerignore              # Arquivos ignorados no build
├── init.sql                   # Script de inicialização do DB
└── README.md                  # Este arquivo
```

## Variáveis de Ambiente

Consulte o arquivo `.env.example` para ver todas as variáveis disponíveis:

- `DATABASE_URL` - URL de conexão assíncrona com PostgreSQL
- `DATABASE_URL_SYNC` - URL de conexão síncrona (para Alembic)
- `SECRET_KEY` - Chave secreta para JWT
- `DEBUG` - Modo debug (True/False)
- `CORS_ORIGINS` - Origens permitidas para CORS
- E mais...

## Segurança

- Senhas são hasheadas com bcrypt
- Tokens JWT para autenticação
- Validação de entrada com Pydantic
- Proteção contra SQL Injection (SQLAlchemy)
- CORS configurável
- Exception handlers customizados

## Testes

Para executar os testes (quando implementados):

```bash
pytest
```

Com coverage:

```bash
pytest --cov=app --cov-report=html
```

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.

## Suporte

Para dúvidas ou problemas, abra uma issue no repositório.

---

Desenvolvido com FastAPI e PostgreSQL
