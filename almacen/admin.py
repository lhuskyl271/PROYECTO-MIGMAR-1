# almacen/admin.py (ASÍ DEBE SER - CORREGIDO)

from django.contrib import admin
from .models import Proveedor, Categoria, SubCategoria, Articulo, EntradaArticulo

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email')
    search_fields = ('nombre',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(SubCategoria)
class SubCategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'categoria__nombre')
    autocomplete_fields = ('categoria',)

@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    # --- CORREGIDO ---
    # 'proveedor' y 'numero_proveedor' eliminados de todas las listas
    list_display = ('nombre', 'subcategoria', 'stock_total')
    list_filter = ('subcategoria',)
    search_fields = ('nombre',)
    autocomplete_fields = ('subcategoria',)
    readonly_fields = ('stock_total',)

@admin.register(EntradaArticulo)
class EntradaArticuloAdmin(admin.ModelAdmin):
    # --- ACTUALIZADO ---
    # 'proveedor' y 'numero_proveedor' añadidos aquí
    list_display = ('articulo', 'proveedor', 'cantidad', 'precio_compra', 'fecha_compra', 'tipo')
    list_filter = ('tipo', 'fecha_compra', 'proveedor', 'articulo')
    search_fields = ('articulo__nombre', 'proveedor__nombre', 'numero_proveedor')
    autocomplete_fields = ('articulo', 'proveedor')
    
    # Esto hace que el campo de fecha sea más amigable
    date_hierarchy = 'fecha_compra'