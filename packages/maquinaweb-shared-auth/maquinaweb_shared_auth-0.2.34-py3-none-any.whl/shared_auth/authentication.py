"""
Backend de autenticação usando tokens do banco compartilhado
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from .utils import get_token_model, get_user_model


class SharedTokenAuthentication(TokenAuthentication):
    """
    Autentica usando tokens do banco de dados compartilhado

    Usa get_token_model() e get_user_model() para suportar models customizados.

    Usage em settings.py:
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'shared_auth.authentication.SharedTokenAuthentication',
            ]
        }
    """

    @property
    def model(self):
        """Retorna o model de Token configurado"""
        return get_token_model()

    def authenticate_credentials(self, key):
        """
        Valida o token no banco de dados compartilhado
        """
        Token = get_token_model()
        User = get_user_model()

        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
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
