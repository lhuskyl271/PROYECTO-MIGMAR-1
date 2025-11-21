# RH/urls.py
from django.urls import path
from . import views
from .views import vacantes_dashboard_view, asignar_reemplazo

app_name = 'rh'

urlpatterns = [
    # Ruta de Inicio
    path('', views.inicio_rh, name='inicio_rh'),
    
    # Rutas de Empleados (Ahora usan int:pk para IDs numéricos 1, 2, 3...)
    path('empleados/', views.EmpleadoListView.as_view(), name='lista_empleados'),
    path('empleados/nuevo/', views.EmpleadoCreateView.as_view(), name='empleado_create'),
    
    # --- CORRECCIÓN: Usamos <int:pk> en lugar de <uuid:pk> ---
    path('empleados/<int:pk>/', views.EmpleadoDetailView.as_view(), name='empleado_detail'),
    path('empleados/<int:pk>/editar/', views.EmpleadoUpdateView.as_view(), name='empleado_update'),
    path('empleados/<int:pk>/eliminar/', views.EmpleadoDeleteView.as_view(), name='empleado_delete'),
    path('empleados/<int:pk>/pdf/', views.generar_pdf_empleado, name='generar_pdf_empleado'),

    path('empleados/exportar/excel/', views.export_empleados_excel, name='export_empleados_excel'),

    # Rutas de Importación
    path('empleados/importar/', views.ImportarEmpleadosExcelView.as_view(), name='importar_empleados'),
    path('empleados/plantilla/', views.descargar_plantilla_importacion, name='descargar_plantilla'),  

    # Rutas para Departamentos
    path('departamentos/', views.DepartamentoListView.as_view(), name='lista_departamentos'),
    path('departamentos/nuevo/', views.DepartamentoCreateView.as_view(), name='departamento_create'),
    path('departamentos/<int:pk>/', views.DepartamentoDetailView.as_view(), name='departamento_detail'),
    path('departamentos/<int:pk>/editar/', views.DepartamentoUpdateView.as_view(), name='departamento_update'),
    path('departamentos/<int:pk>/eliminar/', views.DepartamentoDeleteView.as_view(), name='departamento_delete'),

    # Rutas para Puestos
    path('puestos/', views.PuestoListView.as_view(), name='lista_puestos'),
    path('puestos/nuevo/', views.PuestoCreateView.as_view(), name='puesto_create'),
    path('puestos/<int:pk>/', views.PuestoDetailView.as_view(), name='puesto_detail'),
    path('puestos/<int:pk>/editar/', views.PuestoUpdateView.as_view(), name='puesto_update'),
    path('puestos/<int:pk>/eliminar/', views.PuestoDeleteView.as_view(), name='puesto_delete'),
    
    # Rutas de Catálogos Adicionales (Motivos, Tipos Documento)
    path('tipos-documento-operador/', views.TipoDocumentoOperadorListView.as_view(), name='lista_tipos_documento_operador'),
    path('tipos-documento-operador/crear/', views.TipoDocumentoOperadorCreateView.as_view(), name='crear_tipo_documento_operador'),
    path('tipos-documento-operador/editar/<int:pk>/', views.TipoDocumentoOperadorUpdateView.as_view(), name='editar_tipo_documento_operador'),
    path('tipos-documento-operador/eliminar/<int:pk>/', views.TipoDocumentoOperadorDeleteView.as_view(), name='eliminar_tipo_documento_operador'),
    
    # Otras utilidades y reportes
    path('cumpleanos/', views.cumpleanos_rh, name='cumpleanos_rh'),
    path('documentos/semaforo/', views.semaforo_documentos_view, name='semaforo_documentos'),
    path('reportes/bajas/', views.reporte_bajas, name='reporte_bajas'),
    path('reportes/documentacion-operador/', views.reporte_documentacion_operador, name='reporte_documentacion_operador'),
    
    # Dashboards
    path('dashboard/', views.dashboard_view, name='dashboard_operadores'),
    path('dashboard/vacantes/', vacantes_dashboard_view, name='vacantes_dashboard'),
    path('vacantes/<int:pk>/asignar-reemplazo/', asignar_reemplazo, name='asignar_reemplazo'),
]