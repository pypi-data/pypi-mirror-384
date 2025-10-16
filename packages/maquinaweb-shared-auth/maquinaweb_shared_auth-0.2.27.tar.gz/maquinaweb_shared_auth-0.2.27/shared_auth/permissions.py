"""
Permissões customizadas para DRF
"""

from rest_framework import permissions

from shared_auth.middleware import get_member


class IsAuthenticated(permissions.BasePermission):
    """
    Verifica se usuário está autenticado via SharedToken
    """

    message = "Autenticação necessária."

    def has_permission(self, request, view):
        return bool(
            request.user and hasattr(request.user, "pk") and request.user.is_active
        )


class HasActiveOrganization(permissions.BasePermission):
    """
    Verifica se usuário tem organização ativa
    """

    message = "Organização ativa necessária."

    def has_permission(self, request, view):
        if not request.user or not hasattr(request, "organization_id"):
            return False

        if not request.organization_id:
            return False

        # Verificar se organização está ativa
        from .models import SharedOrganization

        try:
            org = SharedOrganization.objects.get(pk=request.organization_id)
            return org.is_active()
        except SharedOrganization.DoesNotExist:
            return False


class IsSameOrganization(permissions.BasePermission):
    """
    Verifica se o objeto pertence à mesma organização do usuário

    O model deve ter organization_id
    """

    message = "Você não tem permissão para acessar este recurso."

    def has_object_permission(self, request, view, obj):
        if not hasattr(request, "organization_id"):
            return False

        if not hasattr(obj, "organization_id"):
            return True  # Se objeto não tem org, permite

        # Verifica se o usuário é membro da organização do objeto
        if not get_member(request.user.pk, obj.organization_id):
            return False

        return obj.organization_id == request.organization_id


class IsOwnerOrSameOrganization(permissions.BasePermission):
    """
    Verifica se é o dono do objeto OU da mesma organização

    O model deve ter user_id e/ou organization_id
    """

    message = "Você não tem permissão para acessar este recurso."

    def has_object_permission(self, request, view, obj):
        # Verificar se é o dono
        if hasattr(obj, "user_id") and obj.user_id == request.user.pk:
            return True

        # Verificar se é da mesma organização
        if hasattr(obj, "organization_id") and hasattr(request, "organization_id"):
            # Verifica se o usuário é membro da organização do objeto
            if get_member(request.user.pk, obj.organization_id):
                return obj.organization_id == request.organization_id

        return False
