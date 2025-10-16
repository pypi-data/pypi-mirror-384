from rest_framework.exceptions import APIException
"""
Exceções customizadas
"""
class SharedAuthError(APIException):
    """Erro base da biblioteca"""
    pass


class OrganizationNotFoundError(SharedAuthError):
    status_code = 404
    default_detail = 'Organização não encontrada.'
    default_code = 'organization_not_found'

class UserNotFoundError(SharedAuthError):
    status_code = 404
    default_detail = 'Usuário não encontrado.'
    default_code = 'user_not_found'

class DatabaseConnectionError(SharedAuthError):
    status_code = 500
    default_detail = 'Erro interno'
    default_code = 'internal_error'