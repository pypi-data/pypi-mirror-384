# Mantener el archivo original para compatibilidad hacia atrás
from .decorators import legacy_auditable as auditable

# Re-exportar para compatibilidad
__all__ = ["auditable"]
