"""
Mixins para facilitar a criação de models com referências ao sistema de auth
"""

from django.db import models
from rest_framework import status, viewsets
from rest_framework.response import Response

from shared_auth.managers import BaseAuthManager


class OrganizationMixin(models.Model):
    """
    Mixin para models que pertencem a uma organização

    Adiciona:
    - Campo organization_id
    - Property organization (lazy loading)
    - Métodos úteis

    Usage:
        class Rascunho(OrganizationMixin):
            titulo = models.CharField(max_length=200)

        # Uso
        rascunho.organization  # Acessa organização automaticamente
        rascunho.organization_members  # Acessa membros
    """

    organization_id = models.IntegerField(
        db_index=True, help_text="ID da organização no sistema de autenticação"
    )
    objects = BaseAuthManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["organization_id"]),
        ]

    @property
    def organization(self):
        """
        Acessa organização do banco de auth (lazy loading com cache)
        """
        if not hasattr(self, "_cached_organization"):
            from shared_auth.models import SharedOrganization

            self._cached_organization = SharedOrganization.objects.get_or_fail(
                self.organization_id
            )
        return self._cached_organization

    @property
    def organization_members(self):
        """Retorna membros da organização"""
        return self.organization.members

    @property
    def organization_users(self):
        """Retorna usuários da organização"""
        return self.organization.users

    def is_organization_active(self):
        """Verifica se a organização está ativa"""
        return self.organization.is_active()

    def get_organization_name(self):
        """Retorna nome da organização (safe)"""
        try:
            return self.organization.name
        except:
            return None


class UserMixin(models.Model):
    """
    Mixin para models que pertencem a um usuário

    Adiciona:
    - Campo user_id
    - Property user (lazy loading)
    - Métodos úteis

    Usage:
        class Rascunho(UserMixin):
            titulo = models.CharField(max_length=200)

        # Uso
        rascunho.user  # Acessa usuário automaticamente
        rascunho.user_email  # Acessa email
    """

    user_id = models.IntegerField(
        db_index=True, help_text="ID do usuário no sistema de autenticação"
    )
    objects = BaseAuthManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["user_id"]),
        ]

    @property
    def user(self):
        """
        Acessa usuário do banco de auth (lazy loading com cache)
        """
        if not hasattr(self, "_cached_user"):
            from shared_auth.models import User

            self._cached_user = User.objects.get_or_fail(self.user_id)
        return self._cached_user

    @property
    def user_email(self):
        """Retorna email do usuário (safe)"""
        try:
            return self.user.email
        except:
            return None

    @property
    def user_full_name(self):
        """Retorna nome completo do usuário (safe)"""
        try:
            return self.user.get_full_name()
        except:
            return None

    @property
    def user_organizations(self):
        """Retorna organizações do usuário"""
        return self.user.organizations

    def is_user_active(self):
        """Verifica se o usuário está ativo"""
        try:
            return self.user.is_active and self.user.deleted_at is None
        except:
            return False


class OrganizationUserMixin(OrganizationMixin, UserMixin):
    """
    Mixin combinado para models que pertencem a organização E usuário

    Adiciona tudo dos dois mixins + validações

    Usage:
        class Rascunho(OrganizationUserMixin):
            titulo = models.CharField(max_length=200)

        # Uso
        rascunho.organization  # Organização
        rascunho.user  # Usuário
        rascunho.validate_user_belongs_to_organization()  # Validação
    """

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["organization_id", "user_id"]),
        ]

    def validate_user_belongs_to_organization(self):
        """
        Valida se o usuário pertence à organização

        Returns:
            bool: True se pertence, False caso contrário
        """
        from shared_auth.models import SharedMember

        return SharedMember.objects.filter(
            user_id=self.user_id, organization_id=self.organization_id
        ).exists()

    def user_can_access(self, user_id):
        """
        Verifica se um usuário pode acessar este registro
        (se pertence à mesma organização)
        """
        from shared_auth.models import SharedMember

        return SharedMember.objects.filter(
            user_id=user_id, organization_id=self.organization_id
        ).exists()


class LoggedOrganizationMixin(viewsets.ModelViewSet):
    """
    Mixin para ViewSets que dependem de uma organização logada.
    Integra com a lib maquinaweb-shared-auth.
    """

    def get_organization_id(self):
        """Obtém o ID da organização logada via maquinaweb-shared-auth"""
        return self.request.organization_id

    def get_user(self):
        """Obtém o usuário atual autenticado"""
        return self.request.user

    def check_logged_organization(self):
        """Verifica se há uma organização logada"""
        return self.get_organization_id() is not None

    def require_logged_organization(self):
        """Retorna erro se não houver organização logada"""
        if not self.check_logged_organization():
            return Response(
                {
                    "detail": "Nenhuma organização logada. Defina uma organização antes de continuar."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def get_queryset(self):
        """Filtra os objetos pela organização logada, se aplicável"""
        queryset = super().get_queryset()

        response = self.require_logged_organization()
        if response:
            return queryset.none()

        organization_id = self.get_organization_id()
        if hasattr(queryset.model, "organization_id"):
            return queryset.filter(organization_id=organization_id)
        elif hasattr(queryset.model, "organization"):
            return queryset.filter(organization_id=organization_id)
        return queryset

    def perform_create(self, serializer):
        """Define a organização automaticamente ao criar um objeto"""
        response = self.require_logged_organization()
        if response:
            return response

        organization_id = self.get_organization_id()

        if "organization" in serializer.fields:
            serializer.save(organization_id=organization_id)
        else:
            serializer.save()


class TimestampedMixin(models.Model):
    """
    Mixin para adicionar timestamps
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
