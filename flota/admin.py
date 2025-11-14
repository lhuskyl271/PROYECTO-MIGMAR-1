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
    
    # --- IMPORTACIONES AÑADIDAS ---
    LlantasInspeccion,
    LlantaDetalle,
    ProcesoCarga,
    AjusteInventario,
    AsignacionRevision,
    AlertaInventario,
    ChecklistCorreccion,
    EntregaSuministros,
    TareaCorrectiva,
)

# =================================================================
# --- CONFIGURACIÓN PARA INSPECCIÓN DE LLANTAS ---
# =================================================================

class LlantaDetalleInline(admin.TabularInline):
    model = LlantaDetalle
    fields = ['posicion', 'mm', 'marca', 'modelo', 'medida', 'presion']
    extra = 0 

@admin.register(LlantasInspeccion)
class LlantasInspeccionAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'fecha', 'tecnico', 'km', 'es_dummy')
    list_filter = ('fecha', 'es_dummy', 'tecnico')
    search_fields = ('unidad__nombre', 'tecnico__username')
    inlines = [LlantaDetalleInline]
    autocomplete_fields = ['unidad', 'tecnico']

# =================================================================
# --- REGISTROS EXISTENTES (MEJORADOS CON @register) ---
# =================================================================

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'modelo', 'placas', 'tipo', 'km_actual')
    list_filter = ('tipo', 'marca', 'unidad_negocio')
    search_fields = ('nombre', 'placas', 'vin', 'modelo') # <--- Este ya estaba bien

@admin.register(CargaDiesel)
class CargaDieselAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'fecha', 'operador', 'lts_diesel', 'lts_thermo', 'km_actual')
    list_filter = ('unidad',)
    date_hierarchy = 'fecha'
    autocomplete_fields = ['unidad', 'operador']
    
    # --- INICIO DE LA CORRECCIÓN 1 ---
    # Necesitamos esto para que otros modelos (como ProcesoCarga)
    # puedan buscar Cargas de Diésel.
    search_fields = ('unidad__nombre', 'operador__nombre', 'fecha')
    # --- FIN DE LA CORRECCIÓN 1 ---

@admin.register(CompraSuministro)
class CompraSuministroAdmin(admin.ModelAdmin):
    list_display = ('fecha_compra', 'tipo_suministro', 'proveedor', 'cantidad', 'precio_por_litro', 'precio')
    list_filter = ('tipo_suministro', 'proveedor')
    date_hierarchy = 'fecha_compra'
    search_fields = ('proveedor', 'tipo_suministro') # Añadido por buena práctica

@admin.register(ChecklistInspeccion)
class ChecklistInspeccionAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'operador', 'tecnico', 'fecha', 'es_dummy')
    list_filter = ('fecha', 'es_dummy', 'tecnico')
    # Este 'search_fields' ya estaba, y es necesario para 'autocomplete_fields'
    search_fields = ('unidad__nombre', 'operador__nombre', 'tecnico__username')
    autocomplete_fields = ['unidad', 'operador', 'tecnico']

# =================================================================
# --- REGISTROS NUEVOS (PARA QUE TENGAS TODO EL ADMIN COMPLETO) ---
# =================================================================

# --- INICIO DE LA CORRECCIÓN 2 ---
# 'Operador' necesita su propio Admin con 'search_fields'
# porque CargaDieselAdmin y ChecklistInspeccionAdmin lo usan en 'autocomplete_fields'
@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido')
    search_fields = ('nombre', 'apellido')
# --- FIN DE LA CORRECCIÓN 2 ---

# --- INICIO DE LA CORRECCIÓN 3 ---
# 'CargaUrea' necesita su propio Admin con 'search_fields'
# porque ProcesoCargaAdmin lo usa en 'autocomplete_fields'
@admin.register(CargaUrea)
class CargaUreaAdmin(admin.ModelAdmin):
    list_display = ('unidad', 'fecha', 'litros_cargados', 'costo')
    list_filter = ('fecha', 'unidad')
    search_fields = ('unidad__nombre', 'fecha')
    autocomplete_fields = ['unidad']
# --- FIN DE LA CORRECCIÓN 3 ---

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
    search_fields = ('unidad__nombre', 'tecnico_inicia__username', 'encargado_finaliza__username')
    autocomplete_fields = [
        'unidad', 
        'tecnico_inicia', 
        'encargado_finaliza', 
        'checklist', 
        'inspeccion_llantas', 
        'carga_diesel', 
        'carga_urea'
    ]

@admin.register(ChecklistCorreccion)
class ChecklistCorreccionAdmin(admin.ModelAdmin):
    list_display = ('inspeccion', 'nombre_campo', 'status', 'fecha_correccion', 'corregido_por')
    list_filter = ('status', 'fecha_correccion')
    search_fields = ('inspeccion__unidad__nombre', 'nombre_campo')
    autocomplete_fields = ['inspeccion', 'corregido_por']

# Registros simples (los que no necesitan configuración especial)
# (Operador y CargaUrea se movieron arriba para convertirlos en @admin.register)
admin.site.register(CargaAceite)
admin.site.register(AjusteInventario)
admin.site.register(AlertaInventario)
admin.site.register(EntregaSuministros)
admin.site.register(TareaCorrectiva)