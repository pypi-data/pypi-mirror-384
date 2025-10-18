from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .constants import AuditAction, AuditLevel
from .managers import AuditLogManager


class AuditLog(models.Model):
    """Modelo principal de auditoría con mayor flexibilidad"""

    # Relación genérica al objeto auditado
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255, verbose_name="ID del objeto")
    content_object = GenericForeignKey("content_type", "object_id")

    # Información de la acción
    action = models.CharField(
        max_length=10, choices=AuditAction.choices, default=AuditAction.UPDATE
    )
    level = models.CharField(
        max_length=10, choices=AuditLevel.choices, default=AuditLevel.MEDIUM
    )

    # Cambios realizados (JSON)
    changes = models.JSONField(default=dict, blank=True)

    # Información del usuario
    user_id = models.PositiveIntegerField(null=True, blank=True)
    username = models.CharField(max_length=150, default="anonymous")
    user_email = models.EmailField(null=True, blank=True)

    # Metadatos adicionales
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AuditLogManager()

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user_id", "username"]),
            models.Index(fields=["action"]),
            models.Index(fields=["level"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.content_type.model}({self.object_id}) by {self.username}"

    @property
    def model_name(self):
        """Compatibilidad con el modelo anterior"""
        return self.content_type.model

    def get_changes_display(self):
        """Muestra los cambios de forma legible"""
        if not self.changes:
            return "Sin cambios específicos"

        display = []
        for field, change in self.changes.items():
            old_val = change.get("old_value", "N/A")
            new_val = change.get("new_value", "N/A")
            display.append(f"{field}: {old_val} → {new_val}")

        return "; ".join(display)
