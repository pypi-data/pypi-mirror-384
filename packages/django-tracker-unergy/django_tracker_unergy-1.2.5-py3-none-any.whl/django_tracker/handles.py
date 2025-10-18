import logging

from django.forms.models import model_to_dict

from .services import AuditConfig, AuditService

logger = logging.getLogger("django_tracker.audit")


def _handle_create(instance, cls, audit_config: AuditConfig):
    """Maneja auditoría de creación de registros."""
    logger.info(f"Creating new {cls.__name__} with ID: {instance.pk}")
    AuditService.audit_create(
        instance=instance,
        excluded_fields=audit_config.excluded_fields,
        level=audit_config.level,
    )


def _handle_update(instance, cls, old_instance, audit_config: AuditConfig):
    """Maneja auditoría de actualizaciones de registros."""
    tracked = (
        audit_config.tracked_fields
        if audit_config.tracked_fields
        else [f.name for f in instance._meta.fields]
    )

    changes = {}
    logger.info(f"Tracking fields for {cls.__name__}: {tracked}")

    for field in tracked:
        if field in (audit_config.excluded_fields or []):
            continue

        old_value = getattr(old_instance, field, None)
        new_value = getattr(instance, field, None)
        if old_value != new_value:
            changes[field] = {"old": str(old_value), "new": str(new_value)}

    if changes:
        logger.info(
            f"Updating {cls.__name__} with ID: {instance.pk}\n"
            f"Changes detected: {changes}"
        )

    AuditService.audit_update(
        instance=instance,
        changes=changes,
        level=audit_config.level,
        metadata={
            "old_instance": str(model_to_dict(old_instance)),
            "new_instance": str(model_to_dict(instance)),
        },
    )
