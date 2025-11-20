"""
Utilitários para trabalhar com timezone do Brasil
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


# Timezone de Brasília (UTC-3)
BRASILIA_TZ = ZoneInfo('America/Sao_Paulo')


def now_brasilia() -> datetime:
    """
    Retorna o datetime atual no horário de Brasília

    Returns:
        datetime: Data e hora atual em Brasília
    """
    return datetime.now(BRASILIA_TZ)


def to_brasilia(dt: datetime) -> datetime:
    """
    Converte um datetime para o timezone de Brasília

    Args:
        dt: Datetime a ser convertido

    Returns:
        datetime: Datetime convertido para Brasília
    """
    if dt.tzinfo is None:
        # Se não tem timezone, assume que já é horário de Brasília
        return dt.replace(tzinfo=BRASILIA_TZ)
    return dt.astimezone(BRASILIA_TZ)


def brasilia_offset_hours() -> int:
    """
    Retorna o offset de horas de Brasília em relação ao UTC

    Returns:
        int: Offset em horas (normalmente -3)
    """
    now = now_brasilia()
    offset = now.utcoffset()
    if offset:
        return int(offset.total_seconds() / 3600)
    return -3
