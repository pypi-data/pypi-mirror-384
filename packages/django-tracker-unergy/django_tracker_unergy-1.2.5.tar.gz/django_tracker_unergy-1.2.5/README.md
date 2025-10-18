# Django Tracker

Django Tracker is a middleware for Django that automatically audits and logs all model changes made through user requests. It records the user responsible, the fields changed, and other useful information for tracking data changes.

## Installation

```bash
pip install django-tracker-unergy
```

## Setup

1. Add `'django_tracker'` to `INSTALLED_APPS` in your `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'django_tracker',
]
```
and add the middleware
```python
MIDDLEWARE = [
    # ...
    'django_tracker.middleware.CurrentUserMiddleware'
]
```

2. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate django_tracker
```

## Usage

### Auditable Decorator

```python
from django_tracker.decorators import auditable

@auditable(
    tracked_fields=['field1', 'field2'],
    exclude_fiels=["created_at", "updated_at"]
    audit_creates=True,
    audit_updates=True,
    audit_deletes=True,
    level=AuditLevel.MEDIUM
)
class MyModel(models.Model):
    field1 = models.CharField(max_length=100)
    field2 = models.IntegerField()
    # And the control attrb
```

### Querying Audit Logs

You can view audit logs in the Django admin or directly from the model:

```python
from django_tracker.models import AuditLog

# Get changes for a specific object
logs = AuditLog.objects.filter(
    content_type__model='mymodel',
    object_id=obj_id
)

# Get changes by user
logs = AuditLog.objects.filter(username='username')
```

## License

MIT License. See LICENSE file for details.
