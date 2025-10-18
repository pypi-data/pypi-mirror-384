import datetime

from django.contrib import admin
from django.utils import timezone

from .models import AuditLog


class CreatedDateListFilter(admin.SimpleListFilter):
    """Filtro optimizado para fechas recientes"""

    title = "Fecha de creación"
    parameter_name = "created_at"

    def lookups(self, request, model_admin):
        return (
            ("today", "Hoy"),
            ("yesterday", "Ayer"),
            ("this_week", "Esta semana"),
            ("last_week", "Semana pasada"),
            ("this_month", "Este mes"),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()

        if self.value() == "today":
            return queryset.filter(created_at__date=today)
        if self.value() == "yesterday":
            return queryset.filter(created_at__date=today - datetime.timedelta(days=1))
        if self.value() == "this_week":
            start_of_week = today - datetime.timedelta(days=today.weekday())
            return queryset.filter(created_at__date__gte=start_of_week)
        if self.value() == "last_week":
            start_of_last_week = today - datetime.timedelta(days=today.weekday() + 7)
            end_of_last_week = start_of_last_week + datetime.timedelta(days=6)
            return queryset.filter(
                created_at__date__range=[start_of_last_week, end_of_last_week]
            )
        if self.value() == "this_month":
            return queryset.filter(
                created_at__month=today.month, created_at__year=today.year
            )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "action",
        "level",
        "content_type",
        "object_id",
        "username",
        "get_keys_changes",
    ]
    list_display_links = ["created_at", "object_id"]
    list_filter = [CreatedDateListFilter, "action", "level", "content_type", "username"]
    search_fields = ["username", "object_id"]
    readonly_fields = [
        "created_at",
        "content_type",
        "object_id",
        "action",
        "level",
        "changes",
        "user_id",
        "username",
        "user_email",
        "metadata",
    ]

    # Optimizaciones extremas de rendimiento
    list_select_related = ["content_type"]  # Reduce queries para FK
    list_per_page = 100  # Limitar número de registros por página
    show_full_result_count = False  # Evita COUNT(*) extras
    actions = None  # Deshabilitar acciones por lotes
    save_as = False  # Deshabilitar "guardar como"
    save_on_top = False  # No mostrar botones de guardado arriba

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        """
        Consulta extremadamente optimizada para máximo rendimiento
        - Utiliza .defer() para evitar cargar campos grandes como changes y metadata
        - Selecciona solo los campos necesarios según la vista
        - Aprovecha índices para filtrar y ordenar
        """
        qs = super().get_queryset(request)

        # Optimización extrema: cargar lo mínimo necesario según el contexto
        if request.resolver_match.view_name.endswith("changelist"):
            # Para la vista de lista, nunca necesitamos changes ni metadata
            qs = qs.defer("changes", "metadata")
        elif request.resolver_match.view_name.endswith("change"):
            # Para la vista detallada, podemos cargar todo lo necesario
            obj_id = request.resolver_match.kwargs.get("object_id")
            if obj_id:
                qs = qs.filter(id=obj_id)

        return qs

    def get_keys_changes(self, obj):
        """
        Muestra las claves de cambios para una referencia rápida
        """
        if not obj.changes:
            return "_"
        return ", ".join(obj.changes.keys())

    get_keys_changes.short_description = "Campos cambiados"
