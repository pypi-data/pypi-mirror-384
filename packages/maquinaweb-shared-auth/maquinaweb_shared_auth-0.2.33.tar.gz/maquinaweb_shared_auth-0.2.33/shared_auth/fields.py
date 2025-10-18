"""
Fields customizados para facilitar ainda mais
"""

"""
Fields customizados para facilitar ainda mais
"""
from rest_framework import serializers


class OrganizationField(serializers.Field):
    """
    Field que retorna dados completos da organização

    Usage:
        class RascunhoSerializer(serializers.ModelSerializer):
            organization = OrganizationField(source='*')
    """

    def to_representation(self, obj):
        try:
            org = obj.organization
            return {
                "id": org.pk,
                "name": org.name,
                "fantasy_name": org.fantasy_name,
                "cnpj": org.cnpj,
                "email": org.email,
                "is_active": org.is_active(),
            }
        except:
            return None


class UserField(serializers.Field):
    """
    Field que retorna dados completos do usuário
    """

    def to_representation(self, obj):
        try:
            user = obj.user
            return {
                "id": user.pk,
                "username": user.username,
                "email": user.email,
                "full_name": user.get_full_name(),
                "is_active": user.is_active,
            }
        except:
            return None