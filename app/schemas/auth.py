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
    senha: str = Field(..., min_length=6, description="Senha (mínimo 6 caracteres)")

    @field_validator("name", "phone")
    @classmethod
    def validate_not_empty(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Campo não pode ser vazio")
        return v.strip()


class UsuarioLogin(BaseModel):
    """Schema para login de usuário"""
    email: EmailStr = Field(..., description="Email do usuário")
    senha: str = Field(..., description="Senha do usuário")


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
