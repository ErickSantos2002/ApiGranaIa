"""
Service para lógica de negócios de Autenticação
"""
from typing import Optional
from datetime import timedelta, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import secrets

from app.models import Usuario
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import UsuarioRegister, UsuarioLogin, TokenResponse, RequestPasswordReset, PasswordResetResponse, ResetPassword
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.exceptions import NotFoundException, BadRequestException, UnauthorizedException, ConflictException
from app.utils.timezone import now_brasilia
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

        # Define valores padrão para premium
        # Novo usuário começa com plano 'free' válido por 7 dias
        # Usa horário de Brasília
        now = now_brasilia()
        premium_expires = now + timedelta(days=7)

        # Remove timezone para compatibilidade com TIMESTAMP (sem timezone) do banco
        premium_expires_naive = premium_expires.replace(tzinfo=None)

        # Cria o usuário
        usuario = Usuario(
            name=user_data.name,
            email=user_data.email,
            phone=user_data.phone,
            remotejid=remotejid,
            senha=senha_hash,
            tipo_premium='free',
            premium_until=premium_expires_naive,
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

    @staticmethod
    async def request_password_reset(db: AsyncSession, data: RequestPasswordReset) -> PasswordResetResponse:
        """
        Cria um token para reset de senha

        Args:
            db: Sessão do banco de dados
            data: Dados com telefone do usuário

        Returns:
            PasswordResetResponse: Token e tempo de expiração

        Raises:
            NotFoundException: Se usuário não encontrado
        """
        # Gera remotejid a partir do telefone
        phone_clean = data.phone
        remotejid = f"{phone_clean}@s.whatsapp.net"

        # Busca usuário pelo remotejid
        stmt = select(Usuario).where(Usuario.remotejid == remotejid)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException("Usuário não encontrado com este telefone")

        # Gera token único e seguro (64 caracteres hexadecimais)
        token = secrets.token_urlsafe(48)

        # Define expiração (15 minutos)
        now = now_brasilia()
        expires_at = now + timedelta(minutes=15)
        expires_at_naive = expires_at.replace(tzinfo=None)

        # Invalida tokens anteriores deste usuário (marca como usados)
        stmt_update = select(PasswordResetToken).where(
            PasswordResetToken.usuario_id == usuario.id,
            PasswordResetToken.used == False
        )
        result = await db.execute(stmt_update)
        old_tokens = result.scalars().all()
        for old_token in old_tokens:
            old_token.used = True

        # Cria novo token
        reset_token = PasswordResetToken(
            usuario_id=usuario.id,
            token=token,
            expires_at=expires_at_naive,
            used=False
        )

        db.add(reset_token)
        await db.flush()

        return PasswordResetResponse(
            token=token,
            expires_in_minutes=15
        )

    @staticmethod
    async def reset_password(db: AsyncSession, data: ResetPassword) -> None:
        """
        Redefine a senha do usuário usando o token

        Args:
            db: Sessão do banco de dados
            data: Token e nova senha

        Raises:
            NotFoundException: Se token não encontrado
            BadRequestException: Se token inválido ou expirado
        """
        # Busca token
        stmt = select(PasswordResetToken).where(PasswordResetToken.token == data.token)
        result = await db.execute(stmt)
        reset_token = result.scalar_one_or_none()

        if not reset_token:
            raise NotFoundException("Token de recuperação não encontrado")

        # Verifica se token foi usado
        if reset_token.used:
            raise BadRequestException("Este token já foi utilizado")

        # Verifica se token expirou
        if reset_token.is_expired:
            raise BadRequestException("Este token expirou. Solicite um novo link de recuperação")

        # Busca usuário
        stmt = select(Usuario).where(Usuario.id == reset_token.usuario_id)
        result = await db.execute(stmt)
        usuario = result.scalar_one_or_none()

        if not usuario:
            raise NotFoundException("Usuário não encontrado")

        # Atualiza senha
        senha_hash = get_password_hash(data.new_password)
        usuario.senha = senha_hash

        # Marca token como usado
        reset_token.used = True

        await db.flush()
