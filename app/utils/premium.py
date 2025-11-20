"""
Utilitários para verificação de premium
"""
from fastapi import HTTPException, status, Depends
from app.models.usuario import Usuario
from app.utils.security import get_current_user


async def require_premium(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependency para verificar se o usuário tem premium ativo

    Args:
        current_user: Usuário autenticado

    Returns:
        Usuario: Usuário com premium ativo

    Raises:
        HTTPException: Se o premium não estiver ativo
    """
    if not current_user.is_premium_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "premium_expired",
                "message": "Seu plano expirou. Assine um plano para continuar usando o sistema.",
                "premium_until": current_user.premium_until.isoformat() if current_user.premium_until else None,
                "tipo_premium": current_user.tipo_premium,
            }
        )
    return current_user


def check_premium_feature(feature: str):
    """
    Decorator para verificar se o usuário tem acesso a uma feature premium específica

    Args:
        feature: Nome da feature (ex: 'ia', 'dashboard', etc.)

    Returns:
        Função decorator
    """
    async def premium_feature_checker(
        current_user: Usuario = Depends(get_current_user)
    ) -> Usuario:
        # Verifica se o premium está ativo
        if not current_user.is_premium_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "premium_expired",
                    "message": "Seu plano expirou. Assine um plano para acessar esta funcionalidade.",
                    "feature": feature,
                }
            )

        # Verifica se o plano do usuário tem acesso à feature
        tipo = current_user.tipo_premium or 'free'

        # Mapeamento de features por tipo de plano
        feature_access = {
            'free': [],  # Free não tem acesso a nenhuma feature premium
            'ia': ['ia'],  # IA tem acesso apenas à IA
            'ia_dashboard': ['ia', 'dashboard'],  # IA+Dashboard tem acesso a ambos
            'vitalicio': ['ia', 'dashboard', 'all'],  # Vitalício tem acesso a tudo
        }

        allowed_features = feature_access.get(tipo, [])

        if feature not in allowed_features and 'all' not in allowed_features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "feature_not_available",
                    "message": f"Seu plano '{tipo}' não inclui acesso a '{feature}'. Faça upgrade para acessar.",
                    "current_plan": tipo,
                    "required_feature": feature,
                }
            )

        return current_user

    return premium_feature_checker
