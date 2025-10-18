import logging

from django.db import models

from .services import AuditConfig, AuditService

logger = logging.getLogger("django_tracker.audit")


def _connect_m2m_signals(cls, audit_config: AuditConfig):
    """Conecta señales para auditar cambios en relaciones M2M."""

    def m2m_changed_handler(sender, instance, action, reverse, model, pk_set, **kwargs):
        if not audit_config.audit_updates:
            return

        field_name = _get_m2m_field_name(instance, sender)
        if not field_name or field_name in (audit_config.excluded_fields or []):
            return

        if action in ["pre_add", "pre_remove", "pre_clear"]:
            _capture_m2m_previous_state(instance, field_name, action)
        elif action in ["post_add", "post_remove", "post_clear"]:
            _handle_m2m_update(instance, field_name, action, audit_config)

    for field in cls._meta.many_to_many:
        models.signals.m2m_changed.connect(
            m2m_changed_handler,
            sender=getattr(cls, field.name).through,
            dispatch_uid=f"m2m_change_{cls.__name__}_{field.name}",
            weak=False,
        )


def _get_m2m_field_name(instance, sender):
    """Identifica el nombre del campo M2M basado en el sender."""
    for field in instance._meta.many_to_many:
        if sender == getattr(instance, field.name).through:
            return field.name
    return None


def _capture_m2m_previous_state(instance, field_name, action):
    """Guarda el estado previo de un campo M2M antes de cambios."""
    if not hasattr(instance, "_m2m_previous_state"):
        instance._m2m_previous_state = {}
    if not hasattr(instance, "_m2m_previous_objects"):
        instance._m2m_previous_objects = {}

    instance._m2m_previous_state[field_name] = set(
        getattr(instance, field_name).values_list("pk", flat=True)
    )
    instance._m2m_previous_objects[field_name] = list(
        getattr(instance, field_name).all()
    )

    logger.info(
        f"M2M {action} - Captured state for "
        f"{instance.__class__.__name__}.{field_name} (ID: {instance.pk}): "
        f"{instance._m2m_previous_state[field_name]}"
    )


def _handle_m2m_update(instance, field_name, action, audit_config: AuditConfig):
    """Compara estado previo y actual de relaciones M2M."""
    if (
        not hasattr(instance, "_m2m_previous_state")
        or field_name not in instance._m2m_previous_state
    ):
        logger.warning(f"No previous state found for {field_name} in {action} handler")
        return

    current = set(getattr(instance, field_name).values_list("pk", flat=True))
    previous = instance._m2m_previous_state.get(field_name, set())

    added = current - previous
    removed = previous - current

    if added or removed:
        m2m_changes = {field_name: {"old": list(previous), "new": list(current)}}
        metadata = {"added": list(added), "removed": list(removed)}

        if not hasattr(instance, "_m2m_accumulated_changes"):
            instance._m2m_accumulated_changes = {}

        instance._m2m_accumulated_changes.update(m2m_changes)

        logger.info(
            f"M2M Update for {instance.__class__.__name__} (ID: {instance.pk})\n"
            f"Changes detected: {m2m_changes}"
        )

        # Create the registry
        AuditService.audit_update(
            instance=instance,
            changes=m2m_changes,
            level=audit_config.level,
            metadata={**metadata},
        )
