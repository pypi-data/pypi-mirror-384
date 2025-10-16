"""
Serializers compartilhados para DRF
"""

from rest_framework import serializers

from .models import SharedOrganization, User


class OrganizationSerializerMixin(serializers.ModelSerializer):
    """
    Mixin para serializers que incluem dados de organização como objeto aninhado
    e automaticamente setam organization_id no create a partir do request context.

    Retorna:
        {
            "id": 1,
            "titulo": "Teste",
            "organization": {
                "id": 123,
                "name": "Empresa XYZ",
                "cnpj": "12.345.678/0001-90",
                "email": "contato@xyz.com",
                "is_active": true
            }
        }

    Usage:
        class RascunhoSerializer(OrganizationSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'organization']
    """

    organization = serializers.SerializerMethodField()

    def get_organization(self, obj):
        """Retorna dados da organização como objeto"""
        try:
            org = obj.organization
            return {
                "id": org.pk,
                "name": org.name,
                "fantasy_name": org.fantasy_name,
                "image_organization": org.image_organization.url
                if org.image_organization
                else None,
                "cnpj": org.cnpj,
                "email": org.email,
                "telephone": org.telephone,
                "cellphone": org.cellphone,
                "is_branch": org.is_branch,
                "is_active": org.is_active(),
            }
        except Exception:
            return None

    def create(self, validated_data):
        """Automatically set organization_id from request context"""
        if self.context.get("request") and hasattr(
            self.context["request"], "organization_id"
        ):
            validated_data["organization_id"] = self.context["request"].organization_id
        return super().create(validated_data)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedOrganization
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]


class UserSerializerMixin(serializers.ModelSerializer):
    """
    Mixin para serializers que incluem dados de usuário como objeto aninhado
    e automaticamente setam user_id no create a partir do request context.

    Retorna:
        {
            "id": 1,
            "titulo": "Teste",
            "user": {
                "id": 456,
                "username": "joao",
                "email": "joao@xyz.com",
                "full_name": "João Silva",
                "is_active": true
            }
        }

    Usage:
        class RascunhoSerializer(UserSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'user']
    """

    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        """Retorna dados do usuário como objeto"""
        try:
            user: User = obj.user
            return {
                "id": user.pk,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar.url if user.avatar else None,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.get_full_name(),
                "is_active": user.is_active,
            }
        except Exception:
            return None

    def create(self, validated_data):
        """Automatically set user_id from request context"""
        if self.context.get("request") and hasattr(self.context["request"], "user"):
            validated_data["user_id"] = self.context["request"].user.id
        return super().create(validated_data)


class OrganizationUserSerializerMixin(OrganizationSerializerMixin, UserSerializerMixin):
    """
    Mixin combinado com organization e user como objetos aninhados
    e automaticamente seta organization_id e user_id no create a partir do request context.

    Retorna:
        {
            "id": 1,
            "titulo": "Teste",
            "organization": {
                "id": 123,
                "name": "Empresa XYZ",
                ...
            },
            "user": {
                "id": 456,
                "username": "joao",
                ...
            }
        }

    Usage:
        class RascunhoSerializer(OrganizationUserSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'conteudo', 'organization', 'user']
    """

    def create(self, validated_data):
        """Automatically set both organization_id and user_id from request context"""
        if self.context.get("request"):
            request = self.context["request"]
            if hasattr(request, "organization_id"):
                validated_data["organization_id"] = request.organization_id
            if hasattr(request, "user"):
                validated_data["user_id"] = request.user.id
        return super(UserSerializerMixin, self).create(validated_data)


# Versões simplificadas (opcional)
class OrganizationSimpleSerializerMixin(serializers.ModelSerializer):
    """
    Versão simplificada que retorna apenas campos essenciais da organização
    e automaticamente seta organization_id no create a partir do request context.
    """

    organization = serializers.SerializerMethodField()

    def get_organization(self, obj):
        try:
            org = obj.organization
            return {
                "id": org.pk,
                "name": org.name,
                "cnpj": org.cnpj,
            }
        except:
            return None

    def create(self, validated_data):
        """Automatically set organization_id from request context"""
        if self.context.get("request") and hasattr(
            self.context["request"], "organization_id"
        ):
            validated_data["organization_id"] = self.context["request"].organization_id
        return super().create(validated_data)


class UserSimpleSerializerMixin(serializers.ModelSerializer):
    """
    Versão simplificada que retorna apenas campos essenciais do usuário
    e automaticamente seta user_id no create a partir do request context.
    """

    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        try:
            user = obj.user
            return {
                "id": user.pk,
                "email": user.email,
                "full_name": user.get_full_name(),
            }
        except:
            return None

    def create(self, validated_data):
        """Automatically set user_id from request context"""
        if self.context.get("request") and hasattr(self.context["request"], "user"):
            validated_data["user_id"] = self.context["request"].user.id
        return super().create(validated_data)
