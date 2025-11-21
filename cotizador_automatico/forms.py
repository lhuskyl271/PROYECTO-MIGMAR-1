from django import forms
from .models import Cotizacion
from .models import Unidad, ParametrosGlobales

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = [
            # Datos Básicos
            'cliente', 'unidad', 'origen', 'destino', 
            'distancia_km_ida', 'dias_viaje', 'es_viaje_redondo', 'regreso_cargado',
            
            # Logística Avanzada (NUEVOS)
            'peso_carga_toneladas', 'capacidad_maxima_unidad', 'factor_terreno',
            'horas_espera_carga', 'horas_espera_descarga', 'costo_hora_demora',
            
            # Costos Variables
            'costo_casetas', 'sueldo_operador', 'viaticos', 'costo_maniobras',
            'margen_utilidad_deseado'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'origen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad Origen'}),
            'destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad Destino'}),
            'distancia_km_ida': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'KM'}),
            'dias_viaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            
            # Widgets Avanzados
            'peso_carga_toneladas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tons'}),
            'capacidad_maxima_unidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Capacidad Total'}),
            'factor_terreno': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'title': '1.0=Plano, 1.2=Sierra, 1.5=Muy Pesado'}),
            'horas_espera_carga': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'horas_espera_descarga': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'costo_hora_demora': forms.NumberInput(attrs={'class': 'form-control'}),

            'costo_casetas': forms.NumberInput(attrs={'class': 'form-control'}),
            'sueldo_operador': forms.NumberInput(attrs={'class': 'form-control'}),
            'viaticos': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_maniobras': forms.NumberInput(attrs={'class': 'form-control'}),
            'margen_utilidad_deseado': forms.NumberInput(attrs={'class': 'form-control'}),
            'es_viaje_redondo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'regreso_cargado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ['nombre', 'rendimiento_cargado', 'rendimiento_vacio', 
                  'costo_seguro_mensual', 'costo_gps_mensual', 
                  'depreciacion_mensual', 'otros_fijos_mensual']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rendimiento_cargado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rendimiento_vacio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_seguro_mensual': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_gps_mensual': forms.NumberInput(attrs={'class': 'form-control'}),
            'depreciacion_mensual': forms.NumberInput(attrs={'class': 'form-control'}),
            'otros_fijos_mensual': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ParametrosGlobalesForm(forms.ModelForm):
    class Meta:
        model = ParametrosGlobales
        fields = ['precio_diesel', 'costo_km_llantas', 'costo_km_mantenimiento']
        widgets = {
            'precio_diesel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_km_llantas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_km_mantenimiento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }