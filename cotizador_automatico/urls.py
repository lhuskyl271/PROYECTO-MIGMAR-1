from django.urls import path
from .views import (
    CotizacionListView, CotizacionCreateView, CotizacionDetailView,
    UnidadListView, UnidadCreateView, UnidadUpdateView,
    ParametrosListView, ParametrosCreateView
)

urlpatterns = [
    # Cotizaciones (Ya existían)
    path('', CotizacionListView.as_view(), name='cotizaciones_lista'),
    path('nueva/', CotizacionCreateView.as_view(), name='cotizacion_nueva'),
    path('<int:pk>/', CotizacionDetailView.as_view(), name='cotizacion_detalle'),

    # --- NUEVAS RUTAS ---
    
    # Unidades
    path('unidades/', UnidadListView.as_view(), name='unidades_lista'),
    path('unidades/nueva/', UnidadCreateView.as_view(), name='unidad_nueva'),
    path('unidades/editar/<int:pk>/', UnidadUpdateView.as_view(), name='unidad_editar'),

    # Costos Globales
    path('configuracion/', ParametrosListView.as_view(), name='parametros_lista'),
    path('configuracion/actualizar/', ParametrosCreateView.as_view(), name='parametros_nuevo'),
]