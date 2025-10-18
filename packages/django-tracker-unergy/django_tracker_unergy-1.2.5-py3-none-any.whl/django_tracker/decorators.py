import logging
from typing import List, Optional

from django.db import models

from .constants import AuditLevel
from .interceptors import _intercept_delete, _intercept_save
from .m2m import _connect_m2m_signals
from .services import AuditConfig

logger = logging.getLogger("django_tracker.audit")


# ===============================
# Decorador principal
# ===============================


def auditable(
    tracked_fields: Optional[List[str]] = None,
    excluded_fields: Optional[List[str]] = None,
    audit_creates: bool = True,
    audit_updates: bool = True,
    audit_deletes: bool = True,
    audit_reads: bool = False,
    level: str = AuditLevel.MEDIUM,
):
    """
    Decorador mejorado para auditoría de modelos Django.

    Args:
        tracked_fields: Campos específicos a trackear.
        excluded_fields: Campos a excluir del tracking.
        audit_creates: Si auditar creaciones.
        audit_updates: Si auditar actualizaciones.
        audit_deletes: Si auditar eliminaciones.
        audit_reads: Si auditar lecturas.
        level: Nivel de auditoría.
    """

    def decorator(cls):
        if not issubclass(cls, models.Model):
            raise ValueError(
                "The auditable decorator can only be applied to Django models"
            )

        audit_config = AuditConfig(
            tracked_fields=tracked_fields,
            excluded_fields=excluded_fields,
            audit_creates=audit_creates,
            audit_updates=audit_updates,
            audit_deletes=audit_deletes,
            audit_reads=audit_reads,
            level=level,
        )
        cls._audit_config = audit_config

        if audit_config.audit_creates or audit_config.audit_updates:
            _intercept_save(cls, audit_config)

        if audit_config.audit_deletes:
            _intercept_delete(cls, audit_config)

        # Manejo de relaciones M2M
        _connect_m2m_signals(cls, audit_config)
        return cls

    return decorator
