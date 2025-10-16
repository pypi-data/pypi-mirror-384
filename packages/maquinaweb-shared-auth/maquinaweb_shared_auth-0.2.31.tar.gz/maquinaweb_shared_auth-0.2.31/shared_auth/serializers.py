"""
Serializers compartilhados para DRF

Separação de responsabilidades:
- CreateSerializerMixin: apenas para criação (seta IDs do request)
- SerializerMixin: listagem com dados aninhados + criação (compatibilidade com código existente)

Se quiser usar separadamente:
- Use apenas *CreateSerializerMixin para create
- Use apenas *SerializerMixin para listagem
- Ou herde ambos se precisar
"""

from rest_framework import serializers

from .models import SharedOrganization, User

# ==================== ORGANIZATION SERIALIZERS ====================


class OrganizationCreateSerializerMixin(serializers.ModelSerializer):
    """
    Mixin APENAS para criação.
    Automaticamente seta organization_id no create a partir do request context.

    Usage:
        class RascunhoCreateSerializer(OrganizationCreateSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'conteudo']
    """

    def create(self, validated_data):
        """Automatically set organization_id from request context"""
        if self.context.get("request") and hasattr(
            self.context["request"], "organization_id"
        ):
            validated_data["organization_id"] = self.context["request"].organization_id
        return super().create(validated_data)


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

        # Ou apenas para listagem (sem create):
        class RascunhoListSerializer(OrganizationSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'organization']

        # Ou combinar com create:
        class RascunhoFullSerializer(OrganizationSerializerMixin, OrganizationCreateSerializerMixin):
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


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedOrganization
        fields = "__all__"


# ==================== USER SERIALIZERS ====================


class UserCreateSerializerMixin(serializers.ModelSerializer):
    """
    Mixin APENAS para criação.
    Automaticamente seta user_id no create a partir do request context.

    Usage:
        class RascunhoCreateSerializer(UserCreateSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'conteudo']
    """

    def create(self, validated_data):
        """Automatically set user_id from request context"""
        if self.context.get("request") and hasattr(self.context["request"], "user"):
            validated_data["user_id"] = self.context["request"].user.id
        return super().create(validated_data)


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

        # Ou apenas para listagem (sem create):
        class RascunhoListSerializer(UserSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'user']

        # Ou combinar com create:
        class RascunhoFullSerializer(UserSerializerMixin, UserCreateSerializerMixin):
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


# ==================== COMBINED ORGANIZATION + USER SERIALIZERS ====================


class OrganizationUserCreateSerializerMixin(serializers.ModelSerializer):
    """
    Mixin APENAS para criação com organization + user.
    Automaticamente seta organization_id e user_id no create a partir do request context.

    Usage:
        class RascunhoCreateSerializer(OrganizationUserCreateSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'conteudo']
    """

    def create(self, validated_data):
        """Automatically set both organization_id and user_id from request context"""
        if self.context.get("request"):
            request = self.context["request"]
            if hasattr(request, "organization_id"):
                validated_data["organization_id"] = request.organization_id
            if hasattr(request, "user"):
                validated_data["user_id"] = request.user.id
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

        # Ou apenas para listagem (sem create):
        class RascunhoListSerializer(OrganizationUserSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'organization', 'user']

        # Ou combinar com create:
        class RascunhoFullSerializer(OrganizationUserSerializerMixin, OrganizationUserCreateSerializerMixin):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'organization', 'user']
    """

    pass


# ==================== SIMPLIFIED VERSIONS ====================


class OrganizationSimpleSerializerMixin(serializers.ModelSerializer):
    """
    Versão simplificada que retorna apenas campos essenciais da organização
    e automaticamente seta organization_id no create a partir do request context.

    Usage:
        # Para listagem:
        class RascunhoListSerializer(OrganizationSimpleSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'organization']

        # Para criar com organization:
        class RascunhoCreateSerializer(OrganizationSimpleSerializerMixin, OrganizationCreateSerializerMixin):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'organization']
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
        except Exception:
            return None


class UserSimpleSerializerMixin(serializers.ModelSerializer):
    """
    Versão simplificada que retorna apenas campos essenciais do usuário
    e automaticamente seta user_id no create a partir do request context.

    Usage:
        # Para listagem:
        class RascunhoListSerializer(UserSimpleSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'user']

        # Para criar com user:
        class RascunhoCreateSerializer(UserSimpleSerializerMixin, UserCreateSerializerMixin):
            class Meta:
                model = Rascunho
                fields = ['id', 'titulo', 'user']
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
        except Exception:
            return None
