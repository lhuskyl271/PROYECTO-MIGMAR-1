# urls.py (Completo y Corregido)

from django.urls import path
from . import views

app_name = 'mantenimiento'

urlpatterns = [
    # --- URLs de Administrador ---
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/asignar/', views.AsignarTareaView.as_view(), name='asignar_tarea'),
    path('admin/tarea/<int:pk>/', views.AdminTareaDetalleView.as_view(), name='admin_tarea_detalle'),
    path('admin/tarea/<int:pk>/eliminar/', views.TareaMantenimientoDeleteView.as_view(), name='admin_tarea_eliminar'),

    # --- URLs de Técnico ---
    path('tecnico/dashboard/', views.TecnicoDashboardView.as_view(), name='tecnico_dashboard'),
    path('tecnico/tarea/<int:pk>/', views.TecnicoTareaDetalleView.as_view(), name='tecnico_tarea_detalle'),
    
    # --- URLs de Acciones (POST) ---
    path('tecnico/tarea/<int:pk>/seleccionar-herramientas/', views.seleccionar_herramientas, name='seleccionar_herramientas'),
    path('tecnico/tarea/<int:pk>/iniciar/', views.iniciar_tarea, name='iniciar_tarea'),
    path('tecnico/tarea/<int:pk>/finalizar/', views.finalizar_tarea, name='finalizar_tarea'),
    path('tecnico/tarea/<int:pk>/guardar-progreso/', views.guardar_progreso_preventivo, name='guardar_progreso_preventivo'),
    
    # --- RUTA PARA PDF ---
    path('tecnico/tarea/<int:pk>/generar-pdf/', views.generar_pdf_mantenimiento, name='generar_pdf'),

    # --- URLs de Catálogo de Herramientas (Admin) ---
    path('admin/herramientas/', views.CatalogoHerramientaListView.as_view(), name='herramienta_list'),
    path('admin/herramientas/nueva/', views.CatalogoHerramientaCreateView.as_view(), name='herramienta_crear'),
    path('admin/herramientas/<int:pk>/editar/', views.CatalogoHerramientaUpdateView.as_view(), name='herramienta_editar'),
    path('admin/herramientas/<int:pk>/eliminar/', views.CatalogoHerramientaDeleteView.as_view(), name='herramienta_eliminar'),

    # --- URLs de Catálogo Correctivo (Admin) ---
    path('admin/correctivo/', views.CatalogoCorrectivoListView.as_view(), name='correctivo_list'),
    path('admin/correctivo/nueva/', views.CatalogoCorrectivoCreateView.as_view(), name='correctivo_crear'),
    path('admin/correctivo/<int:pk>/editar/', views.CatalogoCorrectivoUpdateView.as_view(), name='correctivo_editar'),
    path('admin/correctivo/<int:pk>/eliminar/', views.CatalogoCorrectivoDeleteView.as_view(), name='correctivo_eliminar'),
    
    # --- RUTAS DE CIERRE (ADMIN Y SUPERVISOR) ---
    # Estas son las rutas correctas para el panel de "Descartar o Poner Diesel"
    path('gestion/cierre-mantenimiento/', 
         views.CierreMantenimientoListView.as_view(), 
         name='cierre_list'),
    path('gestion/cierre-mantenimiento/<int:pk>/procesar/', 
         views.procesar_cierre_mantenimiento, 
         name='cierre_procesar'),
]