"""
Utilitários para obter os models configurados
Similar ao get_user_model() do Django
"""

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from .conf import get_setting


def get_token_model():
    """
    Retorna o model de Token configurado ou o padrão.
    
    Usage:
        from shared_auth.utils import get_token_model
        
        Token = get_token_model()
        token = Token.objects.get(key='abc123')
    """
    model_string = get_setting('SHARED_AUTH_TOKEN_MODEL', 'shared_auth.SharedToken')
    
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_TOKEN_MODEL deve estar no formato 'app_label.model_name'. "
            f"Recebido: '{model_string}'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_TOKEN_MODEL refere-se ao model '{model_string}' "
            f"que não foi instalado ou é inválido."
        )


def get_organization_model():
    """
    Retorna o model de Organization configurado ou o padrão.
    
    Usage:
        from shared_auth.utils import get_organization_model
        
        Organization = get_organization_model()
        org = Organization.objects.get(id=1)
    """
    model_string = get_setting('SHARED_AUTH_ORGANIZATION_MODEL', 'shared_auth.SharedOrganization')
    
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_ORGANIZATION_MODEL deve estar no formato 'app_label.model_name'. "
            f"Recebido: '{model_string}'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_ORGANIZATION_MODEL refere-se ao model '{model_string}' "
            f"que não foi instalado ou é inválido."
        )


def get_user_model():
    """
    Retorna o model de User configurado ou o padrão.
    
    Usage:
        from shared_auth.utils import get_user_model
        
        User = get_user_model()
        user = User.objects.get(id=1)
    """
    model_string = get_setting('SHARED_AUTH_USER_MODEL', 'shared_auth.User')
    
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_USER_MODEL deve estar no formato 'app_label.model_name'. "
            f"Recebido: '{model_string}'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_USER_MODEL refere-se ao model '{model_string}' "
            f"que não foi instalado ou é inválido."
        )


def get_member_model():
    """
    Retorna o model de Member configurado ou o padrão.
    
    Usage:
        from shared_auth.utils import get_member_model
        
        Member = get_member_model()
        member = Member.objects.get(id=1)
    """
    model_string = get_setting('SHARED_AUTH_MEMBER_MODEL', 'shared_auth.SharedMember')
    
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_MEMBER_MODEL deve estar no formato 'app_label.model_name'. "
            f"Recebido: '{model_string}'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"SHARED_AUTH_MEMBER_MODEL refere-se ao model '{model_string}' "
            f"que não foi instalado ou é inválido."
        )
