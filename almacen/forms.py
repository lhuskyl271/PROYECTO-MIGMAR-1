# almacen/forms.py
from django import forms
from .models import Articulo, EntradaArticulo, Categoria, SubCategoria, Proveedor # Importar Proveedor

# --- Formularios de Gestión ---
# (CategoriaForm y SubCategoriaForm no cambian)

class CategoriaForm(forms.ModelForm):
    """Formulario para crear una Categoría principal"""
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: FILTROS',
                'style': 'text-transform:uppercase;'
            }),
        }
    
    def clean_nombre(self):
        return self.cleaned_data['nombre'].upper()

class SubCategoriaForm(forms.ModelForm):
    """Formulario para crear una Sub-Categoría"""
    class Meta:
        model = SubCategoria
        fields = ['categoria', 'nombre']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: AIRE',
                'style': 'text-transform:uppercase;'
            }),
        }
    
    def clean_nombre(self):
        return self.cleaned_data['nombre'].upper()

# --- Formularios de Soporte (Proveedores) ---
# (ProveedorForm no cambia)

class ProveedorForm(forms.ModelForm):
    """Formulario para crear o editar un Proveedor"""
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase;'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_nombre(self):
        return self.cleaned_data['nombre'].upper()

# --- Formularios Principales ---

class ArticuloForm(forms.ModelForm):
    """Formulario para crear o editar un Artículo (la ficha técnica)"""
    class Meta:
        model = Articulo
        # --- CAMPOS ELIMINADOS DE AQUÍ ---
        fields = ['nombre', 'subcategoria', 'foto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase;'}),
            'subcategoria': forms.Select(attrs={'class': 'form-select select2-widget'}),
            # 'proveedor': forms.Select(attrs={'class': 'form-select select2-widget'}),  <-- ELIMINADO
            # 'numero_proveedor': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase;'}), <-- ELIMINADO
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_nombre(self):
        return self.cleaned_data['nombre'].upper()
    
    # --- MÉTODO ELIMINADO ---
    # def clean_numero_proveedor(self):
    #     return self.cleaned_data['numero_proveedor'].upper()

class EntradaArticuloForm(forms.ModelForm):
    """Formulario para registrar una NUEVA COMPRA (Entrada)"""
    class Meta:
        model = EntradaArticulo
        # --- CAMPOS AÑADIDOS AQUÍ ---
        fields = ['articulo', 'proveedor', 'numero_proveedor', 'cantidad', 'precio_compra', 'fecha_compra', 'tipo']
        widgets = {
            'articulo': forms.Select(attrs={'class': 'form-select select2-widget'}),
            # --- WIDGETS AÑADIDOS ---
            'proveedor': forms.Select(attrs={'class': 'form-select select2-widget'}),
            'numero_proveedor': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase;', 'placeholder': 'Opcional: SKU de factura'}),
            # ------------------------
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

    # --- MÉTODO AÑADIDO (MOVIDO DESDE ArticuloForm) ---
    def clean_numero_proveedor(self):
        return self.cleaned_data['numero_proveedor'].upper()