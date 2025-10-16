# 🔐 Maquinaweb Shared Auth

> Biblioteca Django para autenticação compartilhada entre múltiplos sistemas usando um único banco de dados centralizado.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Características](#-características)
- [Arquitetura](#️-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#️-configuração)
- [Uso Básico](#-uso-básico)
- [Guias Avançados](#-guias-avançados)
- [API Reference](#-api-reference)

---

## 🎯 Visão Geral

A **Maquinaweb Shared Auth** permite que múltiplos sistemas Django compartilhem dados de autenticação, usuários e organizações através de um banco de dados centralizado, sem necessidade de requisições HTTP.

### Problema Resolvido

Ao invés de:
- ❌ Duplicar dados de usuários em cada sistema
- ❌ Fazer requisições HTTP entre sistemas
- ❌ Manter múltiplos bancos de autenticação sincronizados

Você pode:
- ✅ Acessar dados de autenticação diretamente do banco central
- ✅ Usar a interface familiar do Django ORM
- ✅ Garantir consistência de dados entre sistemas
- ✅ Trabalhar com models read-only seguros

---

## ✨ Características

### Core Features

- **🔐 Autenticação Centralizada**: Token-based authentication compartilhado
- **🏢 Multi-Tenancy**: Suporte completo a organizações e filiais
- **👥 Gestão de Membros**: Relacionamento usuários ↔ organizações
- **🔒 Read-Only Safety**: Proteção contra modificações acidentais
- **⚡ Performance**: Managers otimizados com prefetch automático
- **🎨 DRF Ready**: Mixins para serializers com dados aninhados

### Componentes Principais

| Componente | Descrição |
|------------|-----------|
| **Models** | SharedOrganization, User, SharedMember, SharedToken |
| **Mixins** | OrganizationMixin, UserMixin, OrganizationUserMixin |
| **Serializers** | OrganizationSerializerMixin, UserSerializerMixin |
| **Authentication** | SharedTokenAuthentication |
| **Middleware** | SharedAuthMiddleware, OrganizationMiddleware |
| **Permissions** | IsAuthenticated, HasActiveOrganization, IsSameOrganization |
| **Managers** | Métodos otimizados com prefetch e validações |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────┐
│   Sistema de Autenticação Central  │
│                                     │
│  ┌──────────────┐  ┌────────────┐ │
│  │Organization  │  │    User    │ │
│  └──────┬───────┘  └─────┬──────┘ │
│         │                │         │
│         └────────┬───────┘         │
│                  │                 │
│           ┌──────▼──────┐         │
│           │   Member    │         │
│           │   Token     │         │
│           └─────────────┘         │
└──────────────────┬──────────────────┘
                   │
      ┌────────────┴────────────┐
      │  PostgreSQL/MySQL       │
      │  (auth_db)              │
      └────────────┬────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
┌─────▼─────┐            ┌─────▼─────┐
│ Sistema A │            │ Sistema B │
│           │            │           │
│ Pedidos   │            │ Estoque   │
│ ├─ org    │            │ ├─ org    │
│ └─ user   │            │ └─ user   │
└───────────┘            └───────────┘
```

**Fluxo de Autenticação:**

1. Cliente envia request com token no header
2. Middleware valida token no banco `auth_db`
3. Dados do usuário e organização são anexados ao `request`
4. Sistema cliente acessa dados via ORM (read-only)

---

## 📦 Instalação

### 1. Instalar a Biblioteca

```bash
# Via pip (quando publicado)
pip install maquinaweb-shared-auth

# Ou modo desenvolvimento
pip install -e /path/to/maquinaweb-shared-auth
```

### 2. Adicionar ao requirements.txt

```txt
Django>=4.2
djangorestframework>=3.14
maquinaweb-shared-auth>=0.2.25
```

---

## ⚙️ Configuração

### 1. Settings do Django

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'rest_framework',
    
    # Adicionar shared_auth
    'shared_auth',
    
    # Suas apps
    'myapp',
]
```

### 2. Configurar Banco de Dados

```python
# settings.py

DATABASES = {
    'default': {
        # Banco do sistema atual
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'meu_sistema_db',
        'USER': 'meu_user',
        'PASSWORD': 'senha',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'auth_db': {
        # Banco centralizado de autenticação (READ-ONLY)
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sistema_auth_db',
        'USER': 'readonly_user',
        'PASSWORD': 'senha_readonly',
        'HOST': 'auth-server.example.com',
        'PORT': '5432',
    }
}

# Router para direcionar queries
DATABASE_ROUTERS = ['shared_auth.router.SharedAuthRouter']
```

### 3. Configurar Autenticação (DRF)

```python
# settings.py

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'shared_auth.authentication.SharedTokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'shared_auth.permissions.IsAuthenticated',
    ],
}
```

### 4. Configurar Middleware (Opcional)

```python
# settings.py

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    
    # Middlewares da shared_auth
    'shared_auth.middleware.SharedAuthMiddleware',
    'shared_auth.middleware.OrganizationMiddleware',
    
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
```

### 5. Configurar Tabelas (Opcional)

```python
# settings.py

# Customizar nomes das tabelas (se necessário)
SHARED_AUTH_ORGANIZATION_TABLE = 'organization_organization'
SHARED_AUTH_USER_TABLE = 'auth_user'
SHARED_AUTH_MEMBER_TABLE = 'organization_member'
SHARED_AUTH_TOKEN_TABLE = 'authtoken_token'
```

### 6. Criar Usuário Read-Only no PostgreSQL

```sql
-- No servidor de autenticação
CREATE USER readonly_user WITH PASSWORD 'senha_segura_aqui';

-- Conceder permissões
GRANT CONNECT ON DATABASE sistema_auth_db TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Para tabelas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO readonly_user;

-- Garantir read-only
ALTER USER readonly_user SET default_transaction_read_only = on;
```

---

## 🚀 Uso Básico

### 1. Models com Mixins

```python
# myapp/models.py
from django.db import models
from shared_auth.mixins import OrganizationUserMixin, TimestampedMixin
from shared_auth.managers import BaseAuthManager

class Pedido(OrganizationUserMixin, TimestampedMixin):
    """Model que pertence a organização e usuário"""
    
    numero = models.CharField(max_length=20, unique=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    
    objects = BaseAuthManager()
    
    def __str__(self):
        return f"Pedido {self.numero}"
```

**O que você ganha automaticamente:**
- ✅ Campos: `organization_id`, `user_id`, `created_at`, `updated_at`
- ✅ Properties: `organization`, `user`, `organization_name`, `user_email`
- ✅ Métodos: `validate_user_belongs_to_organization()`, `user_can_access()`

### 2. Serializers com Dados Aninhados

```python
# myapp/serializers.py
from rest_framework import serializers
from shared_auth.serializers import OrganizationUserSerializerMixin
from .models import Pedido

class PedidoSerializer(OrganizationUserSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'valor_total', 'status',
            'organization',  # Objeto completo
            'user',          # Objeto completo
            'created_at',
        ]
        read_only_fields = ['organization', 'user', 'created_at']
```

**Response JSON:**
```json
{
  "id": 1,
  "numero": "PED-001",
  "valor_total": "1500.00",
  "status": "pending",
  "organization": {
    "id": 123,
    "name": "Empresa XYZ Ltda",
    "fantasy_name": "XYZ",
    "cnpj": "12.345.678/0001-90",
    "email": "contato@xyz.com",
    "is_active": true
  },
  "user": {
    "id": 456,
    "username": "joao.silva",
    "email": "joao@xyz.com",
    "full_name": "João Silva",
    "is_active": true
  },
  "created_at": "2025-10-01T10:00:00Z"
}
```

### 3. ViewSets com Organização

```python
# myapp/views.py
from rest_framework import viewsets
from shared_auth.mixins import LoggedOrganizationMixin
from shared_auth.permissions import HasActiveOrganization, IsSameOrganization
from .models import Pedido
from .serializers import PedidoSerializer

class PedidoViewSet(LoggedOrganizationMixin, viewsets.ModelViewSet):
    """
    ViewSet que filtra automaticamente por organização logada
    """
    serializer_class = PedidoSerializer
    permission_classes = [HasActiveOrganization, IsSameOrganization]
    
    # get_queryset() já filtra por organization_id automaticamente
    # perform_create() já adiciona organization_id automaticamente
```

### 4. Acessar Dados Compartilhados

```python
# Em qualquer lugar do código
from shared_auth.models import SharedOrganization, User, SharedMember

# Buscar organização
org = SharedOrganization.objects.get_or_fail(123)
print(org.name)  # "Empresa XYZ"
print(org.members)  # QuerySet de membros

# Buscar usuário
user = User.objects.get_or_fail(456)
print(user.email)  # "joao@xyz.com"
print(user.organizations)  # Organizações do usuário

# Verificar membership
member = SharedMember.objects.filter(
    user_id=456,
    organization_id=123
).first()

if member:
    print(f"{member.user.email} é membro de {member.organization.name}")
```

---

## 📚 Guias Avançados

### Mixins para Models

#### 1. OrganizationMixin
Para models que pertencem apenas a uma organização.

```python
from shared_auth.mixins import OrganizationMixin

class EmpresaConfig(OrganizationMixin):
    tema_cor = models.CharField(max_length=7, default='#3490dc')
    logo = models.ImageField(upload_to='logos/')
    
# Uso
config = EmpresaConfig.objects.create(organization_id=123, tema_cor='#ff0000')
print(config.organization.name)  # Acesso automático
print(config.organization_members)  # Membros da organização
```

#### 2. UserMixin
Para models que pertencem apenas a um usuário.

```python
from shared_auth.mixins import UserMixin

class UserPreferences(UserMixin):
    theme = models.CharField(max_length=20, default='light')
    notifications_enabled = models.BooleanField(default=True)

# Uso
prefs = UserPreferences.objects.create(user_id=456, theme='dark')
print(prefs.user.email)
print(prefs.user_full_name)
```

#### 3. OrganizationUserMixin
Para models que pertencem a organização E usuário (mais comum).

```python
from shared_auth.mixins import OrganizationUserMixin, TimestampedMixin

class Tarefa(OrganizationUserMixin, TimestampedMixin):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    status = models.CharField(max_length=20, default='pending')

# Uso
tarefa = Tarefa.objects.create(
    organization_id=123,
    user_id=456,
    titulo='Implementar feature X'
)

# Validações
if tarefa.validate_user_belongs_to_organization():
    print("✓ Usuário pertence à organização")

if tarefa.user_can_access(outro_user_id):
    print("✓ Outro usuário pode acessar")
```

### Managers Otimizados

```python
from shared_auth.managers import BaseAuthManager

class Pedido(OrganizationUserMixin):
    # ...
    objects = BaseAuthManager()

# Filtrar por organização
pedidos = Pedido.objects.for_organization(123)

# Filtrar por usuário
meus_pedidos = Pedido.objects.for_user(456)

# Prefetch automático (evita N+1)
pedidos = Pedido.objects.with_auth_data()
for pedido in pedidos:
    print(pedido.organization.name)  # Sem query adicional
    print(pedido.user.email)  # Sem query adicional
```

### Serializers - Variações

#### Versão Completa (Detail)
```python
from shared_auth.serializers import OrganizationUserSerializerMixin

class PedidoDetailSerializer(OrganizationUserSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = ['id', 'numero', 'organization', 'user', 'created_at']
```

#### Versão Simplificada (List)
```python
from shared_auth.serializers import (
    OrganizationSimpleSerializerMixin,
    UserSimpleSerializerMixin
)

class PedidoListSerializer(
    OrganizationSimpleSerializerMixin,
    UserSimpleSerializerMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = Pedido
        fields = ['id', 'numero', 'organization', 'user']
    
# Response com dados reduzidos
{
  "id": 1,
  "numero": "PED-001",
  "organization": {
    "id": 123,
    "name": "Empresa XYZ",
    "cnpj": "12.345.678/0001-90"
  },
  "user": {
    "id": 456,
    "email": "joao@xyz.com",
    "full_name": "João Silva"
  }
}
```

#### Customização Avançada
```python
class PedidoSerializer(OrganizationUserSerializerMixin, serializers.ModelSerializer):
    
    def get_organization(self, obj):
        """Override para adicionar campos customizados"""
        org_data = super().get_organization(obj)
        
        if org_data:
            # Adicionar dados extras
            org_data['logo_url'] = f"/logos/{obj.organization_id}.png"
            org_data['member_count'] = obj.organization.members.count()
        
        return org_data
```

### Middleware

#### SharedAuthMiddleware
Autentica usuário baseado no token.

```python
# settings.py
MIDDLEWARE = [
    # ...
    'shared_auth.middleware.SharedAuthMiddleware',
]
```

**Busca token em:**
- Header: `Authorization: Token <token>`
- Header: `X-Auth-Token: <token>`
- Cookie: `auth_token`

**Adiciona ao request:**
- `request.user` - Objeto User autenticado
- `request.auth` - Token object

#### OrganizationMiddleware
Adiciona organização logada ao request.

```python
# settings.py
MIDDLEWARE = [
    'shared_auth.middleware.SharedAuthMiddleware',
    'shared_auth.middleware.OrganizationMiddleware',  # Depois do Auth
]
```

**Busca organização:**
1. Header `X-Organization: <org_id>`
2. Primeira organização do usuário autenticado

**Adiciona ao request:**
- `request.organization_id` - ID da organização
- `request.organization` - Objeto SharedOrganization

**Uso em views:**
```python
def my_view(request):
    org_id = request.organization_id
    org = request.organization
    
    if org:
        print(f"Organização logada: {org.name}")
```

### Permissions

```python
from shared_auth.permissions import (
    IsAuthenticated,
    HasActiveOrganization,
    IsSameOrganization,
    IsOwnerOrSameOrganization,
)

class PedidoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,           # Requer autenticação
        HasActiveOrganization,     # Requer organização ativa
        IsSameOrganization,        # Objeto da mesma org
    ]
    
# Ou combinações
class TarefaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrSameOrganization]
    # Permite se for dono OU da mesma organização
```

### Authentication

```python
# Em qualquer view/viewset DRF
from shared_auth.authentication import SharedTokenAuthentication

class MyAPIView(APIView):
    authentication_classes = [SharedTokenAuthentication]
    
    def get(self, request):
        user = request.user  # User autenticado
        token = request.auth  # SharedToken object
        
        return Response({
            'user': user.email,
            'token_created': token.created
        })
```

---

## 🔍 API Reference

### Models

#### SharedOrganization

```python
from shared_auth.models import SharedOrganization

# Campos
org.id
org.name
org.fantasy_name
org.cnpj
org.email
org.telephone
org.cellphone
org.image_organization
org.is_branch
org.main_organization_id
org.created_at
org.updated_at
org.deleted_at

# Properties
org.main_organization  # SharedOrganization | None
org.branches  # QuerySet[SharedOrganization]
org.members  # QuerySet[SharedMember]
org.users  # QuerySet[User]

# Métodos
org.is_active()  # bool
```

#### User

```python
from shared_auth.models import User

# Campos (AbstractUser + custom)
user.id
user.username
user.email
user.first_name
user.last_name
user.is_active
user.is_staff
user.is_superuser
user.date_joined
user.last_login
user.avatar
user.createdat
user.updatedat
user.deleted_at

# Properties
user.organizations  # QuerySet[SharedOrganization]

# Métodos
user.get_full_name()  # str
user.get_org(organization_id)  # SharedOrganization | raise
```

#### SharedMember

```python
from shared_auth.models import SharedMember

# Campos
member.id
member.user_id
member.organization_id
member.metadata  # JSONField

# Properties
member.user  # User
member.organization  # SharedOrganization
```

#### SharedToken

```python
from shared_auth.models import SharedToken

# Campos
token.key  # Primary Key
token.user_id
token.created

# Properties
token.user  # User

# Métodos
token.is_valid()  # bool
```

### Managers

#### SharedOrganizationManager

```python
from shared_auth.models import SharedOrganization

SharedOrganization.objects.get_or_fail(123)  # Org | raise OrganizationNotFoundError
SharedOrganization.objects.active()  # QuerySet (deleted_at is null)
SharedOrganization.objects.branches()  # QuerySet (is_branch=True)
SharedOrganization.objects.main_organizations()  # QuerySet (is_branch=False)
SharedOrganization.objects.by_cnpj('12.345.678/0001-90')  # Org | None
```

#### UserManager

```python
from shared_auth.models import User

User.objects.get_or_fail(456)  # User | raise UserNotFoundError
User.objects.active()  # QuerySet (is_active=True, deleted_at is null)
User.objects.by_email('user@example.com')  # User | None
```

#### SharedMemberManager

```python
from shared_auth.models import SharedMember

SharedMember.objects.for_user(456)  # QuerySet
SharedMember.objects.for_organization(123)  # QuerySet
```

#### BaseAuthManager (para seus models)

```python
# Quando usa OrganizationMixin
Model.objects.for_organization(123)  # QuerySet
Model.objects.for_organizations([123, 456])  # QuerySet
Model.objects.with_organization_data()  # List com prefetch

# Quando usa UserMixin
Model.objects.for_user(456)  # QuerySet
Model.objects.for_users([456, 789])  # QuerySet
Model.objects.with_user_data()  # List com prefetch

# Quando usa OrganizationUserMixin
Model.objects.with_auth_data()  # List com prefetch de org e user
Model.objects.create_with_validation(
    organization_id=123,
    user_id=456,
    **kwargs
)  # Valida membership antes de criar
```

### Exceptions

```python
from shared_auth.exceptions import (
    SharedAuthError,
    OrganizationNotFoundError,
    UserNotFoundError,
    DatabaseConnectionError,
)

try:
    org = SharedOrganization.objects.get_or_fail(999)
except OrganizationNotFoundError as e:
    print(e)  # "Organização com ID 999 não encontrada"
```

---

## 🎯 Casos de Uso Reais

### Sistema de Pedidos Multi-Tenant

```python
# models.py
from shared_auth.mixins import OrganizationUserMixin, TimestampedMixin

class Pedido(OrganizationUserMixin, TimestampedMixin):
    numero = models.CharField(max_length=20, unique=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    
    objects = BaseAuthManager()

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens')
    produto = models.CharField(max_length=200)
    quantidade = models.IntegerField()
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)

# serializers.py
from shared_auth.serializers import OrganizationUserSerializerMixin

class ItemPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedido
        fields = ['id', 'produto', 'quantidade', 'valor_unitario']

class PedidoSerializer(OrganizationUserSerializerMixin, serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'valor_total', 'status',
            'organization', 'user', 'itens', 'created_at'
        ]

# views.py
from shared_auth.mixins import LoggedOrganizationMixin
from shared_auth.permissions import HasActiveOrganization

class PedidoViewSet(LoggedOrganizationMixin, viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [HasActiveOrganization]
    
    def get_queryset(self):
        # Já filtra por organization_id automaticamente
        return super().get_queryset().with_auth_data()
```

### Sistema de Tarefas com Responsáveis

```python
# models.py
class Tarefa(OrganizationUserMixin, TimestampedMixin):
    """
    user_id = criador
    responsavel_id = quem vai executar
    """
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    responsavel_id = models.IntegerField()
    status = models.CharField(max_length=20, default='pending')
    
    objects = BaseAuthManager()
    
    @property
    def responsavel(self):
        """Acessa usuário responsável"""
        if not hasattr(self, '_cached_responsavel'):
            from shared_auth.models import User
            self._cached_responsavel = User.objects.get_or_fail(self.responsavel_id)
        return self._cached_responsavel

# serializers.py
class TarefaSerializer(OrganizationUserSerializerMixin, serializers.ModelSerializer):
    responsavel = serializers.SerializerMethodField()
    
    def get_responsavel(self, obj):
        try:
            resp = obj.responsavel
            return {
                'id': resp.pk,
                'email': resp.email,
                'full_name': resp.get_full_name(),
            }
        except:
            return None
    
    class Meta:
        model = Tarefa
        fields = [
            'id', 'titulo', 'descricao', 'status',
            'organization',  # Organização dona
            'user',  # Criador
            'responsavel',  # Executor
            'created_at'
        ]
```

---

## 🔧 Troubleshooting

### Problema: Queries lentas (N+1)

**Solução:** Use os managers com prefetch

```python
# ❌ Ruim - Causa N+1
pedidos = Pedido.objects.all()
for pedido in pedidos:
    print(pedido.organization.name)  # Query por item!

# ✅ Bom - 3 queries total
pedidos = Pedido.objects.with_auth_data()
for pedido in pedidos:
    print(pedido.organization.name)  # Sem query adicional
```

### Problema: OrganizationNotFoundError

**Causa:** ID de organização inválido ou deletada

**Solução:**
```python
# Usar try/except
try:
    org = SharedOrganization.objects.get_or_fail(org_id)
except OrganizationNotFoundError:
    # Tratar erro
    return Response({'error': 'Organização não encontrada'}, status=404)

# Ou usar filter
org = SharedOrganization.objects.filter(pk=org_id).first()
if not org:
    # Tratar
```

### Problema: Erro de conexão com auth_db

**Solução:** Verificar configuração do database router e permissões

```python
# Testar conexão
from django.db import connections

connection = connections['auth_db']
with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    print("✓ Conexão OK")
```

---

## 📝 Changelog

### v0.2.25
- ✨ Adicionado suporte a imagens (avatar, logo)
- ✨ StorageBackend para arquivos compartilhados
- 🐛 Correções nos serializers
- 📚 Documentação melhorada

### v0.2.0
- ✨ Middlewares: SharedAuthMiddleware, OrganizationMiddleware
- ✨ Permissions customizadas
- ✨ Managers otimizados com prefetch
- ✨ Serializer mixins com dados aninhados

### v0.1.0
- 🎉 Versão inicial
- ✨ Models compartilhados
- ✨ Mixins básicos
- ✨ Autenticação via token

---

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request.

---

## 📧 Suporte

Para suporte, abra uma issue no GitHub ou entre em contato com a equipe Maquinaweb.

---

**Desenvolvido com ❤️ por Maquinaweb**
