from jwt.exceptions import PyJWTError
class JWTValidationError(PyJWTError):
    """Raised when JWT validation fails."""
    pass


class AccessDeniedError(Exception):
    pass