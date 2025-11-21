from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Cotizacion, ParametrosGlobales
from .forms import CotizacionForm
from .forms import UnidadForm, ParametrosGlobalesForm # Asegúrate de importar los nuevos forms
from .models import Unidad, ParametrosGlobales

class CotizacionListView(ListView):
    model = Cotizacion
    template_name = 'cotizaciones/lista.html'
    context_object_name = 'cotizaciones'
    ordering = ['-fecha']

class CotizacionCreateView(CreateView):
    model = Cotizacion
    form_class = CotizacionForm
    template_name = 'cotizaciones/form.html'
    
    def form_valid(self, form):
        # Validar que existan parámetros globales antes de crear
        if not ParametrosGlobales.objects.exists():
            form.add_error(None, "Error Crítico: No se han configurado los Parámetros Globales (Diesel, Llantas).")
            return self.form_invalid(form)
        messages.success(self.request, "Cotización calculada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('cotizacion_detalle', kwargs={'pk': self.object.pk})

class CotizacionDetailView(DetailView):
    model = Cotizacion
    template_name = 'cotizaciones/detalle.html'
    context_object_name = 'cotizacion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ejecutamos la fórmula maestra
        financiero = self.object.calcular_financieros()
        
        if financiero:
            context['finanzas'] = financiero
            # Variable para semáforo de utilidad (Rojo/Verde) en el HTML
            context['es_rentable'] = financiero['utilidad_monetaria'] > 0
        else:
            context['error_params'] = True
            
        return context

class UnidadListView(ListView):
    model = Unidad
    template_name = 'cotizador_automatico/unidades_lista.html'
    context_object_name = 'unidades'

class UnidadCreateView(CreateView):
    model = Unidad
    form_class = UnidadForm
    template_name = 'cotizador_automatico/unidades_form.html'
    success_url = reverse_lazy('unidades_lista')
    
    def form_valid(self, form):
        messages.success(self.request, "Unidad registrada correctamente.")
        return super().form_valid(form)

class UnidadUpdateView(UpdateView):
    model = Unidad
    form_class = UnidadForm
    template_name = 'cotizador_automatico/unidades_form.html'
    success_url = reverse_lazy('unidades_lista')

    def form_valid(self, form):
        messages.success(self.request, "Unidad actualizada correctamente.")
        return super().form_valid(form)

# --- GESTIÓN DE COSTOS GLOBALES ---

class ParametrosListView(ListView):
    """Muestra el historial de cambios de costos"""
    model = ParametrosGlobales
    template_name = 'cotizador_automatico/parametros_lista.html'
    context_object_name = 'parametros'
    ordering = ['-fecha_actualizacion']

class ParametrosCreateView(CreateView):
    """Actualizar costos (Crea un nuevo registro para mantener historial)"""
    model = ParametrosGlobales
    form_class = ParametrosGlobalesForm
    template_name = 'cotizador_automatico/parametros_form.html'
    success_url = reverse_lazy('parametros_lista')

    def get_initial(self):
        # Pre-llenar con los últimos valores para facilitar la edición
        ultimo = ParametrosGlobales.objects.last()
        if ultimo:
            return {
                'precio_diesel': ultimo.precio_diesel,
                'costo_km_llantas': ultimo.costo_km_llantas,
                'costo_km_mantenimiento': ultimo.costo_km_mantenimiento
            }
        return super().get_initial()

    def form_valid(self, form):
        messages.success(self.request, "Costos Globales actualizados exitosamente.")
        return super().form_valid(form)