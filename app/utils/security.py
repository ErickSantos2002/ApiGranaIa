"""
Utilitários de segurança e autenticação JWT
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings

# Configuração do esquema de segurança Bearer
security = HTTPBearer()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT de acesso.

    Args:
        data: Dados a serem codificados no token
        expires_delta: Tempo de expiração customizado (opcional)

    Returns:
        str: Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica e decodifica um token JWT.

    Args:
        token: Token JWT a ser verificado

    Returns:
        Optional[Dict[str, Any]]: Payload do token se válido, None caso contrário
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """
    Gera hash de uma senha usando bcrypt.

    Bcrypt tem limite de 72 bytes, então truncamos a senha se necessário.
    Isso é uma prática segura e comum.

    Args:
        password: Senha em texto plano

    Returns:
        str: Hash da senha
    """
    # Truncar senha para 72 bytes (limite do bcrypt)
    password_bytes = password.encode('utf-8')[:72]

    # Gerar salt e hash usando bcrypt diretamente
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Retornar como string UTF-8
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha corresponde ao hash usando bcrypt.

    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash da senha

    Returns:
        bool: True se a senha é válida, False caso contrário
    """
    # Truncar senha para 72 bytes (limite do bcrypt)
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')

    # Verificar usando bcrypt diretamente
    return bcrypt.checkpw(password_bytes, hashed_bytes)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = None
):
    """
    Dependência para obter o usuário autenticado a partir do token JWT.

    IMPORTANTE: Esta função deve ser usada com Depends() nos endpoints,
    e o parâmetro db deve ser passado explicitamente com Depends(get_db).

    Args:
        credentials: Credenciais HTTP Bearer (token)
        db: Sessão do banco de dados

    Returns:
        Usuario: Usuário autenticado

    Raises:
        HTTPException: Se o token for inválido ou o usuário não for encontrado
    """
    # Importar aqui para evitar import circular
    from app.models.usuario import Usuario

    # Extrair o token
    token = credentials.credentials

    # Credenciais inválidas
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verificar e decodificar o token
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception

        # Extrair o user_id do payload
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Converter para UUID
        user_id = UUID(user_id_str)

    except (JWTError, ValueError):
        raise credentials_exception

    # Buscar o usuário no banco de dados
    stmt = select(Usuario).where(Usuario.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
