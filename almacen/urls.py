# almacen/urls.py
from django.urls import path
from . import views

app_name = 'almacen'

urlpatterns = [
    # Dashboard principal (Lista de artículos)
    path('', views.AlmacenDashboardView.as_view(), name='dashboard'),
    
    # Gestion de Categorías
    path('categorias/', views.GestionCategoriasView.as_view(), name='gestion-categorias'),
    
    # --- Rutas de Proveedores ---
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedor-list'),
    path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor-crear'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor-editar'),
    
    # Vistas de Artículos (Ficha Técnica)
    path('articulo/nuevo/', views.ArticuloCreateView.as_view(), name='articulo-crear'),
    path('articulo/<int:pk>/', views.ArticuloDetailView.as_view(), name='articulo-detalle'),
    path('articulo/<int:pk>/editar/', views.ArticuloUpdateView.as_view(), name='articulo-editar'),
    
    # Vistas de Entradas (Añadir Stock)
    path('entrada/nueva/', views.EntradaArticuloCreateView.as_view(), name='entrada-crear'),
    path('articulo/<int:articulo_pk>/add_stock/', views.EntradaArticuloCreateView.as_view(), name='entrada-crear-especifico'),
    
    # --- NUEVAS RUTAS PARA EDITAR/ELIMINAR ENTRADAS ---
    path('entrada/<int:pk>/editar/', views.EntradaArticuloUpdateView.as_view(), name='entrada-editar'),
    path('entrada/<int:pk>/eliminar/', views.EntradaArticuloDeleteView.as_view(), name='entrada-eliminar'),
]