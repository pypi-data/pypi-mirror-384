"""
Middlewares para autenticação compartilhada
"""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .authentication import SharedTokenAuthentication
from .models import SharedMember, SharedOrganization, SharedToken, User


class SharedAuthMiddleware(MiddlewareMixin):
    """
    Middleware que autentica usuário baseado no token do header

    Usage em settings.py:
        MIDDLEWARE = [
            ...
            'shared_auth.middleware.SharedAuthMiddleware',
        ]

    O middleware busca o token em:
    - Header: Authorization: Token <token>
    - Header: X-Auth-Token: <token>
    - Cookie: auth_token
    """

    def process_request(self, request):
        # Caminhos que não precisam de autenticação
        exempt_paths = getattr(
            request,
            "auth_exempt_paths",
            [
                "/api/auth/login/",
                "/api/auth/register/",
                "/health/",
                "/static/",
            ],
        )

        if any(request.path.startswith(path) for path in exempt_paths):
            return None

        # Extrair token
        token = self._get_token_from_request(request)

        if not token:
            # request.user = None
            request.auth = None
            return None

        # Validar token e buscar usuário
        try:
            token_obj = SharedToken.objects.get(key=token)
            user = User.objects.get(pk=token_obj.user_id)

            if not user.is_active or user.deleted_at is not None:
                # request.user = None
                request.auth = None
                return None

            # Adicionar ao request
            # request.user = user
            request.auth = token_obj

        except (SharedToken.DoesNotExist, User.DoesNotExist):
            # request.user = None
            request.auth = None

        return None

    def _get_token_from_request(self, request):
        """Extrai token do request"""
        # Header: Authorization: Token <token>
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Token "):
            return auth_header.split(" ")[1]

        # Header: X-Auth-Token
        token = request.META.get("HTTP_X_AUTH_TOKEN")
        if token:
            return token

        # Cookie
        token = request.COOKIES.get("auth_token")
        if token:
            return token

        return None


class RequireAuthMiddleware(MiddlewareMixin):
    """
    Middleware que FORÇA autenticação em todas as rotas
    Retorna 401 se não estiver autenticado

    Usage em settings.py:
        MIDDLEWARE = [
            'shared_auth.middleware.SharedAuthMiddleware',
            'shared_auth.middleware.RequireAuthMiddleware',
        ]
    """

    def process_request(self, request):
        # Caminhos públicos
        public_paths = getattr(
            request,
            "public_paths",
            [
                "/api/auth/",
                "/health/",
                "/docs/",
                "/static/",
            ],
        )

        if any(request.path.startswith(path) for path in public_paths):
            return None

        # Verificar se está autenticado
        if not hasattr(request, "user") or request.user is None:
            return JsonResponse(
                {
                    "error": "Autenticação necessária",
                    "detail": "Token não fornecido ou inválido",
                },
                status=401,
            )

        return None


class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware que adiciona organização logada ao request

    Adiciona:
    - request.organization (objeto SharedOrganization)
    """

    def process_request(self, request) -> None:
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        organization_id = self._determine_organization_id(request)
        user = self._authenticate_user(request)

        if not organization_id and not user:
            return

        if organization_id and user:
            organization_id = self._validate_organization_membership(
                user, organization_id
            )
            if not organization_id:
                return

        request.organization_id = organization_id
        request.organization = SharedOrganization.objects.filter(
            pk=organization_id
        ).first()

    @staticmethod
    def _authenticate_user(request):
        data = SharedTokenAuthentication().authenticate(request)

        return data[0] if data else None

    def _determine_organization_id(self, request):
        org_id = self._get_organization_from_header(request)
        if org_id:
            return org_id

        return self._get_organization_from_user(request)

    @staticmethod
    def _get_organization_from_header(request):
        if header_value := request.headers.get("X-Organization"):
            try:
                return int(header_value)
            except (ValueError, TypeError):
                pass
        return None

    @staticmethod
    def _get_organization_from_user(request):
        """
        Retorna a primeira organização do usuário autenticado
        """
        if not request.user.is_authenticated:
            return None

        # Buscar a primeira organização que o usuário pertence
        member = SharedMember.objects.filter(user_id=request.user.pk).first()

        return member.organization_id if member else None

    @staticmethod
    def _validate_organization_membership(user, organization_id):
        try:
            member = get_member(user.pk, organization_id)
            if not member and not user.is_superuser:
                return None
            return organization_id
        except Exception:
            return None


def get_member(user_id, organization_id):
    return SharedMember.objects.filter(
        user_id=user_id, organization_id=organization_id
    ).first()
