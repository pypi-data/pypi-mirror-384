from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Creado"
    UPDATE = "UPDATE", "Modificado"
    DELETE = "DELETE", "Eliminado"
    READ = "READ", "Consultado"


class AuditLevel(models.TextChoices):
    LOW = "LOW", "Bajo"
    MEDIUM = "MEDIUM", "Medio"
    HIGH = "HIGH", "Alto"
    CRITICAL = "CRITICAL", "Crítico"


# Campos que se excluyen por defecto de la auditoría
DEFAULT_EXCLUDED_FIELDS = [
    "id",
    "created_at",
    "updated_at",
    "modified",
    "created",
    "password",
    "last_login",
]

# Campos sensibles que se enmascaran
SENSITIVE_FIELDS = [
    "password",
    "token",
    "secret",
    "key",
    "credit_card",
    "ssn",
    "social_security",
    "cvv",
]
