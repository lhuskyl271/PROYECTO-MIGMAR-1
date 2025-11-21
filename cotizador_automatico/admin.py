from django.contrib import admin
from django.utils.html import mark_safe
from .models import ParametrosGlobales, Unidad, Cliente, Cotizacion

@admin.register(ParametrosGlobales)
class ParametrosAdmin(admin.ModelAdmin):
    list_display = ('fecha_actualizacion', 'precio_diesel', 'costo_km_llantas')
    # Solo permitimos un registro de configuración, así que quitamos el botón de agregar si ya existe uno
    def has_add_permission(self, request):
        return not ParametrosGlobales.objects.exists()

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rendimiento_cargado', 'costo_fijo_diario_view')
    
    def costo_fijo_diario_view(self, obj):
        return f"${obj.costo_fijo_diario():,.2f}"
    costo_fijo_diario_view.short_description = "Costo Fijo Diario"

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'email')

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'origen', 'destino', 'total_venta_view', 'utilidad_view', 'estatus')
    list_filter = ('estatus', 'unidad', 'cliente')
    readonly_fields = ('ver_desglose_completo',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('cliente', 'unidad', 'estatus')
        }),
        ('Ruta y Tiempos', {
            'fields': ('origen', 'destino', 'distancia_km_ida', 'dias_viaje', 'es_viaje_redondo', 'regreso_cargado')
        }),
        ('Gastos Directos', {
            'fields': ('costo_casetas', 'sueldo_operador', 'viaticos', 'costo_maniobras')
        }),
        ('Financiero', {
            'fields': ('margen_utilidad_deseado', 'ver_desglose_completo')
        }),
    )

    def total_venta_view(self, obj):
        datos = obj.calcular_financieros()
        if datos:
            return f"${datos['subtotal_venta']:,.2f}"
        return "Falta Config"
    total_venta_view.short_description = "Subtotal Venta"

    def utilidad_view(self, obj):
        datos = obj.calcular_financieros()
        if datos:
            return f"${datos['utilidad_monetaria']:,.2f}"
        return "---"
    utilidad_view.short_description = "Utilidad Proyectada"

    def ver_desglose_completo(self, obj):
        if not obj.id: return "Guarda la cotización primero para calcular."
        
        datos = obj.calcular_financieros()
        if not datos: return "Error: Faltan Parámetros Globales"

        html = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr style="border-bottom:1px solid #ccc;"><td><strong>Diesel:</strong></td><td style="color:red">${datos['costo_diesel']:,.2f}</td></tr>
            <tr style="border-bottom:1px solid #ccc;"><td><strong>Llantas/Mtto:</strong></td><td style="color:red">${datos['costo_desgaste']:,.2f}</td></tr>
            <tr style="border-bottom:1px solid #ccc;"><td><strong>Fijos (Depr+Seguros):</strong></td><td style="color:red">${datos['costo_fijos']:,.2f}</td></tr>
            <tr style="border-bottom:2px solid #000;"><td><strong>COSTO TOTAL:</strong></td><td><strong>${datos['costo_operativo_total']:,.2f}</strong></td></tr>
            
            <tr><td>&nbsp;</td><td></td></tr>
            <tr style="background-color:#e6fffa;"><td><strong>Subtotal (Precio Cliente):</strong></td><td style="font-size:1.2em; color:green">${datos['subtotal_venta']:,.2f}</td></tr>
            <tr style="border-top:2px solid #000;"><td><strong>TOTAL FACTURA:</strong></td><td><strong>${datos['gran_total']:,.2f}</strong></td></tr>
        </table>
        """
        return mark_safe(html)
    ver_desglose_completo.short_description = "Análisis de Rentabilidad"