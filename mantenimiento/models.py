# models.py (Completo y Modificado)

from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
import os # <-- Importante para las fotos

# Importamos el modelo Unidad de tu app 'flota'
# Asegúrate de que el nombre 'flota' coincida con tu app existente.
from flota.models import Unidad

# --- Catálogos Administrables ---

class CatalogoHerramienta(models.Model):
    """
    Un catálogo de herramientas que el Admin puede dar de alta.
    """
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre de Herramienta")
    
    def __str__(self):
        return self.nombre

class CatalogoMantenimientoCorrectivo(models.Model):
    """
    Un catálogo de tareas correctivas comunes que el Admin puede dar de alta.
    """
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre de Tarea Correctiva")
    descripcion = models.TextField(blank=True, verbose_name="Descripción (Opcional)")

    def __str__(self):
        return self.nombre

# --- Modelos Principales de Tareas ---

class TareaMantenimiento(models.Model):
    """
    La tarea principal asignada por un Admin a un Técnico.
    """
    # --- Choices para los campos ---
    TIPO_CHOICES = [
        ('PREVENTIVO', 'Mantenimiento Preventivo'),
        ('CORRECTIVO', 'Mantenimiento Correctivo'),
    ]
    
    # --- STATUS_CHOICES MODIFICADOS ---
    ESTADO_ASIGNADA = 'ASIGNADA'
    ESTADO_EN_PROCESO = 'EN_PROCESO'
    ESTADO_PENDIENTE_CIERRE = 'PENDIENTE_CIERRE' # <-- Modificado
    ESTADO_CERRADA = 'CERRADA'                 # <-- Nuevo
    ESTADO_CANCELADA = 'CANCELADA'
    
    STATUS_CHOICES = [
        (ESTADO_ASIGNADA, 'Asignada'),
        (ESTADO_EN_PROCESO, 'En Proceso'),
        (ESTADO_PENDIENTE_CIERRE, 'Pendiente de Cierre'), # <-- Modificado
        (ESTADO_CERRADA, 'Cerrada'),                 # <-- Nuevo
        (ESTADO_CANCELADA, 'Cancelada'),
    ]
    # --- FIN DE MODIFICACIÓN ---
    
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
    ]

    # --- Filtro para el campo 'tecnico' ---
    # Busca usuarios que pertenezcan al grupo 'Tecnico' O 'Supervisor'
    limit_tecnicos = Q(groups__name='Tecnico') | Q(groups__name='Supervisor')

    # --- Campos de Asignación ---
    admin = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='tareas_asignadas',
        verbose_name="Administrador"
    )
    tecnico = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='tareas_recibidas',
        verbose_name="Técnico Asignado",
        limit_choices_to=limit_tecnicos
    )
    unidad = models.ForeignKey(
        Unidad, 
        on_delete=models.PROTECT, 
        related_name='mantenimientos',
        verbose_name="Unidad"
    )

    # --- Campos de Tarea ---
    tipo_mantenimiento = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        verbose_name="Tipo de Mantenimiento"
    )
    mantenimiento_correctivo = models.ForeignKey(
        CatalogoMantenimientoCorrectivo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Tarea Correctiva Específica"
    )
    notas_admin = models.TextField(blank=True, verbose_name="Notas Adicionales (Admin)")

    prioridad = models.CharField(
        max_length=10, 
        choices=PRIORIDAD_CHOICES, 
        default='MEDIA',
        verbose_name="Prioridad"
    )

    # --- Campos de Estado y Tiempo ---
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=ESTADO_ASIGNADA, # <-- Modificado
        verbose_name="Estado"
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")
    fecha_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Inicio de Tarea")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fin de Tarea")
    tiempo_total_minutos = models.PositiveIntegerField(default=0, verbose_name="Duración Total (Minutos)")

    # --- Relación a Herramientas ---
    herramientas_solicitadas = models.ManyToManyField(
        CatalogoHerramienta,
        through='HerramientaSolicitada',
        related_name='tareas'
    )

    class Meta:
        ordering = ['-fecha_asignacion']
        verbose_name = "Tarea de Mantenimiento"
        verbose_name_plural = "Tareas de Mantenimiento"

    def __str__(self):
        return f"Tarea {self.id} ({self.get_tipo_mantenimiento_display()}) para {self.unidad.nombre}"

    def get_absolute_url(self):
        # URL para que el Admin vea el detalle
        return reverse('mantenimiento:admin_tarea_detalle', kwargs={'pk': self.pk})

    def get_tecnico_url(self):
        # URL para que el Técnico vea el detalle
        return reverse('mantenimiento:tecnico_tarea_detalle', kwargs={'pk': self.pk})

    def calcular_tiempo_total(self):
        """
        Calcula la diferencia entre fecha_fin y fecha_inicio en minutos.
        """
        if self.fecha_fin and self.fecha_inicio:
            diferencia = self.fecha_fin - self.fecha_inicio
            self.tiempo_total_minutos = int(diferencia.total_seconds() / 60)
        else:
            self.tiempo_total_minutos = 0


# --- CAMBIOS AQUÍ ---

def ruta_evidencia_subtask(instance, filename):
    """
    Genera la ruta de guardado para la foto de evidencia.
    Ej: media/mantenimiento/tarea_10/subtask_5_foto.jpg
    """
    tarea_id = instance.tarea_principal.id
    # Corregido: El ID de la subtarea puede no existir en la creación
    # Usaremos un hash o un nombre único si es necesario, pero para este flujo,
    # el nombre del archivo original suele ser suficiente para la función `upload_to`.
    # Sin embargo, la lógica en views.py la construye manualmente.
    # Esta función es llamada por `formset.save(commit=False)` y luego usada en la vista.
    # El ID puede ser None si es un objeto nuevo.
    # La vista `guardar_progreso_preventivo` parece construir la ruta manualmente,
    # pero usa esta función. Asegurémonos de que maneje `instance.id` como None.
    
    # Si la instancia ya tiene ID (ya fue guardada al menos una vez):
    if instance.id:
        subtask_id = instance.id
        filename = f"subtask_{subtask_id}{os.path.splitext(filename)[1]}"
    else:
        # Si es nueva, usamos el nombre original
        pass
        
    return f'mantenimiento/tarea_{tarea_id}/{filename}'


class TareaPreventivaSubtask(models.Model):
    """
    Almacena el estado de las sub-tareas fijas para un mantenimiento preventivo.
    """
    # --- LISTA ACTUALIZADA Y CORREGIDA ---
    # (Corregí los typos "suscepción" y "revisor")
    TAREAS_PREVENTIVAS_CHOICES = [
        # Categoría 1: Cambios (Agrupados bajo "Cambios")
        ('camb_filtro', 'Cambio de filtro (Aceite, combustible y aire)'),
        ('camb_anticong', 'Revisión de consistencia de anticongelante'),
        
        # Categoría 2: Revisión General
        ('gral_fusibles', 'Revisión, fusibles, relay'),
        ('gral_luces', 'Revisar luces'),
        ('gral_fugas_aire', 'Fugas de aire'),
        ('gral_llantas', 'Llantas (mm y psi)'),
        ('gral_fugas_aceite', 'Fugas de aceite'),
        
        # Categoría 3: Revisión Suspensión
        ('susp_amortiguadores', 'Amortiguadores'),
        ('susp_bolsa_aire', 'Bolsa de aire'),
        ('susp_bujes_muelle', 'Bujes de muelle'),
        ('susp_bujes_tirantes', 'Bujes de tirantes'),
        
        # Categoría 4: Revisión Dirección
        ('dir_vibracion', 'Revisión de vibración (prueba de pistón)'),
        ('dir_pernos', 'Revisión de pernos'),
    ]
    # --- FIN DE LA LISTA ---


    tarea_principal = models.ForeignKey(
        TareaMantenimiento, 
        on_delete=models.CASCADE, 
        related_name='subtasks_preventivas'
    )
    nombre_subtask = models.CharField(
        max_length=100, 
        choices=TAREAS_PREVENTIVAS_CHOICES,
        verbose_name="Sub-tarea"
    )
    
    completada = models.BooleanField(default=False, verbose_name="Completada")
    observaciones = models.TextField(
        blank=True, 
        verbose_name="Observaciones (ej: mm, psi, notas)"
    )
    
    # Esta ruta es la *default*, pero la vista `guardar_progreso_preventivo`
    # la sobreescribe con la lógica S3 manual.
    foto_evidencia = models.ImageField(
        upload_to='evidencias/', # <-- Ruta genérica
        null=True,   
        blank=True,  
        verbose_name="Foto de Evidencia"
    )


    class Meta:
        unique_together = ('tarea_principal', 'nombre_subtask') # Evita duplicados
        ordering = ['id']

    def __str__(self):
        return f"{self.get_nombre_subtask_display()} - {self.tarea_principal.id}"

class HerramientaSolicitada(models.Model):
    """
    Tabla intermedia que conecta Tareas con Herramientas.
    """
    tarea = models.ForeignKey(TareaMantenimiento, on_delete=models.CASCADE)
    herramienta = models.ForeignKey(CatalogoHerramienta, on_delete=models.PROTECT)
    # Puedes añadir cantidad si es necesario, por ahora lo omitimos por simplicidad.
    # cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('tarea', 'herramienta')

    def __str__(self):
        return f"{self.herramienta.nombre} para Tarea {self.tarea.id}"