from django.conf import settings

def get_setting(name, default):
    """Retorna valor configurado no settings ou o padrão"""
    return getattr(settings, name, default)


ORGANIZATION_TABLE = get_setting("SHARED_AUTH_ORGANIZATION_TABLE", "organization_organization")
USER_TABLE = get_setting("SHARED_AUTH_USER_TABLE", "auth_user")
MEMBER_TABLE = get_setting("SHARED_AUTH_MEMBER_TABLE", "organization_member")
TOKEN_TABLE = get_setting("SHARED_AUTH_TOKEN_TABLE", "organization_multitoken")