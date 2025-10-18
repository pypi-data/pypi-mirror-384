import logging
from functools import wraps

from django.core.exceptions import ObjectDoesNotExist

from .handles import _handle_create, _handle_update
from .services import AuditConfig, AuditService

logger = logging.getLogger("django_tracker.audit")


def _intercept_save(cls, audit_config: AuditConfig):
    """Reemplaza `save` para auditar creaciones y actualizaciones."""
    original_save = cls.save

    @wraps(original_save)
    def new_save(self, *args, **kwargs):
        is_creation = self.pk is None
        old_instance = None

        if not is_creation and audit_config.audit_updates:
            try:
                old_instance = cls.objects.get(pk=self.pk)
            except ObjectDoesNotExist:
                old_instance = None

        result = original_save(self, *args, **kwargs)

        if is_creation and audit_config.audit_creates:
            _handle_create(self, cls, audit_config)
        elif old_instance and audit_config.audit_updates:
            _handle_update(self, cls, old_instance, audit_config)

        return result

    cls.save = new_save


def _intercept_delete(cls, audit_config: AuditConfig):
    """Reemplaza `delete` para auditar eliminaciones."""
    original_delete = cls.delete

    @wraps(original_delete)
    def new_delete(self, *args, **kwargs):
        logger.info(f"Deleting {cls.__name__} instance with ID: {self.pk}")
        AuditService.audit_delete(instance=self, level=audit_config.level)
        return original_delete(self, *args, **kwargs)

    cls.delete = new_delete
