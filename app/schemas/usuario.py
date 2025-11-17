"""
Schemas Pydantic para Usuario
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class UsuarioBase(BaseModel):
    """Schema base para Usuario"""
    name: str = Field(..., min_length=1, max_length=255, description="Nome do usuário")
    phone: Optional[str] = Field(None, description="Telefone do usuário")
    remotejid: str = Field(..., min_length=1, description="Identificador único externo")
    last_message: Optional[str] = Field(None, description="Última mensagem recebida")
    premium_until: Optional[datetime] = Field(None, description="Data de expiração do premium")


class UsuarioCreate(UsuarioBase):
    """Schema para criação de Usuario"""
    pass


class UsuarioUpdate(BaseModel):
    """Schema para atualização de Usuario"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = None
    last_message: Optional[str] = None
    premium_until: Optional[datetime] = None
    tipo_premium: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Nome não pode ser vazio")
        return v


class UsuarioUpdatePremium(BaseModel):
    """Schema para atualização do premium"""
    premium_until: datetime = Field(..., description="Nova data de expiração do premium")
    tipo_premium: Optional[str] = Field(None, description="Tipo do premium")


class UsuarioUpdateLastMessage(BaseModel):
    """Schema para atualização da última mensagem"""
    last_message: str = Field(..., description="Última mensagem recebida")


class UsuarioResponse(UsuarioBase):
    """Schema de resposta para Usuario"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_premium_active: bool = Field(default=False, description="Se o premium está ativo")

    class Config:
        from_attributes = True


class UsuarioListResponse(BaseModel):
    """Schema para lista de usuários"""
    usuarios: List[UsuarioResponse]
    total: int

    class Config:
        from_attributes = True


class UsuarioFilter(BaseModel):
    """Schema para filtros de busca de usuários"""
    name: Optional[str] = Field(None, description="Filtrar por nome (busca parcial)")
    phone: Optional[str] = Field(None, description="Filtrar por telefone (busca parcial)")
    remotejid: Optional[str] = Field(None, description="Filtrar por remotejid")
    premium_active: Optional[bool] = Field(None, description="Filtrar por premium ativo")
    premium_expired: Optional[bool] = Field(None, description="Filtrar por premium expirado")
