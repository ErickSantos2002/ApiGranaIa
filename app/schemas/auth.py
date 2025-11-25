"""
Schemas Pydantic para Autenticação
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class UsuarioRegister(BaseModel):
    """Schema para cadastro de novo usuário"""
    name: str = Field(..., min_length=1, max_length=255, description="Nome completo")
    email: EmailStr = Field(..., description="Email do usuário")
    phone: str = Field(..., min_length=1, description="Telefone do usuário")
    senha: str = Field(..., min_length=6, max_length=128, description="Senha (entre 6 e 128 caracteres)")

    @field_validator("name", "phone")
    @classmethod
    def validate_not_empty(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Campo não pode ser vazio")
        return v.strip()


class UsuarioLogin(BaseModel):
    """Schema para login de usuário"""
    email: EmailStr = Field(..., description="Email do usuário")
    senha: str = Field(..., max_length=128, description="Senha do usuário (máximo 128 caracteres)")


class TokenResponse(BaseModel):
    """Schema de resposta com token JWT"""
    access_token: str = Field(..., description="Token JWT de acesso")
    token_type: str = Field(default="bearer", description="Tipo do token")
    user_id: str = Field(..., description="ID do usuário")
    email: str = Field(..., description="Email do usuário")
    name: str = Field(..., description="Nome do usuário")
    remotejid: Optional[str] = Field(None, description="RemoteJID do usuário")


class UsuarioProfile(BaseModel):
    """Schema de perfil do usuário autenticado"""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    remotejid: str
    tipo_premium: Optional[str] = None
    premium_until: Optional[str] = None
    is_premium_active: bool = False

    class Config:
        from_attributes = True


class RequestPasswordReset(BaseModel):
    """Schema para solicitar reset de senha"""
    phone: str = Field(..., min_length=1, description="Telefone do usuário (com código do país)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        # Remove caracteres não numéricos
        phone_clean = ''.join(filter(str.isdigit, v))
        if len(phone_clean) < 10:
            raise ValueError("Telefone inválido")
        return phone_clean


class PasswordResetResponse(BaseModel):
    """Schema de resposta para solicitação de reset"""
    token: str = Field(..., description="Token para reset de senha")
    expires_in_minutes: int = Field(..., description="Tempo de expiração em minutos")


class ResetPassword(BaseModel):
    """Schema para redefinir senha"""
    token: str = Field(..., min_length=1, description="Token de reset de senha")
    new_password: str = Field(..., min_length=6, max_length=128, description="Nova senha (entre 6 e 128 caracteres)")

    @field_validator("token")
    @classmethod
    def validate_token(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Token não pode ser vazio")
        return v.strip()
