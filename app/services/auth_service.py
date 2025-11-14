"""
Service para lógica de negócios de Autenticação
"""
from typing import Optional
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Usuario
from app.schemas.auth import UsuarioRegister, UsuarioLogin, TokenResponse
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.exceptions import NotFoundException, BadRequestException, UnauthorizedException, ConflictException
from app.config import settings


class AuthService:
    """Service para gerenciar autenticação"""

    @staticmethod
    async def register(db: AsyncSession, user_data: UsuarioRegister) -> Usuario:
        """
        Registra um novo usuário no sistema

        Args:
            db: Sessão do banco de dados
            user_data: Dados do usuário a ser registrado

        Returns:
            Usuario: Usuário criado

        Raises:
            ConflictException: Se email já existe
        """
        # Verifica se email já existe
        stmt = select(Usuario).where(Usuario.email == user_data.email)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ConflictException(f"Email '{user_data.email}' já está cadastrado")

        # Gera remotejid a partir do telefone (formato WhatsApp)
        # Remove caracteres não numéricos
        phone_clean = ''.join(filter(str.isdigit, user_data.phone))
        remotejid = f"{phone_clean}@s.whatsapp.net"

        # Verifica se remotejid já existe
        stmt = select(Usuario).where(Usuario.remotejid == remotejid)
        result = await db.execute(stmt)
        existing_remotejid = result.scalar_one_or_none()

        if existing_remotejid:
            raise ConflictException(f"Telefone '{user_data.phone}' já está cadastrado")

        # Hash da senha
        senha_hash = get_password_hash(user_data.senha)

        # Cria o usuário
        usuario = Usuario(
            name=user_data.name,
            email=user_data.email,
            phone=user_data.phone,
            remotejid=remotejid,
            senha=senha_hash,
        )

        db.add(usuario)
        await db.flush()
        await db.refresh(usuario)

        return usuario

    @staticmethod
    async def login(db: AsyncSession, login_data: UsuarioLogin) -> TokenResponse:
        """
        Autentica um usuário e retorna token JWT

        Args:
            db: Sessão do banco de dados
            login_data: Dados de login (email e senha)

        Returns:
            TokenResponse: Token JWT e informações do usuário

        Raises:
            UnauthorizedException: Se credenciais inválidas
        """
        # Busca usuário por email
        stmt = select(Usuario).where(Usuario.email == login_data.email)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise UnauthorizedException("Email ou senha incorretos")

        # Verifica se senha está definida
        if not usuario.senha:
            raise UnauthorizedException("Usuário sem senha cadastrada")

        # Verifica senha
        if not verify_password(login_data.senha, usuario.senha):
            raise UnauthorizedException("Email ou senha incorretos")

        # Gera token JWT
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(usuario.id),
                "email": usuario.email,
                "remotejid": usuario.remotejid,
            },
            expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(usuario.id),
            email=usuario.email,
            name=usuario.name,
            remotejid=usuario.remotejid,
        )

    @staticmethod
    async def get_current_user(db: AsyncSession, user_id: str) -> Usuario:
        """
        Busca o usuário atual pelo ID do token

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário (do token JWT)

        Returns:
            Usuario: Usuário encontrado

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        stmt = select(Usuario).where(Usuario.id == user_id)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException("Usuário não encontrado")

        return usuario
