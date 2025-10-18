from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class AuditLogQuerySet(models.QuerySet):
    """QuerySet personalizado para auditoría"""

    def for_model(self, model_class):
        """Filtrar por tipo de modelo"""
        content_type = ContentType.objects.get_for_model(model_class)
        return self.filter(content_type=content_type)

    def for_object(self, obj):
        """Filtrar por objeto específico"""
        content_type = ContentType.objects.get_for_model(obj.__class__)
        return self.filter(content_type=content_type, object_id=obj.pk)

    def by_user(self, user_id):
        """Filtrar por usuario"""
        return self.filter(user_id=user_id)

    def by_action(self, action):
        """Filtrar por acción"""
        return self.filter(action=action)

    def recent(self, days=30):
        """Logs recientes"""
        since = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=since)

    def critical(self):
        """Solo logs críticos"""
        return self.filter(level="CRITICAL")


class AuditLogManager(models.Manager):
    """Manager personalizado para auditoría"""

    def get_queryset(self):
        return AuditLogQuerySet(self.model, using=self._db)

    def for_model(self, model_class):
        return self.get_queryset().for_model(model_class)

    def for_object(self, obj):
        return self.get_queryset().for_object(obj)

    def by_user(self, user_id):
        return self.get_queryset().by_user(user_id)

    def recent(self, days=30):
        return self.get_queryset().recent(days)

    def create_audit(self, instance, action, changes=None, **kwargs):
        """Método helper para crear logs de auditoría"""
        from .utils import AuditUserExtractor

        user_info = AuditUserExtractor.get_user_info()
        content_type = ContentType.objects.get_for_model(instance.__class__)

        return self.create(
            content_type=content_type,
            object_id=instance.pk,
            action=action,
            changes=changes or {},
            user_id=user_info["user_id"],
            username=user_info["username"],
            user_email=user_info["email"],
            **kwargs,
        )
