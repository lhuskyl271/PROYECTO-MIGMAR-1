from django.contrib import admin
from .models import (
    Unidad, Operador, CargaDiesel, CargaAceite, CargaUrea, 
    CompraSuministro, ChecklistInspeccion, LlantasInspeccion, 
    LlantaDetalle, ProcesoCarga, AjusteInventario, AsignacionRevision,
    EntregaSuministros, AlertaInventario, ChecklistCorreccion, TareaCorrectiva
)

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'placas', 'km_actual', 'tipo_combustible']
    search_fields = ['nombre', 'placas', 'vin']
    list_filter = ['tipo', 'tipo_combustible', 'unidad_negocio']

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido']
    search_fields = ['nombre', 'apellido']

@admin.register(CargaDiesel)
class CargaDieselAdmin(admin.ModelAdmin):
    # Se agregan las nuevas fotos y el km_actual que ahora vive aquí
    list_display = ['unidad', 'fecha', 'lts_diesel', 'km_actual', 'rendimiento']
    list_filter = ['unidad', 'fecha']
    search_fields = ['unidad__nombre']
    readonly_fields = ['costo'] # El costo se calcula automáticamente

@admin.register(CargaAceite)
class CargaAceiteAdmin(admin.ModelAdmin):
    list_display = ['unidad', 'fecha', 'cantidad', 'motivo']
    list_filter = ['unidad', 'fecha']

@admin.register(CargaUrea)
class CargaUreaAdmin(admin.ModelAdmin):
    list_display = ['unidad', 'fecha', 'litros_cargados']
    list_filter = ['unidad', 'fecha']

@admin.register(CompraSuministro)
class CompraSuministroAdmin(admin.ModelAdmin):
    list_display = ['fecha_compra', 'proveedor', 'tipo_suministro', 'cantidad', 'precio']
    list_filter = ['tipo_suministro', 'proveedor']

# --- Corrección para ChecklistInspeccion ---
# Eliminamos referencias a foto_odometro, foto_sticker, etc.
@admin.register(ChecklistInspeccion)
class ChecklistInspeccionAdmin(admin.ModelAdmin):
    list_display = ['unidad', 'fecha', 'operador', 'tecnico', 'es_dummy']
    list_filter = ['unidad', 'tecnico', 'fecha', 'es_dummy']
    search_fields = ['unidad__nombre']

class LlantaDetalleInline(admin.TabularInline):
    model = LlantaDetalle
    extra = 0

# --- Corrección para LlantasInspeccion ---
# Eliminamos 'km' de list_display
@admin.register(LlantasInspeccion)
class LlantasInspeccionAdmin(admin.ModelAdmin):
    list_display = ['unidad', 'fecha', 'tecnico', 'es_dummy'] # SIN 'km'
    list_filter = ['unidad', 'fecha', 'es_dummy']
    inlines = [LlantaDetalleInline]

@admin.register(ProcesoCarga)
class ProcesoCargaAdmin(admin.ModelAdmin):
    list_display = ['unidad', 'fecha_inicio', 'status', 'tecnico_inicia', 'encargado_finaliza']
    list_filter = ['status', 'fecha_inicio']

@admin.register(AjusteInventario)
class AjusteInventarioAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'tipo_suministro', 'tipo_ajuste', 'cantidad', 'responsable']
    list_filter = ['tipo_suministro', 'tipo_ajuste']

@admin.register(AsignacionRevision)
class AsignacionRevisionAdmin(admin.ModelAdmin):
    list_display = ['unidad', 'fecha_revision', 'status', 'tipo_programacion']
    list_filter = ['status', 'fecha_revision', 'tipo_programacion']

@admin.register(EntregaSuministros)
class EntregaSuministrosAdmin(admin.ModelAdmin):
    list_display = ['operador', 'fecha_entrega', 'cant_cinchos', 'unidad', 'entregado']
    list_filter = ['entregado', 'fecha_entrega']

@admin.register(AlertaInventario)
class AlertaInventarioAdmin(admin.ModelAdmin):
    list_display = ['tipo_suministro', 'activa', 'nivel_reportado', 'ultimo_aviso']

@admin.register(ChecklistCorreccion)
class ChecklistCorreccionAdmin(admin.ModelAdmin):
    list_display = ['inspeccion', 'nombre_campo', 'status', 'fecha_correccion', 'corregido_por']
    list_filter = ['status']

@admin.register(TareaCorrectiva)
class TareaCorrectivaAdmin(admin.ModelAdmin):
    list_display = ['asignacion', 'tipo_mantenimiento', 'status', 'usuario_asignado', 'fecha_limite']
    list_filter = ['tipo_mantenimiento', 'status']