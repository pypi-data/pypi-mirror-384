import json
from typing import Any, Dict, List, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from .constants import SENSITIVE_FIELDS
from .middleware import get_current_user


class AuditDataSerializer:
    """Serializa datos para auditoría de forma segura"""

    @staticmethod
    def serialize_value(value: Any) -> str:
        """Serializa un valor a string de forma segura"""
        if value is None:
            return None

        if isinstance(value, (str, int, float, bool)):
            return str(value)

        if isinstance(value, models.Model):
            return f"{value.__class__.__name__}(id={value.pk})"

        try:
            return json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def mask_sensitive_data(field_name: str, value: Any) -> Any:
        """Enmascara datos sensibles"""
        if any(sensitive in field_name.lower() for sensitive in SENSITIVE_FIELDS):
            return "***MASKED***" if value else None
        return value

    @staticmethod
    def get_field_changes(
        old_instance: models.Model,
        new_instance: models.Model,
        tracked_fields: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Obtiene los cambios entre dos instancias"""
        changes = {}

        if not tracked_fields:
            tracked_fields = [f.name for f in new_instance._meta.fields]

        for field_name in tracked_fields:
            old_value = getattr(old_instance, field_name, None)
            new_value = getattr(new_instance, field_name, None)

            if old_value != new_value:
                changes[field_name] = {
                    "old": AuditDataSerializer.mask_sensitive_data(
                        field_name, AuditDataSerializer.serialize_value(old_value)
                    ),
                    "new": AuditDataSerializer.mask_sensitive_data(
                        field_name, AuditDataSerializer.serialize_value(new_value)
                    ),
                }

        return changes


class AuditUserExtractor:
    """Extrae información del usuario para auditoría"""

    @staticmethod
    def get_user_info(request=None) -> Dict[str, Any]:
        """Obtiene información del usuario actual"""

        user = get_current_user()

        return {
            "user_id": getattr(user, "id", None) if user else None,
            "username": getattr(user, "username", "anonymous") if user else "anonymous",
            "email": getattr(user, "email", None) if user else None,
        }
