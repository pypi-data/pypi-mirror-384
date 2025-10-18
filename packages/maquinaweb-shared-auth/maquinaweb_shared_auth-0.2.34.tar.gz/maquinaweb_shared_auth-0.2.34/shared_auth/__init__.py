"""
Biblioteca compartilhada para acesso aos models de autenticação
"""

__version__ = '1.0.0'
default_app_config = "shared_auth.app.SharedAuthConfig"

# Exportar utilitários para facilitar importação
from .utils import (
    get_member_model,
    get_organization_model,
    get_token_model,
    get_user_model,
)

__all__ = [
    'get_token_model',
    'get_organization_model',
    'get_user_model',
    'get_member_model',
]
