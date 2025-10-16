"""
Managers customizados para os models compartilhados
"""

from django.contrib.auth.models import UserManager
from django.db import models

from .exceptions import OrganizationNotFoundError, UserNotFoundError


class SharedOrganizationManager(models.Manager):
    """Manager para SharedOrganization com métodos úteis"""

    def get_or_fail(self, organization_id):
        """
        Busca organização ou lança exceção customizada

        Usage:
            org = SharedOrganization.objects.get_or_fail(123)
        """
        try:
            return self.get(pk=organization_id)
        except self.model.DoesNotExist:
            raise OrganizationNotFoundError(
                f"Organização com ID {organization_id} não encontrada"
            )

    def active(self):
        """Retorna apenas organizações ativas (não deletadas)"""
        return self.filter(deleted_at__isnull=True)

    def branches(self):
        """Retorna apenas filiais"""
        return self.filter(is_branch=True)

    def main_organizations(self):
        """Retorna apenas organizações principais"""
        return self.filter(is_branch=False)

    def by_cnpj(self, cnpj):
        """Busca por CNPJ"""
        import re

        clean_cnpj = re.sub(r"[^0-9]", "", cnpj)
        return self.filter(cnpj__contains=clean_cnpj).first()


class SharedUserManager(UserManager):
    """Manager para SharedUser"""

    def get_or_fail(self, user_id):
        """Busca usuário ou lança exceção"""
        try:
            return self.get(pk=user_id)
        except self.model.DoesNotExist:
            raise UserNotFoundError(f"Usuário com ID {user_id} não encontrado")

    def active(self):
        """Retorna usuários ativos"""
        return self.filter(deleted_at__isnull=True, is_active=True)

    def by_email(self, email):
        """Busca por email"""
        return self.filter(email=email).first()


class SharedMemberManager(models.Manager):
    """Manager para SharedMember"""

    def for_user(self, user_id):
        """Retorna memberships de um usuário"""
        return self.filter(user_id=user_id)

    def for_organization(self, organization_id):
        """Retorna membros de uma organização"""
        return self.filter(organization_id=organization_id)


class OrganizationQuerySetMixin:
    """Mixin para QuerySets com métodos de organização"""

    def for_organization(self, organization_id):
        """Filtra por organização"""
        return self.filter(organization_id=organization_id)

    def for_organizations(self, organization_ids):
        """Filtra por múltiplas organizações"""
        return self.filter(organization_id__in=organization_ids)

    def with_organization_data(self):
        """
        Pré-carrega dados de organizações (evita N+1)

        Returns:
            Lista de objetos com _cached_organization
        """
        objects = list(self.all())
        from . import SharedOrganization

        if not objects:
            return objects

        # Coletar IDs únicos
        org_ids = set(obj.organization_id for obj in objects)

        # Buscar todas de uma vez
        organizations = {
            org.pk: org for org in SharedOrganization.objects.filter(pk__in=org_ids)
        }

        # Cachear nos objetos
        for obj in objects:
            obj._cached_organization = organizations.get(obj.organization_id)

        return objects


class UserQuerySetMixin:
    """Mixin para QuerySets com métodos de usuário"""

    def for_user(self, user_id):
        """Filtra por usuário"""
        return self.filter(user_id=user_id)

    def for_users(self, user_ids):
        """Filtra por múltiplos usuários"""
        return self.filter(user_id__in=user_ids)

    def with_user_data(self):
        """
        Pré-carrega dados de usuários (evita N+1)
        """
        from . import SharedUser

        objects = list(self.all())

        if not objects:
            return objects

        user_ids = set(obj.user_id for obj in objects)

        users = {user.pk: user for user in SharedUser.objects.filter(pk__in=user_ids)}

        for obj in objects:
            obj._cached_user = users.get(obj.user_id)

        return objects


class OrganizationUserQuerySetMixin(OrganizationQuerySetMixin, UserQuerySetMixin):
    """Mixin combinado com todos os métodos"""

    def with_auth_data(self):
        """
        Pré-carrega dados de organizações E usuários (evita N+1)
        """
        from . import SharedOrganization, SharedUser

        objects = list(self.all())

        if not objects:
            return objects

        # Coletar IDs
        org_ids = set(obj.organization_id for obj in objects)
        user_ids = set(obj.user_id for obj in objects)

        # Buscar em batch
        organizations = {
            org.pk: org for org in SharedOrganization.objects.filter(pk__in=org_ids)
        }

        users = {user.pk: user for user in SharedUser.objects.filter(pk__in=user_ids)}

        # Cachear
        for obj in objects:
            obj._cached_organization = organizations.get(obj.organization_id)
            obj._cached_user = users.get(obj.user_id)

        return objects

    def create_with_validation(self, organization_id, user_id, **kwargs):
        """
        Cria objeto com validação de organização e usuário
        """
        from . import SharedMember, SharedOrganization

        # Valida organização
        SharedOrganization.objects.get_or_fail(organization_id)

        # Valida usuário pertence à organização
        if not SharedMember.objects.filter(
            user_id=user_id, organization_id=organization_id
        ).exists():
            raise ValueError(
                f"Usuário {user_id} não pertence à organização {organization_id}"
            )

        return self.create(organization_id=organization_id, user_id=user_id, **kwargs)


class BaseAuthManager(models.Manager):
    """Manager base com suporte aos mixins"""

    def get_queryset(self):
        # Detecta qual mixin está sendo usado
        model_bases = [base.__name__ for base in self.model.__bases__]

        if "OrganizationUserMixin" in model_bases:
            qs_class = type(
                "QuerySet", (OrganizationUserQuerySetMixin, models.QuerySet), {}
            )
        elif "OrganizationMixin" in model_bases:
            qs_class = type(
                "QuerySet", (OrganizationQuerySetMixin, models.QuerySet), {}
            )
        elif "UserMixin" in model_bases:
            qs_class = type("QuerySet", (UserQuerySetMixin, models.QuerySet), {})
        else:
            return super().get_queryset()

        return qs_class(self.model, using=self._db)
