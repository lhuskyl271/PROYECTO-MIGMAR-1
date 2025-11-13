from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Q, F
from django.conf import settings # <-- ¡AÑADE ESTA LÍNEA!
# from flota.models import Unidad # Descomenta si quieres la relación

# --- Modelos de Soporte (Categorías y Proveedores) ---

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class SubCategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Sub-categoría"
        verbose_name_plural = "Sub-categorías"
        unique_together = ('categoria', 'nombre') 
        ordering = ['categoria__nombre', 'nombre']

    def __str__(self):
        return f"{self.categoria.nombre} - {self.nombre}"

# --- Modelos Principales del Inventario ---

class Articulo(models.Model):
    """
    Define el TIPO de artículo. Es la ficha técnica.
    No almacena cantidades ni precios aquí.
    """
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Artículo")
    subcategoria = models.ForeignKey(SubCategoria, on_delete=models.PROTECT, related_name='articulos', verbose_name="Sub-categoría")
    # --- CAMPOS ELIMINADOS DE AQUÍ ---
    # proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    # numero_proveedor = models.CharField(max_length=100, blank=True, verbose_name="Número de Proveedor")
    
    foto = models.ImageField(upload_to='almacen/fotos/', null=True, blank=True, verbose_name="Foto")
    stock_total = models.PositiveIntegerField(default=0, editable=False, verbose_name="Stock Disponible")

    class Meta:
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        # --- 'proveedor' ELIMINADO DE AQUÍ ---
        unique_together = ('nombre', 'subcategoria')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
    def actualizar_stock_total(self):
        """
        Calcula el stock real restando SALIDAS a las ENTRADAS.
        """
        # Sumar todas las entradas de tipo 'Stock'
        total_entradas = self.entradas.filter(tipo='Stock').aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        # ¡NUEVO! Sumar todas las salidas
        total_salidas = self.salidas.aggregate( # Usando related_name='salidas'
            total=Sum('cantidad')
        )['total'] or 0
        
        # Calcular el stock final
        self.stock_total = total_entradas - total_salidas
        
        # Guardamos sin llamar a las señales (signals) para evitar bucles
        super(Articulo, self).save(update_fields=['stock_total'])


class EntradaArticulo(models.Model):
    """
    Registra CADA compra (entrada) de un artículo.
    """
    TIPO_CHOICES = [
        ('Stock', 'Para Almacén (Stock)'),
        ('Unidad', 'Asignado a Unidad'),
    ]

    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='entradas')

    # --- CAMPOS AÑADIDOS AQUÍ (MOVIDOS DESDE Articulo) ---
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras', verbose_name="Proveedor")
    numero_proveedor = models.CharField(max_length=100, blank=True, verbose_name="Número de Proveedor (Factura/SKU)")
    # ----------------------------------------------------
    
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Compra (Unitario)")
    cantidad = models.PositiveIntegerField(default=1)
    fecha_compra = models.DateField(default=timezone.now, verbose_name="Fecha de Compra")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='Stock', verbose_name="Tipo de Entrada")
    
    # Opcional: Si es 'Unidad', puedes registrar a cuál
    # unidad_asignada = models.ForeignKey(Unidad, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Unidad Asignada")

    class Meta:
        verbose_name = "Entrada de Artículo"
        verbose_name_plural = "Entradas de Artículos"
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"{self.cantidad} x {self.articulo.nombre} @ ${self.precio_compra} ({self.tipo})"

# --- Señales (Signals) para la Lógica ---

        
class SalidaArticulo(models.Model):
    """
    Registra una salida de stock de un artículo.
    ...
    """
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT, related_name='salidas')
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(default=timezone.now)
    usuario_registra = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='salidas_registradas')

    # Enlace Genérico (La "causa" de la salida)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Salida de {self.cantidad} x {self.articulo.nombre}"
    
    class Meta:
        ordering = ['-fecha']
        
        
@receiver([post_save, post_delete], sender=EntradaArticulo)
@receiver([post_save, post_delete], sender=SalidaArticulo)
def actualizar_stock_on_change(sender, instance, **kwargs):
    """
    Cada vez que se guarda o elimina una Entrada (de tipo 'Stock')
    O CUALQUIER Salida, recalculamos el stock total del Artículo padre.
    """
    
    # Si es una Entrada, solo nos importa si es de tipo 'Stock'
    if sender == EntradaArticulo and instance.tipo != 'Stock':
        # Si la entrada NO es de 'Stock' (ej. 'Asignado a Unidad'),
        # no afecta el stock, así que no hacemos nada.
        # (Si la estás editando *desde* Stock, la señal de borrado lo maneja)
        pass
    else:
        # Si es una Salida, o una Entrada de 'Stock', actualizamos.
        instance.articulo.actualizar_stock_total()