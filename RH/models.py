# RH/models.py
from django.db import models
from django.core.validators import RegexValidator
import os
import uuid
from django.contrib.auth.models import User
from datetime import date

# --- Funciones de subida de archivos ---
def get_upload_path(instance, filename, path):
    """ Genera una ruta de archivo única usando UUID. """
    ext = os.path.splitext(filename)[1]
    new_filename = f"{uuid.uuid4()}{ext}"
    return os.path.join(path, new_filename)

def empleado_foto_perfil_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_fotos/')

def empleado_ine_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/ine/')

def empleado_domicilio_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/domicilio/')

def empleado_cv_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/cv/')

def operador_documento_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/operador/')

def historial_documento_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/historial/')

def contrato_documento_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/contratos/')

# --- Rutas para nuevos documentos ---
def empleado_acta_nacimiento_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/acta_nacimiento/')

def empleado_comprobante_estudios_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/estudios/')

def empleado_carta_recomendacion_1_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/recomendacion/')

def empleado_carta_recomendacion_2_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/recomendacion/')

def empleado_constancia_fiscal_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/fiscal/')

def empleado_aviso_infonavit_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/infonavit/')

def empleado_semanas_imss_path(instance, filename):
    return get_upload_path(instance, filename, 'empleados_documentos/imss/')


class DivisionOperativa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "División Operativa"
        verbose_name_plural = "Divisiones Operativas"
        ordering = ['nombre']
        
class TipoCarga(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class TipoViaje(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='departamentos_creados')

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

    def __str__(self):
        return self.nombre

class Puesto(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre del puesto (ej. 'Gerente de Ventas', 'Operador de Tráfico')")
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción detallada del puesto.")
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Salario base mensual para este puesto.")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='puestos_creados')

    class Meta:
        verbose_name = "Puesto"
        verbose_name_plural = "Puestos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class MotivoInactivacion(models.Model):
    motivo = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Motivo de Inactivación"
        verbose_name_plural = "Motivos de Inactivación"
        ordering = ['motivo']

    def __str__(self):
        return self.motivo

class Empleado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_empleado = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="Número de empleado interno único")
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    puesto = models.CharField(max_length=150, verbose_name="Puesto")
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados')
    fecha_contratacion = models.DateField()
    email = models.EmailField(unique=True, null=True, blank=True)
    activo = models.BooleanField(default=True)
    motivo_inactivacion = models.ForeignKey(MotivoInactivacion, on_delete=models.SET_NULL, null=True, blank=True, help_text="Motivo por el cual el empleado fue inactivado.")
    fecha_inactivacion = models.DateField(null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    # --- CAMPOS DE DOMICILIO MEJORADOS ---
    direccion = models.CharField(max_length=255, blank=True, null=True, help_text="Calle y número")
    colonia = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=50, default="México", blank=True, null=True)
    
    telefono_personal = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="El número de teléfono debe estar en el formato: '+999999999'. Hasta 15 dígitos permitidos."
            ),
        ],
        help_text="Formato: +999999999. Máx. 15 dígitos."
    )
    ESTADO_CIVIL_CHOICES = [
        ('Soltero/a', 'Soltero/a'),
        ('Casado/a', 'Casado/a'),
        ('Viudo/a', 'Viudo/a'),
        ('Divorciado/a', 'Divorciado/a'),
        ('Unión Libre', 'Unión Libre'),
    ]
    estado_civil = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES, blank=True, null=True)
    nacionalidad = models.CharField(max_length=50, default="Mexicana", blank=True, null=True)
    curp = models.CharField(
        max_length=18,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{4}[0-9]{6}[H,M][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[0-9A-Z]{2}$',
                message="Formato de CURP inválido."
            ),
        ],
        help_text="CURP a 18 caracteres alfanuméricos."
    )
    rfc = models.CharField(
        max_length=13,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$',
                message="Formato de RFC inválido."
            ),
        ],
        help_text="RFC a 12 o 13 caracteres alfanuméricos."
    )
    nss = models.CharField(
        max_length=11,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message="NSS debe ser un número de 11 dígitos."
            ),
        ],
        help_text="Número de Seguro Social a 11 dígitos."
    )
    
    # --- NUEVOS CAMPOS DE FAMILIA Y SUPERVISOR ---
    supervisor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='equipo_a_cargo'
    )
    nombre_conyuge = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre del Cónyuge")
    telefono_conyuge = models.CharField(
        max_length=15, 
        blank=True, 
        null=True, 
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$', 
                message="El número de teléfono debe estar en el formato: '+999999999'. Hasta 15 dígitos permitidos."
            )
        ], 
        help_text="Formato: +999999999. Máx. 15 dígitos.", 
        verbose_name="Teléfono del Cónyuge"
    )
    
    foto_perfil = models.ImageField(upload_to=empleado_foto_perfil_path, null=True, blank=True)
    banco = models.CharField(max_length=100, blank=True, null=True)
    clabe_interbancaria = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{18}$',
                message="La CLABE debe ser un número de 18 dígitos."
            ),
        ],
        help_text="CLABE Interbancaria a 18 dígitos."
    )
    numero_cuenta = models.CharField(max_length=20, blank=True, null=True)
    numero_tarjeta = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{16}$',
                message="El número de tarjeta debe ser de 16 dígitos."
            ),
        ],
        help_text="Número de tarjeta de débito/crédito a 16 dígitos.",
        verbose_name="Número de Tarjeta"
    )
    nombre_referencia_1 = models.CharField(max_length=100, blank=True, null=True)
    telefono_referencia_1 = models.CharField(max_length=15, blank=True, null=True)
    relacion_referencia_1 = models.CharField(max_length=50, blank=True, null=True)
    nombre_referencia_2 = models.CharField(max_length=100, blank=True, null=True)
    telefono_referencia_2 = models.CharField(max_length=15, blank=True, null=True)
    relacion_referencia_2 = models.CharField(max_length=50, blank=True, null=True)
    
    # --- Documentos Existentes ---
    ine_documento = models.FileField(upload_to=empleado_ine_path, null=True, blank=True, help_text="Copia de INE/Identificación oficial")
    comprobante_domicilio = models.FileField(upload_to=empleado_domicilio_path, null=True, blank=True, help_text="Comprobante de domicilio reciente")
    curriculum_vitae = models.FileField(upload_to=empleado_cv_path, null=True, blank=True, help_text="Currículum Vitae")

    # --- NUEVOS CAMPOS DE DOCUMENTOS ---
    acta_nacimiento_documento = models.FileField(upload_to=empleado_acta_nacimiento_path, null=True, blank=True, verbose_name="Acta de Nacimiento")
    comprobante_estudios_documento = models.FileField(upload_to=empleado_comprobante_estudios_path, null=True, blank=True, verbose_name="Comprobante de Estudios")
    carta_recomendacion_1_documento = models.FileField(upload_to=empleado_carta_recomendacion_1_path, null=True, blank=True, verbose_name="Carta de Recomendación 1")
    carta_recomendacion_2_documento = models.FileField(upload_to=empleado_carta_recomendacion_2_path, null=True, blank=True, verbose_name="Carta de Recomendación 2")
    constancia_fiscal_documento = models.FileField(upload_to=empleado_constancia_fiscal_path, null=True, blank=True, verbose_name="Constancia Fiscal (RFC)")
    aviso_retencion_infonavit_documento = models.FileField(upload_to=empleado_aviso_infonavit_path, null=True, blank=True, verbose_name="Aviso de Retención de Infonavit")
    semanas_cotizadas_imss_documento = models.FileField(upload_to=empleado_semanas_imss_path, null=True, blank=True, verbose_name="Semanas Cotizadas IMSS")

    # --- Campos de Información Operativa ---
    EMPRESA_CHOICES = [
        ('MIGMAR', 'Migmar'),
        ('MARCO_MORALES', 'Marco Morales'),
    ]
    empresa = models.CharField(max_length=20, choices=EMPRESA_CHOICES, blank=True, null=True, verbose_name="Empresa")
    division_operativa = models.ManyToManyField(DivisionOperativa, blank=True, verbose_name="División Operativa")
    tipo_carga = models.ManyToManyField(TipoCarga, blank=True, verbose_name="Tipo de Carga")
    tipo_viaje = models.ManyToManyField(TipoViaje, blank=True, verbose_name="Tipo de Viaje")
    
    # --- PROPIEDADES PARA SIMPLIFICAR PLANTILLAS ---
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

    @property
    def antiguedad(self):
        if not self.fecha_contratacion:
            return 0
        return (date.today() - self.fecha_contratacion).days // 365

    @property
    def salario_actual(self):
        return self.salarios.order_by('-fecha_efectiva').first()

    @property
    def documentos_count(self):
        base_docs = 0
        if self.ine_documento: base_docs += 1
        if self.comprobante_domicilio: base_docs += 1
        if self.curriculum_vitae: base_docs += 1
        if self.acta_nacimiento_documento: base_docs += 1
        if self.comprobante_estudios_documento: base_docs += 1
        if self.carta_recomendacion_1_documento: base_docs += 1
        if self.carta_recomendacion_2_documento: base_docs += 1
        if self.constancia_fiscal_documento: base_docs += 1
        if self.aviso_retencion_infonavit_documento: base_docs += 1
        if self.semanas_cotizadas_imss_documento: base_docs += 1
        return base_docs + self.documentos_operador.count() + self.contratos.count()
    
    @property
    def companeros_departamento(self):
        if not self.departamento:
            return Empleado.objects.none()
        return Empleado.objects.filter(departamento=self.departamento, activo=True).exclude(pk=self.pk)

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def delete(self, *args, **kwargs):
        if self.foto_perfil and os.path.isfile(self.foto_perfil.path):
            os.remove(self.foto_perfil.path)
        if self.ine_documento and os.path.isfile(self.ine_documento.path):
            os.remove(self.ine_documento.path)
        if self.comprobante_domicilio and os.path.isfile(self.comprobante_domicilio.path):
            os.remove(self.comprobante_domicilio.path)
        if self.curriculum_vitae and os.path.isfile(self.curriculum_vitae.path):
            os.remove(self.curriculum_vitae.path)
        if self.acta_nacimiento_documento and os.path.isfile(self.acta_nacimiento_documento.path):
            os.remove(self.acta_nacimiento_documento.path)
        if self.comprobante_estudios_documento and os.path.isfile(self.comprobante_estudios_documento.path):
            os.remove(self.comprobante_estudios_documento.path)
        if self.carta_recomendacion_1_documento and os.path.isfile(self.carta_recomendacion_1_documento.path):
            os.remove(self.carta_recomendacion_1_documento.path)
        if self.carta_recomendacion_2_documento and os.path.isfile(self.carta_recomendacion_2_documento.path):
            os.remove(self.carta_recomendacion_2_documento.path)
        if self.constancia_fiscal_documento and os.path.isfile(self.constancia_fiscal_documento.path):
            os.remove(self.constancia_fiscal_documento.path)
        if self.aviso_retencion_infonavit_documento and os.path.isfile(self.aviso_retencion_infonavit_documento.path):
            os.remove(self.aviso_retencion_infonavit_documento.path)
        if self.semanas_cotizadas_imss_documento and os.path.isfile(self.semanas_cotizadas_imss_documento.path):
            os.remove(self.semanas_cotizadas_imss_documento.path)
        super().delete(*args, **kwargs)

# --- NUEVO MODELO PARA HIJOS ---
class Hijo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='hijos')
    nombre = models.CharField(max_length=200)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Hijo/a de {self.empleado}: {self.nombre}"
    
    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        today = date.today()
        # Cálculo preciso de la edad
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

    class Meta:
        verbose_name = "Hijo"
        verbose_name_plural = "Hijos"
        ordering = ['fecha_nacimiento']

class Salario(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='salarios')
    sueldo_diario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_efectiva = models.DateField(help_text="Fecha a partir de la cual este salario es efectivo.")
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Salario"
        verbose_name_plural = "Salarios"
        ordering = ['-fecha_efectiva']

    @property
    def sueldo_semanal(self):
        if self.sueldo_diario is not None:
            return self.sueldo_diario * 7
        return None

    @property
    def sueldo_mensual(self):
        if self.sueldo_diario is not None:
            return self.sueldo_diario * 30
        return None

    def __str__(self):
        return f"Salario de {self.empleado} - ${self.sueldo_diario}/día desde {self.fecha_efectiva}"

# ... (El resto de los modelos permanece igual)
class TipoDocumentoOperador(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej. 'Licencia de Conducir', 'Certificado Médico'")
    descripcion = models.TextField(blank=True, null=True)
    requiere_fecha_vencimiento = models.BooleanField(default=False, help_text="Indica si este tipo de documento tiene una fecha de vencimiento.")

    class Meta:
        verbose_name = "Tipo de Documento de Operador"
        verbose_name_plural = "Tipos de Documentos de Operador"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class DocumentoOperador(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='documentos_operador')
    tipo_documento = models.ForeignKey(TipoDocumentoOperador, on_delete=models.PROTECT)
    archivo = models.FileField(upload_to=operador_documento_path)
    numero_documento = models.CharField(max_length=100, blank=True, null=True, help_text="Número de licencia, folio, etc.")
    fecha_expedicion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Documento de Operador"
        verbose_name_plural = "Documentos de Operador"
        unique_together = ('empleado', 'tipo_documento', 'numero_documento')
        ordering = ['empleado__apellido', 'empleado__nombre', 'tipo_documento__nombre']

    def delete(self, *args, **kwargs):
        if self.archivo and os.path.isfile(self.archivo.path):
            os.remove(self.archivo.path)
        super().delete(*args, **kwargs)

class HistorialLaboral(models.Model):
    EVENT_CHOICES = [
        ('CAMBIO_PUESTO', 'Cambio de Puesto'),
        ('SUSPENSION', 'Suspensión'),
        ('INCAPACIDAD', 'Incapacidad'),
        ('ACTA_ADMINISTRATIVA', 'Acta Administrativa'),
        ('PERMISO', 'Permiso'),
        ('RECONTRATACION', 'Re-contratación'),
        ('RENUNCIA', 'Renuncia'),
        ('BAJA', 'Baja'),
        ('ABANDONO', 'Abandono'),
    ]
    MOTIVO_SALIDA_CHOICES = [
        ('Renuncia', (
            ('AMBIENTE_LABORAL', 'Ambiente laboral'),
            ('LIDERAZGO_RENUNCIA', 'Liderazgo'),
            ('MOTIVOS_PERSONALES', 'Motivos personales'),
            ('PRESTACIONES', 'Prestaciones'),
        )),
        ('Baja', (
            ('RESICION_CONTRATO', 'Rescisión de Contrato'),
            ('FALTAS_REGLAMENTO', 'Faltas al Reglamento'),
            ('TERMINO_CONTRATO', 'Término de Contrato'),
            ('BAJO_RENDIMIENTO', 'Bajo Rendimiento'),
        )),
        ('Abandono', (
            ('FALTAS_INJUSTIFICADAS', 'Faltas injustificadas'),
            ('LIDERAZGO_ABANDONO', 'Liderazgo'),
            ('PAGO', 'Pago'),
        )),
    ]
    
    ESTATUS_CHOICES = [
        ('BUSCANDO', 'Buscando Reemplazo'),
        ('REMPLAZADO', 'Reemplazado'),
    ]
    MOTIVO_SALIDA_CHOICES_FLAT = [choice for group in MOTIVO_SALIDA_CHOICES for choice in group[1]]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='historial_laboral_eventos')
    tipo_evento = models.CharField(max_length=50, choices=EVENT_CHOICES, verbose_name="Tipo de Evento")
    fecha_inicio = models.DateField(verbose_name="Fecha del Evento / Inicio")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de Fin (si aplica)")
    puesto = models.CharField(max_length=100, blank=True, null=True, help_text="Nuevo puesto del empleado.")
    departamento = models.CharField(max_length=150, verbose_name="Departamento", blank=True, null=True)   
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción / Observaciones")
    motivo_salida = models.CharField(max_length=50, choices=MOTIVO_SALIDA_CHOICES, blank=True, null=True, help_text="Detallar el motivo si el evento es una Renuncia, Baja o Abandono.")
    documento_adjunto = models.FileField(upload_to=historial_documento_path, null=True, blank=True, verbose_name="Adjuntar Documento")

     # --- NUEVOS CAMPOS ---
    estatus = models.CharField(
        max_length=20,
        choices=ESTATUS_CHOICES,
        default='BUSCANDO',
        verbose_name="Estatus de la Vacante"
    )
    reemplazo = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reemplaza_a',
        help_text="Empleado que cubre esta vacante."
    )
    fecha_reemplazo = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Asignación del Reemplazo"
    )


    class Meta:
        verbose_name = "Evento de Historial Laboral"
        verbose_name_plural = "Eventos de Historial Laboral"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.get_tipo_evento_display()} para {self.empleado} el {self.fecha_inicio}"

    def delete(self, *args, **kwargs):
        if self.documento_adjunto and os.path.isfile(self.documento_adjunto.path):
            os.remove(self.documento_adjunto.path)
        super().delete(*args, **kwargs)

class Contrato(models.Model):
    TIPO_CONTRATO_CHOICES = [
        ('DETERMINADO', 'Determinado'),
        ('INDETERMINADO', 'Indeterminado'),
    ]
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='contratos')
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True, help_text="Requerido solo si el contrato es de tipo 'Determinado'")
    archivo_contrato = models.FileField(upload_to=contrato_documento_path, null=True, blank=True, verbose_name="Archivo del Contrato")
    comentarios = models.TextField(blank=True, null=True, verbose_name="Comentarios")

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Contrato {self.get_tipo_contrato_display()} para {self.empleado} desde {self.fecha_inicio}"

    def delete(self, *args, **kwargs):
        if self.archivo_contrato and os.path.isfile(self.archivo_contrato.path):
            os.remove(self.archivo_contrato.path)
        super().delete(*args, **kwargs)
        
    @property
    def duracion(self):
        if not self.fecha_fin:
            return "Indefinido"
        
        delta = self.fecha_fin - self.fecha_inicio
        years = delta.days // 365
        months = (delta.days % 365) // 30
        
        if years > 0:
            return f"{years} año(s)"
        elif months > 0:
            return f"{months} mes(es)"
        else:
            return f"{delta.days} día(s)"