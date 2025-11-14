"""
Utilitários de segurança e autenticação JWT
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from app.config import settings


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
