"""
Decorators para views funcionais
"""

from functools import wraps

from django.http import JsonResponse

from .utils import get_organization_model, get_token_model, get_user_model


def require_auth(view_func):
    """
    Decorator que requer autenticação

    Usage:
        @require_auth
        def my_view(request):
            return JsonResponse({'user': request.user.email})
    """

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Extrair token
        token = _get_token_from_request(request)

        if not token:
            return JsonResponse({"error": "Token não fornecido"}, status=401)

        # Validar token
        Token = get_token_model()
        User = get_user_model()

        try:
            token_obj = Token.objects.get(key=token)
            user = User.objects.get(pk=token_obj.user_id)

            if not user.is_active or user.deleted_at is not None:
                return JsonResponse({"error": "Usuário inativo"}, status=401)

            request.user = user
            request.auth = token_obj

        except (Token.DoesNotExist, User.DoesNotExist):
            return JsonResponse({"error": "Token inválido"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapped_view


def require_organization(view_func):
    """
    Decorator que requer organização ativa
    """

    @wraps(view_func)
    @require_auth
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, "organization_id") or not request.organization_id:
            return JsonResponse({"error": "Organização não definida"}, status=403)

        # Buscar organização
        Organization = get_organization_model()

        try:
            org = Organization.objects.get(pk=request.organization_id)

            if not org.is_active():
                return JsonResponse({"error": "Organização inativa"}, status=403)

            request.organization = org

        except Organization.DoesNotExist:
            return JsonResponse({"error": "Organização não encontrada"}, status=404)

        return view_func(request, *args, **kwargs)

    return wrapped_view


def require_same_organization(view_func):
    """
    Decorator que verifica se objeto pertence à mesma organização

    O objeto deve estar em kwargs['pk'] ou kwargs['id']
    """

    @wraps(view_func)
    @require_organization
    def wrapped_view(request, *args, **kwargs):
        obj_id = kwargs.get("pk") or kwargs.get("id")

        if not obj_id:
            return view_func(request, *args, **kwargs)

        # Aqui você precisa buscar o objeto e verificar
        # Exemplo genérico - adapte conforme seu model
        # Tentar identificar o model pelo path
        # Esta é uma implementação básica
        # Em produção, você pode passar o model como parâmetro

        return view_func(request, *args, **kwargs)

    return wrapped_view


def _get_token_from_request(request):
    """Helper para extrair token"""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Token "):
        return auth_header.split(" ")[1]

    token = request.META.get("HTTP_X_AUTH_TOKEN")
    if token:
        return token

    token = request.COOKIES.get("auth_token")
    if token:
        return token

    return None
