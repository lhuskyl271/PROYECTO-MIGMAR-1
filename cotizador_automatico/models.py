from django.db import models
from decimal import Decimal
import math
from django.core.exceptions import ValidationError

class ParametrosGlobales(models.Model):
    precio_diesel = models.DecimalField(max_digits=6, decimal_places=2, default=24.50, verbose_name="Precio Diésel")
    costo_km_llantas = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Costo Llantas/KM")
    costo_km_mantenimiento = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Costo Mtto/KM")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuración del {self.fecha_actualizacion.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Parámetros Globales"
        verbose_name_plural = "Parámetros Globales"

class Unidad(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Eco / Unidad")
    rendimiento_cargado = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Rendimiento Cargado (km/l)")
    rendimiento_vacio = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Rendimiento Vacío (km/l)")
    
    # Costos Fijos
    costo_seguro_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    costo_gps_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    depreciacion_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    otros_fijos_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def costo_fijo_diario(self):
        total = self.costo_seguro_mensual + self.costo_gps_mensual + self.depreciacion_mensual + self.otros_fijos_mensual
        return total / Decimal(30)

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.nombre

class Cotizacion(models.Model):
    ESTATUS = (('BORRADOR', 'Borrador'), ('APROBADA', 'Aprobada'), ('RECHAZADA', 'Rechazada'))
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    
    # --- RUTA Y DISTANCIA ---
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    distancia_km_ida = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Distancia Ida (KM)")
    es_viaje_redondo = models.BooleanField(default=True)
    regreso_cargado = models.BooleanField(default=False)
    dias_viaje = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Días de Viaje")

    # --- VARIABLES LOGÍSTICAS AVANZADAS (NUEVO) ---
    peso_carga_toneladas = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Peso Carga (Ton)")
    # Se asume una capacidad estándar si no se especifica, útil para calcular % de carga
    capacidad_maxima_unidad = models.DecimalField(max_digits=5, decimal_places=2, default=25, verbose_name="Capacidad Max Unidad (Ton)")
    
    # Factor de dificultad (1.0 = Plano, 1.1 = Sierra leve, 1.3 = Sierra pesada)
    factor_terreno = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, verbose_name="Factor Terreno")
    
    # Tiempos muertos / Estadias
    horas_espera_carga = models.DecimalField(max_digits=4, decimal_places=2, default=0, verbose_name="Horas Espera Carga")
    horas_espera_descarga = models.DecimalField(max_digits=4, decimal_places=2, default=0, verbose_name="Horas Espera Descarga")
    costo_hora_demora = models.DecimalField(max_digits=8, decimal_places=2, default=500, verbose_name="Costo x Hora Demora")

    # --- GASTOS VARIABLES ADICIONALES ---
    costo_casetas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sueldo_operador = models.DecimalField(max_digits=10, decimal_places=2)
    viaticos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_maniobras = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # --- ESTRATEGIA ---
    margen_utilidad_deseado = models.DecimalField(max_digits=5, decimal_places=2, default=25.00, verbose_name="Margen (%)")
    estatus = models.CharField(max_length=20, choices=ESTATUS, default='BORRADOR')

    def calcular_rendimiento_ajustado(self):
        """
        Calcula el rendimiento real basado en el peso exacto de la carga
        y la dificultad del terreno.
        """
        rend_vacio = self.unidad.rendimiento_vacio
        rend_cargado = self.unidad.rendimiento_cargado
        
        if self.capacidad_maxima_unidad <= 0:
            return rend_cargado

        # 1. Interpolación por Peso
        # Porcentaje de carga (0.0 a 1.0)
        factor_carga = self.peso_carga_toneladas / self.capacidad_maxima_unidad
        if factor_carga > 1: factor_carga = Decimal(1.0) 
        
        # La diferencia de consumo entre vacío y lleno
        diferencia_rendimiento = rend_vacio - rend_cargado
        
        # Rendimiento base en terreno plano según peso
        rendimiento_por_peso = rend_vacio - (diferencia_rendimiento * factor_carga)
        
        # 2. Ajuste por Terreno
        # Si factor_terreno > 1 (sierra), el rendimiento disminuye (se divide)
        rendimiento_final = rendimiento_por_peso / self.factor_terreno
        
        return rendimiento_final

    def calcular_financieros(self):
        """
        Lógica central de costos y precios "Nivel Profesional"
        """
        try:
            params = ParametrosGlobales.objects.latest('fecha_actualizacion')
        except ParametrosGlobales.DoesNotExist:
            return None

        # 1. Distancia Total
        dist_total = self.distancia_km_ida * 2 if self.es_viaje_redondo else self.distancia_km_ida
        
        # 2. Diesel Inteligente (Ida con carga específica, regreso vacío o cargado)
        rendimiento_ida = self.calcular_rendimiento_ajustado()
        litros_ida = self.distancia_km_ida / rendimiento_ida
        
        litros_regreso = 0
        if self.es_viaje_redondo:
            if self.regreso_cargado:
                # Asumimos misma carga y terreno de regreso (o podrías parametrizarlo aparte)
                rend_regreso = rendimiento_ida 
            else:
                # Regreso vacío, pero afectado por el factor terreno
                rend_regreso = self.unidad.rendimiento_vacio / self.factor_terreno
            
            litros_regreso = self.distancia_km_ida / rend_regreso
        
        litros_totales = Decimal(litros_ida) + Decimal(litros_regreso)
        costo_diesel = litros_totales * params.precio_diesel

        # 3. Desgaste (Llantas + Mtto) afectado por Terreno
        # El terreno difícil daña más el camión
        factor_desgaste_base = params.costo_km_llantas + params.costo_km_mantenimiento
        costo_desgaste = (Decimal(dist_total) * factor_desgaste_base) * self.factor_terreno

        # 4. Fijos (Tiempo de Viaje)
        costo_fijos = self.unidad.costo_fijo_diario() * self.dias_viaje

        # 5. Costo por Demoras (NUEVO: El tiempo es dinero)
        total_horas_espera = self.horas_espera_carga + self.horas_espera_descarga
        costo_demoras = total_horas_espera * self.costo_hora_demora

        # 6. Costo Operativo Total (Directo)
        costo_total = (
            costo_diesel + 
            costo_desgaste + 
            costo_fijos + 
            self.costo_casetas + 
            self.sueldo_operador + 
            self.viaticos + 
            self.costo_maniobras +
            costo_demoras
        )

        # 7. Precio Venta y Márgenes
        factor_margen = 1 - (self.margen_utilidad_deseado / 100)
        if factor_margen <= 0: factor_margen = Decimal(0.01) # Protección contra división por cero
        
        subtotal_venta = costo_total / factor_margen
        iva = subtotal_venta * Decimal(0.16)
        retencion = subtotal_venta * Decimal(0.04)
        gran_total = subtotal_venta + iva - retencion

        # KPIs
        utilidad_monetaria = subtotal_venta - costo_total
        costo_por_km = costo_total / dist_total if dist_total > 0 else 0
        precio_por_km = subtotal_venta / dist_total if dist_total > 0 else 0

        return {
            'distancia_total': dist_total,
            'litros_totales': litros_totales,
            'rendimiento_promedio_viaje': dist_total / litros_totales if litros_totales > 0 else 0,
            
            # Desglose Costos
            'costo_diesel': costo_diesel,
            'costo_desgaste': costo_desgaste,
            'costo_fijos': costo_fijos,
            'costo_demoras': costo_demoras,
            'costo_operativo_total': costo_total,
            
            # Ventas
            'utilidad_monetaria': utilidad_monetaria,
            'subtotal_venta': subtotal_venta,
            'iva': iva,
            'retencion': retencion,
            'gran_total': gran_total,
            
            # KPIs
            'costo_por_km': costo_por_km,
            'precio_por_km': precio_por_km
        }