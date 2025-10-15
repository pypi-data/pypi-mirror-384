"""
Models READ-ONLY para acesso aos dados de autenticação
ATENÇÃO: Estes models NÃO devem ser usados para criar migrations
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from .exceptions import OrganizationNotFoundError
from .conf import MEMBER_TABLE, ORGANIZATION_TABLE, USER_TABLE, TOKEN_TABLE
from .storage_backend import Storage
from .managers import (
    SharedMemberManager,
    SharedOrganizationManager,
    SharedUserManager,
)


class SharedToken(models.Model):
    """
    Model READ-ONLY da tabela authtoken_token
    Usado para validar tokens em outros sistemas
    """

    key = models.CharField(max_length=40, primary_key=True)
    user_id = models.IntegerField()
    created = models.DateTimeField()

    objects = models.Manager()

    class Meta:
        managed = False
        db_table = TOKEN_TABLE

    def __str__(self):
        return self.key

    @property
    def user(self):
        """Acessa usuário do token"""
        if not hasattr(self, "_cached_user"):
            self._cached_user = User.objects.get_or_fail(self.user_id)
        return self._cached_user

    def is_valid(self):
        """Verifica se token ainda é válido"""
        # Implementar lógica de expiração se necessário
        return True

def organization_image_path(instance, filename):
    return os.path.join(
        "organization",
        str(instance.pk),
        "images",
        filename,
    )

class SharedOrganization(models.Model):
    """
    Model READ-ONLY da tabela organization
    Usado para acessar dados de organizações em outros sistemas
    """

    # Campos principais
    name = models.CharField(max_length=255)
    fantasy_name = models.CharField(max_length=255, blank=True, null=True)
    cnpj = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=50, blank=True, null=True)
    cellphone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    image_organization = models.ImageField(storage=Storage,upload_to=organization_image_path, null=True)

    # Relacionamentos
    main_organization_id = models.IntegerField(null=True, blank=True)
    is_branch = models.BooleanField(default=False)

    # Metadados
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SharedOrganizationManager()

    class Meta:
        managed = False  # CRITICAL: Não gera migrations
        db_table = ORGANIZATION_TABLE

    def __str__(self):
        return self.fantasy_name or self.name or f"Org #{self.pk}"

    @property
    def main_organization(self):
        """
        Acessa organização principal (lazy loading)

        Usage:
            if org.is_branch:
                main = org.main_organization
        """
        if self.main_organization_id:
            return SharedOrganization.objects.get_or_fail(self.main_organization_id)
        return None

    @property
    def branches(self):
        """
        Retorna filiais desta organização

        Usage:
            branches = org.branches
        """
        return SharedOrganization.objects.filter(main_organization_id=self.pk)

    @property
    def members(self):
        """
        Retorna membros desta organização

        Usage:
            members = org.members
            for member in members:
                print(member.user.email)
        """
        return SharedMember.objects.for_organization(self.pk)

    @property
    def users(self):
        """
        Retorna usuários desta organização

        Usage:
            users = org.users
        """
        return User.objects.filter(
            id__in=self.members.values_list("user_id", flat=True)
        )

    def is_active(self):
        """Verifica se organização está ativa"""
        return self.deleted_at is None


class User(AbstractUser):
    """
    Model READ-ONLY da tabela auth_user
    """

    date_joined = models.DateTimeField()
    last_login = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(storage=Storage,blank=True, null=True)
    # Campos customizados
    createdat = models.DateTimeField()
    updatedat = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SharedUserManager()

    class Meta:
        managed = False
        db_table = USER_TABLE

    @property
    def organizations(self):
        """
        Retorna todas as organizações associadas ao usuário.
        """
        return SharedOrganization.objects.filter(
            id__in=SharedMember.objects.filter(user_id=self.id).values_list(
                "organization_id", flat=True
            )
        )

    def get_org(self, organization_id):
        """
        Retorna a organização especificada pelo ID, se o usuário for membro.
        """
        try:
            organization = SharedOrganization.objects.get(id=organization_id)
        except SharedOrganization.DoesNotExist:
            raise OrganizationNotFoundError(
                f"Organização com ID {organization_id} não encontrada."
            )

        if not SharedMember.objects.filter(
            user_id=self.id, organization_id=organization.id
        ).exists():
            raise OrganizationNotFoundError("Usuário não é membro desta organização.")

        return organization



class SharedMember(models.Model):
    """
    Model READ-ONLY da tabela organization_member
    Relacionamento entre User e Organization
    """

    user_id = models.IntegerField()
    organization_id = models.IntegerField()
    metadata = models.JSONField(default=dict)

    objects = SharedMemberManager()

    class Meta:
        managed = False
        db_table = MEMBER_TABLE

    def __str__(self):
        return f"Member: User {self.user_id} - Org {self.organization_id}"

    @property
    def user(self):
        """
        Acessa usuário (lazy loading)

        Usage:
            member = SharedMember.objects.first()
            user = member.user
            print(user.email)
        """
        return User.objects.get_or_fail(self.user_id)

    @property
    def organization(self):
        """
        Acessa organização (lazy loading)

        Usage:
            member = SharedMember.objects.first()
            org = member.organization
            print(org.name)
        """
        return SharedOrganization.objects.get_or_fail(self.organization_id)
