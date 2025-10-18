"""
Models READ-ONLY para acesso aos dados de autenticação
ATENÇÃO: Estes models NÃO devem ser usados para criar migrations

Para customizar estes models, herde dos models abstratos em shared_auth.abstract_models
e configure no settings.py. Veja a documentação em abstract_models.py
"""

from .abstract_models import (
    AbstractSharedMember,
    AbstractSharedOrganization,
    AbstractSharedToken,
    AbstractUser,
)


class SharedToken(AbstractSharedToken):
    """
    Model READ-ONLY padrão da tabela authtoken_token
    
    Para customizar, crie seu próprio model herdando de AbstractSharedToken
    """
    
    class Meta(AbstractSharedToken.Meta):
        pass


class SharedOrganization(AbstractSharedOrganization):
    """
    Model READ-ONLY padrão da tabela organization
    
    Para customizar, crie seu próprio model herdando de AbstractSharedOrganization
    """
    
    class Meta(AbstractSharedOrganization.Meta):
        pass


class User(AbstractUser):
    """
    Model READ-ONLY padrão da tabela auth_user
    
    Para customizar, crie seu próprio model herdando de AbstractUser
    """
    
    class Meta(AbstractUser.Meta):
        pass


class SharedMember(AbstractSharedMember):
    """
    Model READ-ONLY padrão da tabela organization_member
    
    Para customizar, crie seu próprio model herdando de AbstractSharedMember
    """
    
    class Meta(AbstractSharedMember.Meta):
        pass
