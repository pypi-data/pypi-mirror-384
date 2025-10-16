"""
Backend de autenticação usando tokens do banco compartilhado
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from .models import SharedToken, User


class SharedTokenAuthentication(TokenAuthentication):
    """
    Autentica usando tokens do banco de dados compartilhado

    Usage em settings.py:
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'shared_auth.authentication.SharedTokenAuthentication',
            ]
        }
    """

    model = SharedToken

    def authenticate_credentials(self, key):
        """
        Valida o token no banco de dados compartilhado
        """
        try:
            token = SharedToken.objects.get(key=key)
        except SharedToken.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Token inválido."))

        # Buscar usuário completo
        try:
            user = User.objects.get(pk=token.user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Usuário não encontrado."))

        if not user.is_active:
            raise exceptions.AuthenticationFailed(_("Usuário inativo ou deletado."))

        if user.deleted_at is not None:
            raise exceptions.AuthenticationFailed(_("Usuário deletado."))

        return (user, token)
