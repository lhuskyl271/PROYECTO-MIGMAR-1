from django import forms
from django.utils.safestring import mark_safe
from .models import Cotizacion, Unidad, ParametrosGlobales, Cliente

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = [
            'cliente', 'unidad', 
            'origen', 'destino', 'distancia_km_ida', 'es_viaje_redondo',
            'es_refrigerado', 'horas_thermo_motor', 'dias_viaje',
            'sueldo_operador', 'costo_casetas', 'viaticos', 'costo_maniobras',
            'margen_utilidad_deseado'
        ]
        
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'origen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Monterrey'}),
            'destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. CDMX'}),
            'distancia_km_ida': forms.NumberInput(attrs={'class': 'form-control border-primary fw-bold'}),
            'horas_thermo_motor': forms.NumberInput(attrs={'class': 'form-control'}),
            'dias_viaje': forms.NumberInput(attrs={'class': 'form-control'}),
            'sueldo_operador': forms.NumberInput(attrs={'class': 'form-control input-money'}),
            'costo_casetas': forms.NumberInput(attrs={'class': 'form-control input-money'}),
            'viaticos': forms.NumberInput(attrs={'class': 'form-control input-money'}),
            'costo_maniobras': forms.NumberInput(attrs={'class': 'form-control input-money'}),
            'margen_utilidad_deseado': forms.NumberInput(attrs={'class': 'form-control fw-bold text-success'}),
            'es_viaje_redondo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'es_refrigerado': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch', 'id': 'toggleThermo'}),
        }

        labels = {
            'distancia_km_ida': 'Distancia Sencilla (KM)',
            'horas_thermo_motor': 'Horas Motor Thermo Encendido',
            'sueldo_operador': 'Pago Neto Operador',
            'costo_maniobras': 'Maniobras y Carga/Descarga'
        }

        help_texts = {
            'distancia_km_ida': mark_safe("""
                <div class="text-muted small mt-1">
                    <i class="fas fa-calculator"></i> <strong>Fórmula Diésel Tracto:</strong> <br>
                    (KM Totales / Rendimiento Unidad) × Precio Diésel Actual
                </div>
            """),
            'es_viaje_redondo': mark_safe("""
                <span class="badge bg-info text-dark">
                    Al activar: Se duplica distancia y costos variables (llantas/mtto).
                </span>
            """),
            'es_refrigerado': mark_safe("""
                <div class="text-primary small">
                    <i class="fas fa-snowflake"></i> Habilita el cálculo de consumo de combustible independiente para el equipo de frío.
                </div>
            """),
            'horas_thermo_motor': mark_safe("""
                <div class="alert alert-light border-start border-primary p-2 small mb-0 mt-1">
                    <strong>Fórmula Costo Thermo:</strong> <br>
                    <code>Horas Uso × Litros/Hora (Config) × Precio Diésel</code>
                    <br><em>Ej. Mty-Mex: 24-30 hrs aprox.</em>
                </div>
            """),
            'dias_viaje': mark_safe("""
                <div class="text-muted small">
                    <strong>Impacto en Costo:</strong> Prorratea Seguro, GPS y Depreciación de la unidad según los días ocupados.
                </div>
            """),
            'margen_utilidad_deseado': mark_safe("""
                <div class="text-end text-success small fw-bold">
                    Precio Venta = Costo Total / (1 - Margen%)
                </div>
            """)
        }

class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ['nombre', 'rendimiento_cargado', 'rendimiento_vacio', 
                  'costo_seguro_mensual', 'costo_gps_mensual', 
                  'depreciacion_mensual', 'otros_fijos_mensual']
        
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Kenworth T680 - Eco 105'}),
            'rendimiento_cargado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'km/l'}),
            'rendimiento_vacio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'km/l'}),
            
            # Clases especiales 'costo-input' para el Javascript
            'costo_seguro_mensual': forms.NumberInput(attrs={'class': 'form-control costo-input', 'placeholder': '$'}),
            'costo_gps_mensual': forms.NumberInput(attrs={'class': 'form-control costo-input', 'placeholder': '$'}),
            'depreciacion_mensual': forms.NumberInput(attrs={'class': 'form-control costo-input', 'placeholder': '$'}),
            'otros_fijos_mensual': forms.NumberInput(attrs={'class': 'form-control costo-input', 'placeholder': '$'}),
        }
        
        help_texts = {
            'rendimiento_cargado': mark_safe('<i class="fas fa-gas-pump"></i> Km/L con carga completa. (Excel ref: 3.5 km/l local)'),
            'depreciacion_mensual': mark_safe('<strong>Fórmula:</strong> (Valor Factura Unidad - Valor Rescate) / 60 meses.'),
            'otros_fijos_mensual': 'Incluir: Placas, Verificaciones, Estacionamiento (Pensión).'
        }
        
        labels = {
            'rendimiento_cargado': 'Rendimiento Cargado (Km/L)',
            'rendimiento_vacio': 'Rendimiento Vacío (Km/L)',
        }

class ParametrosGlobalesForm(forms.ModelForm):
    class Meta:
        model = ParametrosGlobales
        fields = ['precio_diesel', 'costo_km_llantas', 'costo_km_mantenimiento', 'consumo_thermo_hora']
        widgets = {
            'precio_diesel': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_km_llantas': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_km_mantenimiento': forms.NumberInput(attrs={'class': 'form-control'}),
            'consumo_thermo_hora': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'consumo_thermo_hora': 'Litros consumidos por hora de operación del equipo de refrigeración.'
        }