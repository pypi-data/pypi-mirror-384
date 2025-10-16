class CurcumaException(Exception):
    """Conflict exception"""


class ConflictException(CurcumaException):
    """Conflict exception"""


class NotFoundException(CurcumaException):
    """Not found exception"""


class PermissionException(CurcumaException):
    """Not enough permission exception"""


class TemplateParameterException(CurcumaException):
    """Template parameter missing exception"""
