# almacen/models.py
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

# ... (Modelos Proveedor, Categoria, SubCategoria se quedan igual) ...

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
    Define el TIPO de artículo.
    AHORA INCLUYE PRECIO DE REFERENCIA.
    """
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Artículo")
    subcategoria = models.ForeignKey(SubCategoria, on_delete=models.PROTECT, related_name='articulos', verbose_name="Sub-categoría")
    foto = models.ImageField(upload_to='almacen/fotos/', null=True, blank=True, verbose_name="Foto")
    stock_total = models.PositiveIntegerField(default=0, editable=False, verbose_name="Stock Disponible")
    
    # --- NUEVO CAMPO DE PRECIO ---
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Precio Unitario (Ref)"
    )

    class Meta:
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        unique_together = ('nombre', 'subcategoria')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
    def actualizar_stock_total(self):
        """
        Calcula el stock real Y EL ÚLTIMO PRECIO DE COMPRA.
        """
        # 1. Calcular Stock (Entradas - Salidas)
        total_entradas = self.entradas.filter(tipo='Stock').aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        total_salidas = self.salidas.aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        self.stock_total = total_entradas - total_salidas

        # 2. Actualizar Precio (Basado en la última compra registrada)
        ultima_entrada = self.entradas.order_by('-fecha_compra', '-id').first()
        if ultima_entrada:
            self.precio = ultima_entrada.precio_compra
        
        # Guardamos stock y precio
        super(Articulo, self).save(update_fields=['stock_total', 'precio'])


class EntradaArticulo(models.Model):
    """
    Registra CADA compra (entrada) de un artículo.
    """
    TIPO_CHOICES = [
        ('Stock', 'Para Almacén (Stock)'),
        ('Unidad', 'Asignado a Unidad'),
    ]

    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='entradas')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras', verbose_name="Proveedor")
    numero_proveedor = models.CharField(max_length=100, blank=True, verbose_name="Número de Proveedor (Factura/SKU)")
    
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Compra (Unitario)")
    cantidad = models.PositiveIntegerField(default=1)
    fecha_compra = models.DateField(default=timezone.now, verbose_name="Fecha de Compra")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='Stock', verbose_name="Tipo de Entrada")

    class Meta:
        verbose_name = "Entrada de Artículo"
        verbose_name_plural = "Entradas de Artículos"
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"{self.cantidad} x {self.articulo.nombre} @ ${self.precio_compra} ({self.tipo})"

        
class SalidaArticulo(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT, related_name='salidas')
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(default=timezone.now)
    usuario_registra = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='salidas_registradas')

    # Enlace Genérico
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Salida de {self.cantidad} x {self.articulo.nombre}"
    
    class Meta:
        ordering = ['-fecha']
        

# --- SEÑALES ---
@receiver([post_save, post_delete], sender=EntradaArticulo)
@receiver([post_save, post_delete], sender=SalidaArticulo)
def actualizar_stock_on_change(sender, instance, **kwargs):
    """
    Recalcula stock y precio al guardar/borrar entradas o salidas.
    """
    if sender == EntradaArticulo and instance.tipo != 'Stock':
        # Si la entrada NO es stock (va directo a unidad), 
        # igual actualizamos el precio si es la ultima compra, 
        # así que llamamos a actualizar_stock_total de todos modos.
        instance.articulo.actualizar_stock_total()
    else:
        instance.articulo.actualizar_stock_total()