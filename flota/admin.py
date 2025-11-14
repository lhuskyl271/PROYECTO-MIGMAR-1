# flota/admin.py

from django.contrib import admin
from .models import (
    Operador,
    Unidad,
    CargaDiesel,
    CargaAceite,
    CargaUrea,
    CompraSuministro,
    ChecklistInspeccion,
    
    # --- INICIO: IMPORTACIONES AÑADIDAS ---
    LlantasInspeccion,
    LlantaDetalle,
    ProcesoCarga,
    AjusteInventario,
    AsignacionRevision,
    AlertaInventario,
    ChecklistCorreccion,
    EntregaSuministros,
    TareaCorrectiva,
    # --- FIN: IMPORTACIONES AÑADIDAS ---
)

# =================================================================
# --- CONFIGURACIÓN PARA INSPECCIÓN DE LLANTAS (LO QUE PEDISTE) ---
# =================================================================

class LlantaDetalleInline(admin.TabularInline):
    """
    Esto permite editar los 'LlantaDetalle' (las posiciones 1-6)
    DENTRO del formulario de 'LlantasInspeccion'.
    """
    model = LlantaDetalle
    # Campos que se mostrarán en la tabla de edición
    fields = ['posicion', 'mm', 'marca', 'modelo', 'medida', 'presion']
    
    # 'extra' controla cuántas filas vacías se muestran.
    # 0 es bueno para editar. 6 es bueno si quieres forzar 6 al crear.
    extra = 0 

@admin.register(LlantasInspeccion)
class LlantasInspeccionAdmin(admin.ModelAdmin):
    """
    Configuración principal para el modelo 'LlantasInspeccion'.
    """
    # Columnas que se verán en la lista de inspecciones
    list_display = ('unidad', 'fecha', 'tecnico', 'km', 'es_dummy')
    
    # Filtros que aparecerán a la derecha
    list_filter = ('fecha', 'es_dummy', 'tecnico')
    
    # Campos de búsqueda
    search_fields = ('unidad__nombre', 'tecnico__username')
    
    # ¡La parte más importante!
    # Conecta el inline de 'LlantaDetalle'
    inlines = [LlantaDetalleInline]
    
    # Optimización para los campos de búsqueda (ForeignKey)
    autocomplete_fields = ['unidad', 'tecnico']

# =================================================================
# --- REGISTROS EXISTENTES (MEJORADOS CON @register) ---
# =================================================================

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'modelo', 'placas', 'tipo', 'km_actual')
    list_filter = ('tipo', 'marca', 'unidad_negocio')
    search_fields = ('nombre', 'placas', 'vin', 'modelo')

@admin.register(CargaDiesel)
class CargaDieselAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'fecha', 'operador', 'lts_diesel', 'lts_thermo', 'km_actual')
    list_filter = ('unidad',)
    date_hierarchy = 'fecha'
    autocomplete_fields = ['unidad', 'operador']

@admin.register(CompraSuministro)
class CompraSuministroAdmin(admin.ModelAdmin):
    list_display = ('fecha_compra', 'tipo_suministro', 'proveedor', 'cantidad', 'precio_por_litro', 'precio')
    list_filter = ('tipo_suministro', 'proveedor')
    date_hierarchy = 'fecha_compra'

@admin.register(ChecklistInspeccion)
class ChecklistInspeccionAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'operador', 'tecnico', 'fecha', 'es_dummy')
    list_filter = ('fecha', 'es_dummy', 'tecnico')
    search_fields = ('unidad__nombre', 'operador__nombre')
    autocomplete_fields = ['unidad', 'operador', 'tecnico']

# =================================================================
# --- REGISTROS NUEVOS (PARA QUE TENGAS TODO EL ADMIN COMPLETO) ---
# =================================================================

class TareaCorrectivaInline(admin.TabularInline):
    model = TareaCorrectiva
    fields = ('refaccion', 'usuario_asignado', 'fecha_limite', 'status')
    extra = 1
    autocomplete_fields = ['usuario_asignado']

@admin.register(AsignacionRevision)
class AsignacionRevisionAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'fecha_revision', 'tipo_programacion', 'status')
    list_filter = ('fecha_revision', 'status', 'tipo_programacion')
    search_fields = ('unidad__nombre',)
    inlines = [TareaCorrectivaInline]
    autocomplete_fields = ['unidad']

@admin.register(ProcesoCarga)
class ProcesoCargaAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'fecha_inicio', 'fecha_fin', 'tecnico_inicia', 'encargado_finaliza', 'status')
    list_filter = ('status', 'fecha_inicio')
    search_fields = ('unidad__nombre',)
    autocomplete_fields = ['unidad', 'tecnico_inicia', 'encargado_finaliza', 'checklist', 'inspeccion_llantas', 'carga_diesel', 'carga_urea']

@admin.register(ChecklistCorreccion)
class ChecklistCorreccionAdmin(admin.ModelAdmin):
    list_display = ('inspeccion', 'nombre_campo', 'status', 'fecha_correccion', 'corregido_por')
    list_filter = ('status', 'fecha_correccion')
    search_fields = ('inspeccion__unidad__nombre', 'nombre_campo')
    autocomplete_fields = ['inspeccion', 'corregido_por']

# Registros simples (los que no necesitan configuración especial)
admin.site.register(Operador)
admin.site.register(CargaAceite)
admin.site.register(CargaUrea)
admin.site.register(AjusteInventario)
admin.site.register(AlertaInventario)
admin.site.register(EntregaSuministros)
admin.site.register(TareaCorrectiva) # También se puede registrar por sí solo