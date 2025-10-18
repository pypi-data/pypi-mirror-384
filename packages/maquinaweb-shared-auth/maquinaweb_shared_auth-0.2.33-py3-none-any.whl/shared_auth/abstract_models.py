"""
Models abstratos para customização
Estes models podem ser herdados nos apps clientes para adicionar campos e métodos customizados
"""

import os

from django.contrib.auth.models import AbstractUser
from django.db import models

from .conf import MEMBER_TABLE, ORGANIZATION_TABLE, TOKEN_TABLE, USER_TABLE
from .exceptions import OrganizationNotFoundError
from .managers import SharedMemberManager, SharedOrganizationManager, UserManager
from .storage_backend import Storage


def organization_image_path(instance, filename):
    return os.path.join(
        "organization",
        str(instance.pk),
        "images",
        filename,
    )


class AbstractSharedToken(models.Model):
    """
    Model abstrato READ-ONLY da tabela authtoken_token
    Usado para validar tokens em outros sistemas
    
    Para customizar, crie um model no seu app:
    
    from shared_auth.abstract_models import AbstractSharedToken
    
    class CustomToken(AbstractSharedToken):
        # Adicione campos customizados
        custom_field = models.CharField(max_length=100)
        
        class Meta(AbstractSharedToken.Meta):
            pass
    
    E configure no settings.py:
    SHARED_AUTH_TOKEN_MODEL = 'seu_app.CustomToken'
    """

    key = models.CharField(max_length=40, primary_key=True)
    user_id = models.IntegerField()
    created = models.DateTimeField()

    objects = models.Manager()

    class Meta:
        abstract = True
        managed = False
        db_table = TOKEN_TABLE

    def __str__(self):
        return self.key

    @property
    def user(self):
        """Acessa usuário do token"""
        from .utils import get_user_model
        
        if not hasattr(self, "_cached_user"):
            User = get_user_model()
            self._cached_user = User.objects.get_or_fail(self.user_id)
        return self._cached_user

    def is_valid(self):
        """Verifica se token ainda é válido"""
        # Implementar lógica de expiração se necessário
        return True


class AbstractSharedOrganization(models.Model):
    """
    Model abstrato READ-ONLY da tabela organization
    Usado para acessar dados de organizações em outros sistemas
    
    Para customizar, crie um model no seu app:
    
    from shared_auth.abstract_models import AbstractSharedOrganization
    
    class CustomOrganization(AbstractSharedOrganization):
        # Adicione campos customizados
        custom_field = models.CharField(max_length=100)
        
        class Meta(AbstractSharedOrganization.Meta):
            pass
    
    E configure no settings.py:
    SHARED_AUTH_ORGANIZATION_MODEL = 'seu_app.CustomOrganization'
    """

    # Campos principais
    name = models.CharField(max_length=255)
    fantasy_name = models.CharField(max_length=255, blank=True, null=True)
    cnpj = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=50, blank=True, null=True)
    cellphone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    image_organization = models.ImageField(
        storage=Storage, upload_to=organization_image_path, null=True
    )

    # Relacionamentos
    main_organization_id = models.IntegerField(null=True, blank=True)
    is_branch = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    
    # Metadados
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SharedOrganizationManager()

    class Meta:
        abstract = True
        managed = False
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
        from .utils import get_organization_model
        
        if self.main_organization_id:
            Organization = get_organization_model()
            return Organization.objects.get_or_fail(self.main_organization_id)
        return None

    @property
    def branches(self):
        """
        Retorna filiais desta organização

        Usage:
            branches = org.branches
        """
        from .utils import get_organization_model
        
        Organization = get_organization_model()
        return Organization.objects.filter(main_organization_id=self.pk)

    @property
    def members(self):
        """
        Retorna membros desta organização

        Usage:
            members = org.members
            for member in members:
                print(member.user.email)
        """
        from .utils import get_member_model
        
        Member = get_member_model()
        return Member.objects.for_organization(self.pk)

    @property
    def users(self):
        """
        Retorna usuários desta organização

        Usage:
            users = org.users
        """
        from .utils import get_user_model
        
        User = get_user_model()
        return User.objects.filter(
            id__in=self.members.values_list("user_id", flat=True)
        )

    def is_active(self):
        """Verifica se organização está ativa"""
        return self.deleted_at is None


class AbstractUser(AbstractUser):
    """
    Model abstrato READ-ONLY da tabela auth_user
    
    Para customizar, crie um model no seu app:
    
    from shared_auth.abstract_models import AbstractUser
    
    class CustomUser(AbstractUser):
        # Adicione campos customizados
        custom_field = models.CharField(max_length=100)
        
        class Meta(AbstractUser.Meta):
            pass
    
    E configure no settings.py:
    SHARED_AUTH_USER_MODEL = 'seu_app.CustomUser'
    """

    date_joined = models.DateTimeField()
    last_login = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(storage=Storage, blank=True, null=True)
    
    # Campos customizados
    createdat = models.DateTimeField()
    updatedat = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    class Meta:
        abstract = True
        managed = False
        db_table = USER_TABLE

    @property
    def organizations(self):
        """
        Retorna todas as organizações associadas ao usuário.
        """
        from .utils import get_organization_model, get_member_model
        
        Organization = get_organization_model()
        Member = get_member_model()
        
        return Organization.objects.filter(
            id__in=Member.objects.filter(user_id=self.id).values_list(
                "organization_id", flat=True
            )
        )

    def get_org(self, organization_id):
        """
        Retorna a organização especificada pelo ID, se o usuário for membro.
        """
        from .utils import get_organization_model, get_member_model
        
        Organization = get_organization_model()
        Member = get_member_model()
        
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise OrganizationNotFoundError(
                f"Organização com ID {organization_id} não encontrada."
            )

        if not Member.objects.filter(
            user_id=self.id, organization_id=organization.id
        ).exists():
            raise OrganizationNotFoundError("Usuário não é membro desta organização.")

        return organization


class AbstractSharedMember(models.Model):
    """
    Model abstrato READ-ONLY da tabela organization_member
    Relacionamento entre User e Organization
    
    Para customizar, crie um model no seu app:
    
    from shared_auth.abstract_models import AbstractSharedMember
    
    class CustomMember(AbstractSharedMember):
        # Adicione campos customizados
        custom_field = models.CharField(max_length=100)
        
        class Meta(AbstractSharedMember.Meta):
            pass
    
    E configure no settings.py:
    SHARED_AUTH_MEMBER_MODEL = 'seu_app.CustomMember'
    """

    user_id = models.IntegerField()
    organization_id = models.IntegerField()
    metadata = models.JSONField(default=dict)

    objects = SharedMemberManager()

    class Meta:
        abstract = True
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
        from .utils import get_user_model
        
        User = get_user_model()
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
        from .utils import get_organization_model
        
        Organization = get_organization_model()
        return Organization.objects.get_or_fail(self.organization_id)
