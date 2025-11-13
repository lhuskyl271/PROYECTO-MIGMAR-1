# almacen/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, DeleteView # <-- Añadir DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.contrib import messages

# Importaciones de Modelos y Formularios
from .models import Articulo, EntradaArticulo, Categoria, SubCategoria, Proveedor
from .forms import ArticuloForm, EntradaArticuloForm, CategoriaForm, SubCategoriaForm, ProveedorForm

# --- Vista de Gestión de Categorías ---
# (Esta vista no cambia)
class GestionCategoriasView(LoginRequiredMixin, TemplateView):
    template_name = 'almacen/gestion_categorias.html'
    # ... (resto del código de la vista) ...
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'categoria_form' not in context:
            context['categoria_form'] = CategoriaForm()
        if 'subcategoria_form' not in context:
            context['subcategoria_form'] = SubCategoriaForm()
        context['categorias'] = Categoria.objects.prefetch_related('subcategorias').all()
        context['titulo'] = "Gestionar Categorías de Almacén"
        return context
    def post(self, request, *args, **kwargs):
        context = {}
        if 'submit_categoria' in request.POST:
            form = CategoriaForm(request.POST)
            form_name = 'categoria_form'
            success_message = "¡Categoría creada exitosamente!"
        elif 'submit_subcategoria' in request.POST:
            form = SubCategoriaForm(request.POST)
            form_name = 'subcategoria_form'
            success_message = "¡Sub-categoría creada exitosamente!"
        else:
            return redirect('almacen:gestion-categorias')
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect('almacen:gestion-categorias')
        else:
            messages.error(request, "Error al guardar. Revisa los campos.")
            context[form_name] = form
            return self.render_to_response(self.get_context_data(**context))

# --- Vistas de Proveedores ---
# (Estas vistas no cambian)
class ProveedorListView(LoginRequiredMixin, ListView):
    model = Proveedor
    template_name = 'almacen/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 10
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Lista de Proveedores"
        return context

class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'almacen/proveedor_form.html'
    success_url = reverse_lazy('almacen:proveedor-list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Registrar Nuevo Proveedor"
        return context

class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'almacen/proveedor_form.html'
    success_url = reverse_lazy('almacen:proveedor-list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Editar Proveedor"
        return context

# --- Vistas Principales del Almacén ---
# (AlmacenDashboardView no cambia)
class AlmacenDashboardView(LoginRequiredMixin, ListView):
    model = Articulo
    template_name = 'almacen/dashboard.html'
    context_object_name = 'articulos'
    paginate_by = 20
    def get_queryset(self):
        query = self.request.GET.get('q')
        qs = Articulo.objects.select_related('subcategoria', 'subcategoria__categoria')
        if query:
            qs = qs.filter(nombre__icontains=query)
        return qs.order_by('nombre')

class ArticuloDetailView(LoginRequiredMixin, DetailView):
    """
    Muestra el detalle de un artículo y todo su historial de entradas.
    ¡ACTUALIZADO CON FILTROS!
    """
    model = Articulo
    template_name = 'almacen/articulo_detalle.html'
    context_object_name = 'articulo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- Lógica de Filtros ---
        filtro_proveedor_id = self.request.GET.get('proveedor')
        filtro_tipo = self.request.GET.get('tipo')

        # Iniciar consulta base
        historial = self.object.entradas.select_related('proveedor').all()

        # Aplicar filtros si existen
        if filtro_proveedor_id:
            historial = historial.filter(proveedor_id=filtro_proveedor_id)
        if filtro_tipo:
            historial = historial.filter(tipo=filtro_tipo)

        context['historial_entradas'] = historial.order_by('-fecha_compra')
        
        # --- Pasar opciones y valores de filtros a la plantilla ---
        proveedor_ids = self.object.entradas.values_list('proveedor_id', flat=True).distinct()
        context['filtro_proveedores_opciones'] = Proveedor.objects.filter(id__in=proveedor_ids).order_by('nombre')
        context['filtro_tipo_opciones'] = EntradaArticulo.TIPO_CHOICES
        
        # Devolver los filtros actuales para marcarlos en el HTML
        context['filtro_actual_proveedor'] = filtro_proveedor_id
        context['filtro_actual_tipo'] = filtro_tipo
        
        return context

# (ArticuloCreateView no cambia)
class ArticuloCreateView(LoginRequiredMixin, CreateView):
    model = Articulo
    form_class = ArticuloForm
    template_name = 'almacen/articulo_form.html'
    success_url = reverse_lazy('almacen:dashboard')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Artículo'
        return context

class ArticuloUpdateView(LoginRequiredMixin, UpdateView):
    """Para editar la ficha técnica de un artículo"""
    model = Articulo
    form_class = ArticuloForm
    template_name = 'almacen/articulo_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Artículo'
        return context
    
    def get_success_url(self):
        # Redirige de vuelta al detalle del artículo que se editó
        messages.success(self.request, "¡Ficha técnica actualizada!")
        return reverse_lazy('almacen:articulo-detalle', kwargs={'pk': self.object.pk})


class EntradaArticuloCreateView(LoginRequiredMixin, CreateView):
    """
    La vista más importante: para AÑADIR stock (registrar una compra).
    ¡ACTUALIZADO CON MENSAJE DE ÉXITO!
    """
    model = EntradaArticulo
    form_class = EntradaArticuloForm
    template_name = 'almacen/entrada_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        articulo_pk = self.kwargs.get('articulo_pk')
        if articulo_pk:
            initial['articulo'] = get_object_or_404(Articulo, pk=articulo_pk)
        return initial
    
    def get_success_url(self):
        # Redirige al detalle del artículo que se actualizó
        messages.success(self.request, "¡Compra registrada exitosamente!")
        return reverse_lazy('almacen:articulo-detalle', kwargs={'pk': self.object.articulo.pk})

# --- VISTAS NUEVAS PARA EDITAR/ELIMINAR ENTRADAS ---

class EntradaArticuloUpdateView(LoginRequiredMixin, UpdateView):
    """
    Permite EDITAR una entrada de compra (un registro de historial).
    """
    model = EntradaArticulo
    form_class = EntradaArticuloForm
    template_name = 'almacen/entrada_form.html' # Reutilizamos el formulario de creación

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Editar Compra de: {self.object.articulo.nombre}"
        return context

    def get_success_url(self):
        # Redirige de vuelta a la página de detalle del artículo
        messages.success(self.request, "¡Compra actualizada exitosamente!")
        return reverse_lazy('almacen:articulo-detalle', kwargs={'pk': self.object.articulo.pk})

class EntradaArticuloDeleteView(LoginRequiredMixin, DeleteView):
    """
    Permite ELIMINAR una entrada de compra (un registro de historial).
    """
    model = EntradaArticulo
    template_name = 'almacen/entradaarticulo_confirm_delete.html' 
    context_object_name = 'entrada' # Para usar {{ entrada }} en la plantilla

    def get_success_url(self):
        # Redirige de vuelta a la página de detalle del artículo
        messages.warning(self.request, "La entrada de compra ha sido eliminada.")
        return reverse_lazy('almacen:articulo-detalle', kwargs={'pk': self.object.articulo.pk})