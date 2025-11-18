# RH/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q, Avg, F
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from datetime import date, timedelta
from django.template.loader import get_template, render_to_string
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView, FormView, TemplateView
from django.urls import reverse_lazy
from django.forms import inlineformset_factory
from django.db import transaction

# --- Imports para Excel y Gráficos ---
import pandas as pd
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter 

# --- Imports para PDF (Mantenemos tu xhtml2pdf original) ---
from xhtml2pdf import pisa

# --- Imports para S3 (NUEVO) ---
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
import os

# --- Imports Locales ---
from .models import (
    Empleado, Departamento, Puesto, MotivoInactivacion,
    TipoDocumentoOperador, DocumentoOperador, HistorialLaboral, Salario, Contrato, Hijo,
    TipoViaje, DivisionOperativa, TipoCarga
)
from .forms import (
    EmpleadoForm, DepartamentoForm, PuestoForm, MotivoInactivacionForm, 
    TipoDocumentoOperadorForm, DocumentoOperadorForm, HistorialLaboralForm, 
    SalarioForm, ContratoForm, HijoForm
)

# ==============================================================================
# === LÓGICA DE AMAZON S3 (NUEVO) ===
# ==============================================================================

def _eliminar_archivo_de_s3(ruta_completa_s3):
    """
    Elimina un archivo de S3 dado su nombre/ruta relativa (Key).
    Evita dejar archivos huérfanos en el bucket.
    """
    if not ruta_completa_s3:
        return
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        # Convertir a string y asegurar ruta correcta si usas 'media' en settings
        key = str(ruta_completa_s3)
        
        # Ajuste: Si tus archivos en S3 están dentro de una carpeta 'media' y Django no lo incluye en el nombre
        if hasattr(settings, 'AWS_MEDIA_LOCATION') and not key.startswith(settings.AWS_MEDIA_LOCATION):
             key = f"{settings.AWS_MEDIA_LOCATION}/{key}"

        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key
        )
    except (BotoCoreError, NoCredentialsError, Exception) as e:
        print(f"Error al eliminar archivo de S3: {e}")

# Mixin para permisos (Opcional, ajusta según tus grupos de usuarios)
def es_admin_rh(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=['Administrador', 'RH_Admin', 'Recursos Humanos']).exists())

class RHAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return es_admin_rh(self.request.user)

# ==============================================================================
# === VISTAS PRINCIPALES ===
# ==============================================================================

# Vista para el panel de control de la aplicación RH
def inicio_rh(request):
    today = date.today()
    
    # --- 1. KPIs Generales ---
    total_empleados = Empleado.objects.count()
    empleados_activos = Empleado.objects.filter(activo=True).count()
    total_departamentos = Departamento.objects.count()
    empleados_inactivos = Empleado.objects.filter(activo=False).count()

    # Cálculo de Porcentajes
    porcentaje_activos = round((empleados_activos / total_empleados * 100), 1) if total_empleados > 0 else 0
    porcentaje_inactivos = round((empleados_inactivos / total_empleados * 100), 1) if total_empleados > 0 else 0

    # --- 1.5 KPIs Operativos ---
    operadores_migmar = Empleado.objects.filter(
        activo=True, 
        empresa='MIGMAR', 
        puesto__nombre__icontains='Operador'
    ).count()
    
    operadores_marco = Empleado.objects.filter(
        activo=True, 
        empresa='MARCO_MORALES', 
        puesto__nombre__icontains='Operador'
    ).count()

    # --- 2. Cumpleaños ---
    cumpleanos_hoy = []
    empleados_cumple = Empleado.objects.filter(
        fecha_nacimiento__month=today.month,
        fecha_nacimiento__day=today.day,
        activo=True
    )
    for emp in empleados_cumple:
        edad = today.year - emp.fecha_nacimiento.year
        cumpleanos_hoy.append({'empleado': emp, 'edad_a_cumplir': edad})

    # --- 3. ALERTAS ---
    alertas_rh = []
    
    # A. Alerta de Contratos por Vencer
    fecha_limite_contrato = today + timedelta(days=30)
    contratos_por_vencer = Contrato.objects.filter(
        tipo_contrato='DETERMINADO',
        fecha_fin__range=[today, fecha_limite_contrato],
        empleado__activo=True
    ).select_related('empleado')

    for c in contratos_por_vencer:
        dias = (c.fecha_fin - today).days
        alertas_rh.append({
            'titulo': f'Vencimiento de Contrato ({dias} días)',
            'descripcion': f'Contrato de {c.empleado.nombre} {c.empleado.apellido}',
            'tipo': 'warning',
            'icono': 'file-contract',
            'fecha': c.fecha_fin
        })

    # B. Documentos Vencidos
    fecha_limite_docs = today + timedelta(days=15)
    docs_vencidos = DocumentoOperador.objects.filter(
        fecha_vencimiento__lte=fecha_limite_docs,
        empleado__activo=True
    ).select_related('empleado', 'tipo_documento')

    for d in docs_vencidos:
        if d.fecha_vencimiento < today:
            tipo_alerta = 'danger'
            texto_dias = "VENCIDO"
        else:
            tipo_alerta = 'warning'
            texto_dias = f"Vence: {(d.fecha_vencimiento - today).days} días"

        alertas_rh.append({
            'titulo': f'{d.tipo_documento.nombre}',
            'descripcion': f'{texto_dias} - {d.empleado.nombre} {d.empleado.apellido}',
            'tipo': tipo_alerta,
            'icono': 'id-card',
            'fecha': d.fecha_vencimiento
        })
    
    # C. Vacantes
    vacantes_activas = HistorialLaboral.objects.filter(estatus='BUSCANDO').select_related('empleado')
    for v in vacantes_activas:
        dias = (today - v.fecha_inicio).days
        alertas_rh.append({
            'titulo': 'Vacante Abierta',
            'descripcion': f'{v.puesto or "Puesto"} - {dias} días sin cubrir',
            'tipo': 'info',
            'icono': 'user-clock',
            'fecha': v.fecha_inicio
        })

    alertas_rh.sort(key=lambda x: (x['tipo'] != 'danger', x['fecha']))

    # --- 4. Gráficos ---
    departamento_distribucion = Empleado.objects.filter(activo=True).values('departamento__nombre').annotate(count=Count('id')).order_by('-count')
    departamento_distribucion_list = [{'nombre': item['departamento__nombre'] or 'Sin Asignar', 'count': item['count']} for item in departamento_distribucion]

    context = {
        'total_empleados': total_empleados,
        'empleados_activos': empleados_activos,
        'total_departamentos': total_departamentos,
        'empleados_inactivos': empleados_inactivos,
        'empleados_activos_porcentaje': porcentaje_activos,
        'empleados_inactivos_porcentaje': porcentaje_inactivos,
        'operadores_migmar': operadores_migmar,
        'operadores_marco': operadores_marco,
        'cumpleanos_hoy': cumpleanos_hoy,
        'departamento_distribucion': departamento_distribucion_list,
        'alertas_rh': alertas_rh,
        'today': today,
    }
    return render(request, 'rh/home.html', context)

class EmpleadoListView(ListView):
    model = Empleado
    template_name = 'rh/lista_empleados.html'
    context_object_name = 'empleados'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related('puesto', 'departamento')

        # Parámetros de Filtrado
        nombre = self.request.GET.get('nombre', '')
        depto_id = self.request.GET.get('departamento', '')
        puesto_id = self.request.GET.get('puesto', '')
        estado = self.request.GET.get('estado', '')
        fecha_inicio = self.request.GET.get('fecha_inicio', '')
        fecha_fin = self.request.GET.get('fecha_fin', '')
        tipo_viaje_id = self.request.GET.get('tipo_viaje', '')
        empresa = self.request.GET.get('empresa', '')

        # Aplicar filtros
        if nombre:
            queryset = queryset.filter(Q(nombre__icontains=nombre) | Q(apellido__icontains=nombre))
        if depto_id:
            queryset = queryset.filter(departamento__id=depto_id)
        if puesto_id:
            queryset = queryset.filter(puesto__id=puesto_id)
        if estado in ['0', '1']:
            queryset = queryset.filter(activo=(estado == '1'))
        if fecha_inicio:
            queryset = queryset.filter(fecha_contratacion__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_contratacion__lte=fecha_fin)
        if tipo_viaje_id:
            queryset = queryset.filter(tipo_viaje__id=tipo_viaje_id)
        if empresa:
            queryset = queryset.filter(empresa=empresa)

        # Ordenamiento
        sort_by = self.request.GET.get('sort', 'id')
        direction = self.request.GET.get('direction', 'desc')

        if direction == 'desc':
            if not sort_by.startswith('-'):
                sort_by = f'-{sort_by}'
        else:
            if sort_by.startswith('-'):
                sort_by = sort_by[1:]

        valid_sort_fields = ['id', 'apellido', 'puesto__nombre', 'departamento__nombre', 'fecha_contratacion', 'empresa']
        if sort_by.replace('-', '') == 'nombre':
            sort_by = sort_by.replace('nombre', 'apellido')

        if sort_by.replace('-', '') in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-id', 'apellido', 'nombre')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        for empleado in context['object_list']:
            empleado.age = calculate_age(empleado.fecha_nacimiento, today)
            if empleado.fecha_contratacion:
                start_date = empleado.fecha_contratacion
                end_date = empleado.fecha_inactivacion if not empleado.activo and empleado.fecha_inactivacion else today
                empleado.dias_laborados = (end_date - start_date).days
            else:
                empleado.dias_laborados = 0

        context['departamentos'] = Departamento.objects.all().order_by('nombre')
        context['puestos'] = Puesto.objects.all().order_by('nombre')
        context['tipos_viaje'] = TipoViaje.objects.all().order_by('nombre')
        context['empresas'] = Empleado.EMPRESA_CHOICES
        context['total_empleados'] = self.model.objects.count()
        context['empleados_activos'] = self.model.objects.filter(activo=True).count()
        context['empleados_inactivos'] = self.model.objects.filter(activo=False).count()

        current_get_params = self.request.GET.copy()
        if 'page' in current_get_params:
            del current_get_params['page']
        context['query_string'] = current_get_params.urlencode()
        
        return context

def calculate_age(birth_date, current_date):
    if not birth_date:
        return None
    age = current_date.year - birth_date.year
    if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

# ==============================================================================
# === GESTIÓN DE EMPLEADOS (CRUD + FORMSETS + S3) ===
# ==============================================================================

# Formsets
DocumentoOperadorFormSet = inlineformset_factory(
    Empleado, DocumentoOperador, form=DocumentoOperadorForm, extra=0, can_delete=True
)
HistorialLaboralFormSet = inlineformset_factory(
    Empleado, HistorialLaboral, form=HistorialLaboralForm, fk_name='empleado', extra=0, can_delete=True
)
SalarioFormSet = inlineformset_factory(
    Empleado, Salario, form=SalarioForm, extra=0, can_delete=True
)
ContratoFormSet = inlineformset_factory(
    Empleado, Contrato, form=ContratoForm, extra=0, can_delete=True
)
HijoFormSet = inlineformset_factory(
    Empleado, Hijo, fields=['nombre', 'fecha_nacimiento'], extra=0, can_delete=True
)

class EmpleadoCreateView(CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'rh/empleado_form.html'
    success_url = reverse_lazy('rh:lista_empleados')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['documentos_operador_formset'] = DocumentoOperadorFormSet(self.request.POST, self.request.FILES, prefix='documentos_operador')
            data['historial_laboral_formset'] = HistorialLaboralFormSet(self.request.POST, self.request.FILES, prefix='historial_laboral')
            data['salario_formset'] = SalarioFormSet(self.request.POST, prefix='salarios')
            data['contrato_formset'] = ContratoFormSet(self.request.POST, self.request.FILES, prefix='contratos')
            data['hijos_formset'] = HijoFormSet(self.request.POST, prefix='hijos')
        else:
            data['documentos_operador_formset'] = DocumentoOperadorFormSet(prefix='documentos_operador')
            data['historial_laboral_formset'] = HistorialLaboralFormSet(prefix='historial_laboral')
            data['salario_formset'] = SalarioFormSet(prefix='salarios')
            data['contrato_formset'] = ContratoFormSet(prefix='contratos')
            data['hijos_formset'] = HijoFormSet(prefix='hijos')
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        formsets = {
            'documentos_operador': context['documentos_operador_formset'],
            'historial_laboral': context['historial_laboral_formset'],
            'salarios': context['salario_formset'],
            'contratos': context['contrato_formset'],
            'hijos': context['hijos_formset']
        }
        
        if all(fs.is_valid() for fs in formsets.values()):
            with transaction.atomic():
                self.object = form.save()
                for fs in formsets.values():
                    fs.instance = self.object
                    fs.save()
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Tu lógica original de manejo de errores
        context = self.get_context_data(form=form)
        all_errors = []
        if form.errors:
            for field, error_list in form.errors.items():
                field_label = form.fields.get(field).label if form.fields.get(field) else field
                all_errors.append(f"Error en '{field_label}': {error_list[0]}")
        # ... (resto de la lógica de formsets)
        context['all_errors'] = all_errors
        return self.render_to_response(context)


class EmpleadoUpdateView(UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'rh/empleado_form.html'
    context_object_name = 'empleado'
    success_url = reverse_lazy('rh:lista_empleados')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['documentos_operador_formset'] = DocumentoOperadorFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='documentos_operador')
            data['historial_laboral_formset'] = HistorialLaboralFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='historial_laboral')
            data['salario_formset'] = SalarioFormSet(self.request.POST, instance=self.object, prefix='salarios')
            data['contrato_formset'] = ContratoFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='contratos')
            data['hijos_formset'] = HijoFormSet(self.request.POST, instance=self.object, prefix='hijos')
        else:
            data['documentos_operador_formset'] = DocumentoOperadorFormSet(instance=self.object, prefix='documentos_operador')
            data['historial_laboral_formset'] = HistorialLaboralFormSet(instance=self.object, prefix='historial_laboral')
            data['salario_formset'] = SalarioFormSet(instance=self.object, prefix='salarios')
            data['contrato_formset'] = ContratoFormSet(instance=self.object, prefix='contratos')
            data['hijos_formset'] = HijoFormSet(instance=self.object, prefix='hijos')
        
        # Cálculo de estadísticas para el dashboard interno de edición
        if self.object:
            employee = self.object
            historial = employee.historial_laboral_eventos.all()
            tenure_days = (date.today() - employee.fecha_contratacion).days if employee.fecha_contratacion else 0
            years_service = tenure_days / 365.25
            vacation_days = 0
            # Lógica simplificada de vacaciones (según tu código)
            if years_service >= 1:
                if years_service < 2: vacation_days = 12
                elif years_service < 3: vacation_days = 14
                elif years_service < 4: vacation_days = 16
                elif years_service < 5: vacation_days = 18
                else: vacation_days = 20 + ((int(years_service) - 5) // 5) * 2
            
            latest_salary = employee.salarios.order_by('-fecha_efectiva').first()
            data['dashboard_stats'] = {
                'vacaciones_disponibles': vacation_days,
                'sueldo_mensual': f"${latest_salary.sueldo_mensual:,.2f}" if latest_salary else "N/A",
                'actas_administrativas': historial.filter(tipo_evento='ACTA_ADMINISTRATIVA').count(),
                'suspensiones': historial.filter(tipo_evento='SUSPENSION').count(),
                'recontrataciones': historial.filter(tipo_evento='RECONTRATACION').count(),
                'permisos': historial.filter(tipo_evento='PERMISO').count()
            }
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        formsets = {
            'documentos_operador': context['documentos_operador_formset'],
            'historial_laboral': context['historial_laboral_formset'],
            'salarios': context['salario_formset'],
            'contratos': context['contrato_formset'],
            'hijos': context['hijos_formset']
        }
        
        if all(fs.is_valid() for fs in formsets.values()):
            original_activo = self.get_object().activo
            new_activo = form.cleaned_data['activo']
            
            # --- LOGICA S3: Obtener instancia vieja para comparar archivos ---
            old_instance = Empleado.objects.get(pk=self.object.pk)
            file_fields = [
                'foto_perfil', 'ine_documento', 'comprobante_domicilio', 'curriculum_vitae',
                'acta_nacimiento_documento', 'comprobante_estudios_documento',
                'carta_recomendacion_1_documento', 'carta_recomendacion_2_documento',
                'constancia_fiscal_documento', 'aviso_retencion_infonavit_documento',
                'semanas_cotizadas_imss_documento'
            ]
            
            with transaction.atomic():
                self.object = form.save(commit=False)
                
                # Lógica de activación/desactivación automática
                if original_activo and not new_activo:
                    self.object.fecha_inactivacion = date.today()
                elif not original_activo and new_activo:
                    self.object.motivo_inactivacion = None
                    self.object.fecha_inactivacion = None
                
                self.object.save()
                form.save_m2m()

                for fs in formsets.values():
                    fs.instance = self.object
                    fs.save()
                
                # --- LOGICA S3: Borrar archivos viejos si cambiaron ---
                for field in file_fields:
                    old_file = getattr(old_instance, field)
                    new_file = getattr(self.object, field)
                    if old_file and old_file != new_file:
                        _eliminar_archivo_de_s3(old_file.name)

            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        all_errors = []
        if form.errors:
             for field, error_list in form.errors.items():
                field_label = form.fields.get(field).label if form.fields.get(field) else field
                all_errors.append(f"Error en '{field_label}': {error_list[0]}")
        
        # Mensajes genéricos para formsets
        formset_names = {
            "Documentos de Operador": context['documentos_operador_formset'],
            "Contratos": context['contrato_formset'],
            "Historial Laboral": context['historial_laboral_formset'],
            "Salarios": context['salario_formset'],
            "Hijos": context['hijos_formset']
        }
        for name, fs in formsets_names.items(): # typo corrected in loop var
            if fs.errors:
                 for form_errors in fs.errors:
                    if form_errors:
                        all_errors.append(f"Revisa la sección '{name}'. Datos incompletos/incorrectos.")
        
        context['all_errors'] = all_errors
        return self.render_to_response(context)


class EmpleadoDetailView(DetailView):
    model = Empleado
    template_name = 'rh/empleado_detail.html'
    context_object_name = 'empleado'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documentos_operador'] = self.object.documentos_operador.all().select_related('tipo_documento')
        return context

class EmpleadoDeleteView(DeleteView):
    model = Empleado
    template_name = 'rh/empleado_confirm_delete.html'
    context_object_name = 'empleado'
    success_url = reverse_lazy('rh:lista_empleados')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            # --- LOGICA S3: Recolectar archivos antes de borrar ---
            archivos_a_borrar = []
            
            # 1. Archivos directos
            campos_archivo = [
                'foto_perfil', 'ine_documento', 'comprobante_domicilio', 'curriculum_vitae',
                'acta_nacimiento_documento', 'comprobante_estudios_documento',
                'carta_recomendacion_1_documento', 'carta_recomendacion_2_documento',
                'constancia_fiscal_documento', 'aviso_retencion_infonavit_documento',
                'semanas_cotizadas_imss_documento'
            ]
            for campo in campos_archivo:
                archivo = getattr(self.object, campo)
                if archivo:
                    archivos_a_borrar.append(archivo.name)
            
            # 2. Documentos Operador
            for doc in self.object.documentos_operador.all():
                if doc.archivo:
                    archivos_a_borrar.append(doc.archivo.name)
            
            # 3. Contratos
            for contrato in self.object.contratos.all():
                if contrato.archivo_contrato:
                    archivos_a_borrar.append(contrato.archivo_contrato.name)

            # Borrar de la BD
            self.object.delete()

            # Borrar de S3
            for ruta in archivos_a_borrar:
                _eliminar_archivo_de_s3(ruta)
                
            return redirect(self.success_url)
        except Exception as e:
             # Manejo básico de error, podrías agregar messages.error
             return redirect(self.success_url)

# ==============================================================================
# === IMPORTACIÓN EXCEL CON VINCULACIÓN S3 (NUEVO) ===
# ==============================================================================

class ImportarEmpleadosExcelView(RHAdminRequiredMixin, FormView):
    template_name = 'rh/importar_empleados.html'
    success_url = reverse_lazy('rh:lista_empleados')
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'titulo': 'Migración Masiva (Excel)'})

    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, "Selecciona el archivo Excel.")
            return redirect(request.path)

        try:
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            creados = 0
            errores = []
            
            # Rutas base en tu Bucket S3 (Ajusta si tus carpetas se llaman diferente)
            S3_PREFIX_FOTOS = 'empleados_fotos/' 
            S3_PREFIX_INE = 'empleados_documentos/ine/'

            with transaction.atomic():
                # Empezamos en la fila 2 (saltando encabezados)
                for index, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    try:
                        # Mapeo EXACTO con la función de Exportar de arriba
                        # 0:Num, 1:Nom, 2:Ape, 3:Email, 4:Ingreso, 5:Puesto, 6:Depto
                        # 7:Sueldo, 8:TipoContrato, 9:Nacimiento, 10:CURP, 11:RFC, 12:NSS, 13:Tel
                        # 14:Foto, 15:INE
                        
                        (num_emp, nombre, apellido, email, fecha_ingreso, nombre_puesto, 
                         nombre_depto, sueldo_diario, tipo_contrato, fecha_nacimiento, 
                         curp, rfc, nss, telefono, foto_name, ine_name) = row[:16]
                        
                        if not nombre or not apellido: continue

                        # 1. Validar Fechas (Excel a veces las da como string)
                        if isinstance(fecha_ingreso, str):
                            fecha_ingreso = timezone.datetime.strptime(fecha_ingreso, '%Y-%m-%d').date()
                        if not fecha_ingreso: fecha_ingreso = timezone.now().date()
                            
                        if isinstance(fecha_nacimiento, str):
                            fecha_nacimiento = timezone.datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()

                        # 2. Crear/Buscar Catálogos
                        puesto_obj, _ = Puesto.objects.get_or_create(nombre=nombre_puesto) if nombre_puesto else (None, False)
                        depto_obj, _ = Departamento.objects.get_or_create(nombre=nombre_depto) if nombre_depto else (None, False)

                        # 3. Crear Empleado
                        empleado = Empleado(
                            numero_empleado=str(num_emp) if num_emp else None,
                            nombre=nombre,
                            apellido=apellido,
                            email=email,
                            fecha_contratacion=fecha_ingreso,
                            puesto=puesto_obj,
                            departamento=depto_obj,
                            fecha_nacimiento=fecha_nacimiento,
                            curp=curp, rfc=rfc, nss=str(nss) if nss else None,
                            telefono_personal=str(telefono) if telefono else None,
                            activo=True
                        )

                        # 4. Vincular Archivos S3 (Solo el nombre, Django asume que ya están en el bucket)
                        if foto_name: empleado.foto_perfil.name = f"{S3_PREFIX_FOTOS}{foto_name}"
                        if ine_name: empleado.ine_documento.name = f"{S3_PREFIX_INE}{ine_name}"
                        
                        empleado.save()

                        # 5. Crear Registro de Salario Inicial (Si viene en el Excel)
                        if sueldo_diario:
                            Salario.objects.create(
                                empleado=empleado,
                                sueldo_diario=float(sueldo_diario),
                                fecha_efectiva=fecha_ingreso, # Asume salario desde que entró
                                observaciones="Carga Inicial por Migración Excel"
                            )

                        # 6. Crear Contrato Inicial (Si viene en el Excel)
                        if tipo_contrato:
                            Contrato.objects.create(
                                empleado=empleado,
                                tipo_contrato=tipo_contrato,
                                fecha_inicio=fecha_ingreso,
                                comentarios="Carga Inicial por Migración Excel"
                            )

                        creados += 1
                        
                    except Exception as e:
                        errores.append(f"Fila {index} ({nombre} {apellido}): {str(e)}")
            
            if creados > 0:
                messages.success(request, f"¡Éxito! Se migraron {creados} empleados con sus salarios y contratos.")
            
            if errores:
                messages.warning(request, f"Hubo problemas en {len(errores)} filas. Revisa: {', '.join(errores[:3])}")
                
            return redirect(self.success_url)

        except Exception as e:
            messages.error(request, f"Error crítico en el archivo: {e}")
            return redirect(request.path)

def descargar_plantilla_importacion(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plantilla Empleados"
    headers = ["Numero Empleado", "Nombre", "Apellido", "Fecha Ingreso (AAAA-MM-DD)", "Puesto", "Departamento", "Email", "Nombre Archivo Foto (S3)", "Nombre Archivo INE (S3)"]
    ws.append(headers)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_empleados.xlsx"'
    wb.save(response)
    return response

# ==============================================================================
# === CRUDs DE CATALOGOS (Departamentos, Puestos, etc) ===
# ==============================================================================

# Departamentos
class DepartamentoListView(ListView):
    model = Departamento
    template_name = 'rh/lista_departamentos.html'
    context_object_name = 'departamentos'
    ordering = ['nombre']
class DepartamentoCreateView(CreateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'rh/departamento_form.html'
    success_url = reverse_lazy('rh:lista_departamentos')
class DepartamentoDetailView(DetailView):
    model = Departamento
    template_name = 'rh/departamento_detail.html'
    context_object_name = 'departamento'
class DepartamentoUpdateView(UpdateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'rh/departamento_form.html'
    success_url = reverse_lazy('rh:lista_departamentos')
class DepartamentoDeleteView(DeleteView):
    model = Departamento
    template_name = 'rh/departamento_confirm_delete.html'
    context_object_name = 'departamento'
    success_url = reverse_lazy('rh:lista_departamentos')

# Puestos
class PuestoListView(ListView):
    model = Puesto
    template_name = 'rh/lista_puestos.html'
    context_object_name = 'puestos'
    ordering = ['nombre']
class PuestoCreateView(CreateView):
    model = Puesto
    form_class = PuestoForm
    template_name = 'rh/puesto_form.html'
    success_url = reverse_lazy('rh:lista_puestos')
class PuestoDetailView(DetailView):
    model = Puesto
    template_name = 'rh/puesto_detail.html'
    context_object_name = 'puesto'
class PuestoUpdateView(UpdateView):
    model = Puesto
    form_class = PuestoForm
    template_name = 'rh/puesto_form.html'
    success_url = reverse_lazy('rh:lista_puestos')
class PuestoDeleteView(DeleteView):
    model = Puesto
    template_name = 'rh/puesto_confirm_delete.html'
    context_object_name = 'puesto'
    success_url = reverse_lazy('rh:lista_puestos')

# Motivos Inactivación
class MotivoInactivacionListView(ListView):
    model = MotivoInactivacion
    template_name = 'rh/lista_motivos_inactivacion.html'
    context_object_name = 'motivos'
    ordering = ['motivo']
class MotivoInactivacionCreateView(CreateView):
    model = MotivoInactivacion
    form_class = MotivoInactivacionForm
    template_name = 'rh/motivo_inactivacion_form.html'
    success_url = reverse_lazy('rh:lista_motivos_inactivacion')
class MotivoInactivacionUpdateView(UpdateView):
    model = MotivoInactivacion
    form_class = MotivoInactivacionForm
    template_name = 'rh/motivo_inactivacion_form.html'
    success_url = reverse_lazy('rh:lista_motivos_inactivacion')
class MotivoInactivacionDeleteView(DeleteView):
    model = MotivoInactivacion
    template_name = 'rh/motivo_inactivacion_confirm_delete.html'
    context_object_name = 'motivo'
    success_url = reverse_lazy('rh:lista_motivos_inactivacion')

# Tipo Documento Operador
class TipoDocumentoOperadorListView(ListView):
    model = TipoDocumentoOperador
    template_name = 'rh/lista_tipos_documento_operador.html'
    context_object_name = 'tipos_documento'
    ordering = ['nombre']
class TipoDocumentoOperadorCreateView(CreateView):
    model = TipoDocumentoOperador
    form_class = TipoDocumentoOperadorForm
    template_name = 'rh/tipo_documento_operador_form.html'
    success_url = reverse_lazy('rh:lista_tipos_documento_operador')
class TipoDocumentoOperadorUpdateView(UpdateView):
    model = TipoDocumentoOperador
    form_class = TipoDocumentoOperadorForm
    template_name = 'rh/tipo_documento_operador_form.html'
    success_url = reverse_lazy('rh:lista_tipos_documento_operador')
class TipoDocumentoOperadorDeleteView(DeleteView):
    model = TipoDocumentoOperador
    template_name = 'rh/tipo_documento_operador_confirm_delete.html'
    context_object_name = 'tipo_documento'
    success_url = reverse_lazy('rh:lista_tipos_documento_operador')

# ==============================================================================
# === REPORTES Y EXPORTACIONES ===
# ==============================================================================

def generar_pdf_empleado(request, pk):
    """ Genera PDF usando xhtml2pdf (Tu lógica original) """
    empleado = get_object_or_404(
        Empleado.objects.select_related(
            'puesto', 'departamento', 'supervisor', 'motivo_inactivacion'
        ).prefetch_related(
            'hijos', 'contratos', 'documentos_operador__tipo_documento',
            'salarios', 'historial_laboral_eventos', 'tipo_viaje',
            'tipo_carga', 'division_operativa'
        ),
        pk=pk
    )
    template_path = 'rh/empleado_pdf_template.html'
    context = {'empleado': empleado}
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ficha-empleado-{empleado.nombre}-{empleado.apellido}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
       return HttpResponse('Ocurrió un error al generar el PDF <pre>' + html + '</pre>')
    return response

def semaforo_documentos_view(request):
    """ Semáforo de vencimientos (Tu lógica original) """
    today = date.today()
    expirable_items = []

    documentos = DocumentoOperador.objects.filter(
        fecha_vencimiento__isnull=False,
        empleado__activo=True
    ).select_related('empleado', 'tipo_documento')

    for doc in documentos:
        expirable_items.append({
            'empleado': doc.empleado,
            'nombre_item': f"Doc. Operador: {doc.tipo_documento.nombre}",
            'fecha_vencimiento': doc.fecha_vencimiento,
            'comentarios': doc.observaciones
        })

    contratos_determinados = Contrato.objects.filter(
        tipo_contrato='DETERMINADO',
        fecha_fin__isnull=False,
        empleado__activo=True
    ).select_related('empleado')

    for contrato in contratos_determinados:
        expirable_items.append({
            'empleado': contrato.empleado,
            'nombre_item': 'Contrato Determinado',
            'fecha_vencimiento': contrato.fecha_fin,
            'comentarios': contrato.comentarios
        })

    expirable_items.sort(key=lambda x: x['fecha_vencimiento'])
    
    docs_rojo, docs_amarillo, docs_verde = [], [], []

    for item in expirable_items:
        days_remaining = (item['fecha_vencimiento'] - today).days
        item['dias_restantes'] = days_remaining
        if days_remaining <= 10: docs_rojo.append(item)
        elif days_remaining <= 30: docs_amarillo.append(item)
        else: docs_verde.append(item)

    context = {'docs_rojo': docs_rojo, 'docs_amarillo': docs_amarillo, 'docs_verde': docs_verde, 'today': today, 'page_title': 'Semáforo de Vencimientos'}
    return render(request, 'rh/semaforo_documentos.html', context)

def export_empleados_excel(request):
    """
    Exporta un Excel MAESTRO con toda la información necesaria para migrar a la nube.
    Incluye: Datos Personales, Puesto, Depto, Salario Actual y Datos de Contrato.
    """
    if not es_admin_rh(request.user):
        return HttpResponse("No autorizado", status=403)

    # Traemos todo para no hacer mil consultas
    empleados = Empleado.objects.all().select_related(
        'puesto', 'departamento'
    ).prefetch_related('salarios', 'contratos')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Migracion_Maestra"
    
    # Encabezados EXACTOS que usará el importador
    headers = [
        "Numero Empleado", "Nombre", "Apellido", "Email", 
        "Fecha Ingreso (AAAA-MM-DD)", "Puesto", "Departamento", 
        "Sueldo Diario", "Tipo Contrato (DETERMINADO/INDETERMINADO)", 
        "Fecha Nacimiento", "CURP", "RFC", "NSS", "Telefono",
        "Nombre Archivo Foto", "Nombre Archivo INE"
    ]
    ws.append(headers)
    
    # Estilo para encabezado
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
    
    for emp in empleados:
        # Obtener último salario y contrato vigente
        salario = emp.salarios.order_by('-fecha_efectiva').first()
        sueldo_diario = salario.sueldo_diario if salario else 0
        
        contrato = emp.contratos.order_by('-fecha_inicio').first()
        tipo_contrato = contrato.tipo_contrato if contrato else "INDETERMINADO"
        
        # Obtener nombres de archivos limpios (solo el nombre, sin la ruta completa)
        foto_name = os.path.basename(emp.foto_perfil.name) if emp.foto_perfil else ""
        ine_name = os.path.basename(emp.ine_documento.name) if emp.ine_documento else ""

        row = [
            emp.numero_empleado,
            emp.nombre,
            emp.apellido,
            emp.email,
            emp.fecha_contratacion,
            str(emp.puesto) if emp.puesto else "",
            str(emp.departamento) if emp.departamento else "",
            sueldo_diario,          # Dato clave para migración
            tipo_contrato,          # Dato clave para migración
            emp.fecha_nacimiento,
            emp.curp,
            emp.rfc,
            emp.nss,
            emp.telefono_personal,
            foto_name,              # Para vincular con S3
            ine_name                # Para vincular con S3
        ]
        ws.append(row)
        
    # Ajustar ancho columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length: max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = (max_length + 2)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="MIGRACION_RH_{timezone.now().date()}.xlsx"'
    wb.save(response)
    return response

def reporte_bajas(request):
    """ Reporte con gráficos (Tu lógica original) """
    eventos_baja = HistorialLaboral.objects.filter(tipo_evento__in=['RENUNCIA', 'BAJA', 'ABANDONO']).select_related('empleado').order_by('-fecha_inicio')

    if request.GET.get('export') == 'excel':
        data = []
        MOTIVO_SALIDA_CHOICES_FLAT = [choice for group in HistorialLaboral.MOTIVO_SALIDA_CHOICES for choice in group[1]]
        evento_choices_dict = dict(HistorialLaboral.EVENT_CHOICES)
        motivo_choices_dict = dict(MOTIVO_SALIDA_CHOICES_FLAT)

        for evento in eventos_baja:
            data.append({'ID Empleado': evento.empleado.id, 'Nombre Empleado': f"{evento.empleado.nombre} {evento.empleado.apellido}", 'Número de Empleado': evento.empleado.numero_empleado, 'Tipo de Evento': evento_choices_dict.get(evento.tipo_evento, evento.tipo_evento), 'Motivo de Salida': motivo_choices_dict.get(evento.motivo_salida, evento.motivo_salida), 'Fecha del Evento': evento.fecha_inicio, 'Comentario': evento.descripcion})
        
        df = pd.DataFrame(data)
        wb = openpyxl.Workbook()
        ws_data = wb.active
        ws_data.title = "Reporte de Bajas"
        for r in dataframe_to_rows(df, index=False, header=True): ws_data.append(r)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

        for col_idx, col in enumerate(ws_data.columns, 1):
            column_letter = get_column_letter(col_idx)
            for cell_idx, cell in enumerate(col):
                if cell_idx == 0:
                    cell.font = header_font
                    cell.fill = header_fill
                cell.alignment = center_align
        
        if not df.empty:
            ws_charts = wb.create_sheet("Graficas")
            df_charts = df.copy()
            df_charts['Fecha del Evento'] = pd.to_datetime(df_charts['Fecha del Evento'])
            monthly_counts = df_charts.groupby(df_charts['Fecha del Evento'].dt.strftime('%Y-%m')).size().reset_index(name='Total').sort_values(by='Fecha del Evento')
            weekly_counts = df_charts.groupby(df_charts['Fecha del Evento'].dt.strftime('%Y-W%U')).size().reset_index(name='Total').sort_values(by='Fecha del Evento')
            
            ws_charts.append(['Mes', 'Total Bajas'])
            for _, row in monthly_counts.iterrows(): ws_charts.append(list(row))
            ws_charts.append([])
            start_row_weekly = ws_charts.max_row + 1
            ws_charts.append(['Semana', 'Total Bajas'])
            for _, row in weekly_counts.iterrows(): ws_charts.append(list(row))

            chart_monthly = BarChart()
            chart_monthly.title = "Bajas por Mes"
            chart_monthly.add_data(Reference(ws_charts, min_col=2, min_row=1, max_row=len(monthly_counts)+1, max_col=2), titles_from_data=True)
            chart_monthly.set_categories(Reference(ws_charts, min_col=1, min_row=2, max_row=len(monthly_counts)+1))
            ws_charts.add_chart(chart_monthly, "D2")

            chart_weekly = BarChart()
            chart_weekly.title = "Bajas por Semana"
            chart_weekly.add_data(Reference(ws_charts, min_col=2, min_row=start_row_weekly, max_row=ws_charts.max_row, max_col=2), titles_from_data=True)
            chart_weekly.set_categories(Reference(ws_charts, min_col=1, min_row=start_row_weekly + 1, max_row=ws_charts.max_row))
            ws_charts.add_chart(chart_weekly, "D20")

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte_bajas_personal.xlsx"'
        wb.save(response)
        return response

    context = {'eventos_baja': eventos_baja}
    return render(request, 'rh/reportes.html', context)

def dashboard_view(request):
    """ Dashboard Operativo (Tu lógica original) """
    selected_company = request.GET.get('empresa', 'MIGMAR')
    base_operadores = Empleado.objects.filter(activo=True, empresa=selected_company, puesto__nombre__icontains='Operador').order_by('apellido', 'nombre')
    total_operadores = base_operadores.count()
    
    operadores_local_foraneo_list = base_operadores.filter(tipo_viaje__nombre='Local').filter(tipo_viaje__nombre='Foraneo').distinct()
    operadores_local_foraneo = operadores_local_foraneo_list.count()
    ids_ambos = set(operadores_local_foraneo_list.values_list('id', flat=True))

    operadores_locales_list = base_operadores.filter(tipo_viaje__nombre='Local').exclude(id__in=ids_ambos)
    operadores_locales = operadores_locales_list.count()
    operadores_foraneos_list = base_operadores.filter(tipo_viaje__nombre='Foraneo').exclude(id__in=ids_ambos)
    operadores_foraneos = operadores_foraneos_list.count()

    grupos_de_interes = ['Autozone', 'Walmart', 'Bafar', 'Femsa', 'Sams', 'Bodega Aurrera']
    frecuencia_por_grupo = [{'grupo': g, 'total': base_operadores.filter(division_operativa__nombre=g).count()} for g in grupos_de_interes]

    ops_autozone = set(base_operadores.filter(division_operativa__nombre='Autozone').values_list('id', flat=True))
    ops_walmart = set(base_operadores.filter(division_operativa__nombre='Walmart').values_list('id', flat=True))
    ops_sams = set(base_operadores.filter(division_operativa__nombre='Sams').values_list('id', flat=True))

    venn_data = {
        'autozone_total': len(ops_autozone),
        'walmart_total': len(ops_walmart),
        'sams_total': len(ops_sams),
        'autozone_walmart': len(ops_autozone.intersection(ops_walmart)),
        'autozone_sams': len(ops_autozone.intersection(ops_sams)),
        'walmart_sams': len(ops_walmart.intersection(ops_sams)),
        'autozone_walmart_sams': len(ops_autozone.intersection(ops_walmart).intersection(ops_sams)),
    }

    context = {'page_title': 'Dashboard de Operadores', 'selected_company': selected_company, 'total_operadores': total_operadores, 'operadores_locales': operadores_locales, 'operadores_foraneos': operadores_foraneos, 'operadores_locales_list': operadores_locales_list, 'operadores_foraneos_list': operadores_foraneos_list, 'operadores_local_foraneo_list': operadores_local_foraneo_list, 'operadores_local_foraneo': operadores_local_foraneo, 'frecuencia_por_grupo': frecuencia_por_grupo, 'venn_data': venn_data}
    return render(request, 'rh/dashboard.html', context)

def vacantes_dashboard_view(request):
    """ Dashboard Vacantes (Tu lógica original) """
    today = date.today()
    tipos_baja = ['RENUNCIA', 'BAJA', 'ABANDONO']
    vacantes = HistorialLaboral.objects.filter(tipo_evento__in=tipos_baja).select_related('empleado__departamento', 'empleado__puesto', 'reemplazo').order_by('estatus', '-fecha_inicio')

    for vacante in vacantes:
        if vacante.estatus == 'BUSCANDO':
            vacante.dias_transcurridos = (today - vacante.fecha_inicio).days
            if vacante.empleado and vacante.empleado.puesto and vacante.empleado.departamento:
                vacante.potenciales_reemplazos = Empleado.objects.filter(activo=True, puesto=vacante.empleado.puesto, departamento=vacante.empleado.departamento).exclude(id=vacante.empleado.id)
            else: vacante.potenciales_reemplazos = Empleado.objects.none()
        else:
            vacante.dias_transcurridos = (vacante.fecha_reemplazo - vacante.fecha_inicio).days if vacante.fecha_reemplazo else 0

    pie_chart_data, bar_chart_data = {}, {}
    for empresa in ['MIGMAR', 'MARCO_MORALES']:
        activos = Empleado.objects.filter(activo=True, empresa=empresa).count()
        pendientes = HistorialLaboral.objects.filter(tipo_evento__in=tipos_baja, empleado__empresa=empresa, estatus='BUSCANDO').count()
        pie_chart_data[empresa] = {'activos': activos, 'pendientes': pendientes}
        avg_days_data = HistorialLaboral.objects.filter(empleado__empresa=empresa, estatus='REMPLAZADO', fecha_reemplazo__isnull=False).values('empleado__departamento__nombre').annotate(avg_days=Avg(F('fecha_reemplazo') - F('fecha_inicio'))).values('empleado__departamento__nombre', 'avg_days')
        bar_chart_data[empresa] = {'departamento': [{'name': item['empleado__departamento__nombre'], 'avg_days': item['avg_days'].days if item['avg_days'] else 0} for item in avg_days_data if item['empleado__departamento__nombre']]}

    context = {'vacantes': vacantes, 'pie_chart_data': pie_chart_data, 'bar_chart_data': bar_chart_data}
    return render(request, 'rh/vacantes_dashboard.html', context)

def asignar_reemplazo(request, pk):
    if request.method == 'POST':
        vacante = get_object_or_404(HistorialLaboral, pk=pk)
        reemplazo_id = request.POST.get('reemplazo_id')
        if reemplazo_id:
            reemplazo = get_object_or_404(Empleado, pk=reemplazo_id)
            vacante.reemplazo = reemplazo
            vacante.estatus = 'REMPLAZADO'
            vacante.fecha_reemplazo = date.today()
            vacante.save()
    return redirect('rh:vacantes_dashboard')

def reporte_documentacion_operador(request):
    """ Reporte cumplimiento documentos (Tu lógica original) """
    todos_los_tipos_requeridos = TipoDocumentoOperador.objects.all()
    mapa_tipos_requeridos = {tipo.id: tipo.nombre for tipo in todos_los_tipos_requeridos}
    ids_tipos_requeridos = set(mapa_tipos_requeridos.keys())
    operadores_activos = Empleado.objects.filter(activo=True, puesto__nombre__icontains='Operador').prefetch_related('documentos_operador')

    operadores_incompletos = []
    for operador in operadores_activos:
        ids_documentos_entregados = set(operador.documentos_operador.values_list('tipo_documento_id', flat=True))
        ids_documentos_faltantes = ids_tipos_requeridos - ids_documentos_entregados
        if ids_documentos_faltantes:
            nombres_documentos_faltantes = [mapa_tipos_requeridos[id_faltante] for id_faltante in ids_documentos_faltantes]
            operadores_incompletos.append({'operador': operador, 'documentos_faltantes': nombres_documentos_faltantes})

    context = {'operadores_incompletos': operadores_incompletos}
    return render(request, 'rh/reporte_cumplimiento_docs.html', context)

def cumpleanos_rh(request):
    """ Vista de cumpleaños (Tu lógica original) """
    try:
        import locale
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except: pass

    today = date.today()
    empleados_mes = Empleado.objects.filter(fecha_nacimiento__month=today.month, activo=True).order_by('fecha_nacimiento__day')
    lista_cumpleanos_mes, cumpleanos_hoy = [], []

    for emp in empleados_mes:
        try: cumple_este_ano = date(today.year, emp.fecha_nacimiento.month, emp.fecha_nacimiento.day)
        except ValueError: cumple_este_ano = date(today.year, 2, 28)
        edad = today.year - emp.fecha_nacimiento.year
        dias_faltantes = (cumple_este_ano - today).days
        es_hoy, ya_paso = (dias_faltantes == 0), (dias_faltantes < 0)
        data = {'empleado': emp, 'dia_nacimiento': emp.fecha_nacimiento.day, 'fecha_cumple': cumple_este_ano, 'edad_a_cumplir': edad, 'dias_faltantes': dias_faltantes, 'dias_faltantes_abs': abs(dias_faltantes), 'es_hoy': es_hoy, 'ya_paso': ya_paso}
        lista_cumpleanos_mes.append(data)
        if es_hoy: cumpleanos_hoy.append(data)

    nombre_mes = today.strftime('%B').capitalize()
    context = {'cumpleanos_hoy': cumpleanos_hoy, 'lista_cumpleanos_mes': lista_cumpleanos_mes, 'nombre_mes': nombre_mes, 'today': today}
    return render(request, 'rh/cumpleanos.html', context)