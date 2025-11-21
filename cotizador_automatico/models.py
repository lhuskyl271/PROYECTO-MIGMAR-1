from django.db import models
from decimal import Decimal

class ParametrosGlobales(models.Model):
    precio_diesel = models.DecimalField(max_digits=6, decimal_places=2, default=24.50, verbose_name="Precio Diésel ($/L)")
    costo_km_llantas = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Factor Desgaste Llantas ($/Km)")
    costo_km_mantenimiento = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Reserva Mantenimiento ($/Km)")
    consumo_thermo_hora = models.DecimalField(max_digits=4, decimal_places=2, default=2.5, verbose_name="Consumo Thermo (Lts/Hora)")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parámetros vigentes al {self.fecha_actualizacion.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Parámetros Globales"
        verbose_name_plural = "Parámetros Globales"

class Unidad(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Eco / Unidad", help_text="Ej. Tracto T-800")
    
    # Rendimientos (Vital para la pestaña VARIOS del Excel)
    rendimiento_cargado = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Rendimiento Cargado (km/l)")
    rendimiento_vacio = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Rendimiento Vacío (km/l)")
    
    # Costos Fijos Detallados (Basado en pestaña 'camioneta local' y 'Dedicado')
    costo_seguro_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Seguro Mensual")
    costo_gps_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="GPS / Satelital")
    depreciacion_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Depreciación Mensual")
    otros_fijos_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Otros (Placas/Admin)")

    # Propiedad calculada (No se guarda en BD, se calcula al vuelo)
    @property
    def costo_fijo_mensual_total(self):
        return self.costo_seguro_mensual + self.costo_gps_mensual + self.depreciacion_mensual + self.otros_fijos_mensual

    def costo_fijo_diario(self):
        return self.costo_fijo_mensual_total / Decimal(30)

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Razón Social / Nombre")
    contacto = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.nombre

class Cotizacion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    
    # --- LOGÍSTICA DEL VIAJE ---
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    distancia_km_ida = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Distancia Ida (KM)")
    es_viaje_redondo = models.BooleanField(default=True, verbose_name="¿Cobrar Redondo?")
    dias_viaje = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Días de Operación")

    # --- LOGÍSTICA DE REFRIGERACIÓN (THERMO) ---
    es_refrigerado = models.BooleanField(default=False, verbose_name="¿Servicio Refrigerado?")
    horas_thermo_motor = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Horas Uso Thermo")

    # --- ESTRUCTURA DE COSTOS DIRECTOS (VARIABLES) ---
    sueldo_operador = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sueldo Operador")
    costo_casetas = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Casetas (Total)")
    viaticos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Viáticos / Comidas")
    costo_maniobras = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Maniobras / Cargas")

    # --- ESTRATEGIA COMERCIAL ---
    margen_utilidad_deseado = models.DecimalField(max_digits=5, decimal_places=2, default=25.00, verbose_name="Margen Objetivo (%)")

    def calcular_financieros(self):
        """
        Motor de cálculo financiero de alta precisión basado en hoja 'VARIOS.csv'.
        """
        try:
            params = ParametrosGlobales.objects.latest('fecha_actualizacion')
        except ParametrosGlobales.DoesNotExist:
            return None

        # 1. DETERMINACIÓN DE DISTANCIA
        # Si es redondo, duplicamos kms. Si es sencillo, solo ida.
        dist_total = self.distancia_km_ida * 2 if self.es_viaje_redondo else self.distancia_km_ida
        
        # 2. CÁLCULO DE COMBUSTIBLE TRACTO (MOTRIZ)
        # Promedio simple de rendimiento si es redondo (ida cargado / vuelta vacía o cargada)
        if self.es_viaje_redondo:
            rendimiento_promedio = (self.unidad.rendimiento_cargado + self.unidad.rendimiento_vacio) / 2
        else:
            rendimiento_promedio = self.unidad.rendimiento_cargado
            
        litros_tracto = dist_total / rendimiento_promedio
        costo_diesel_tracto = litros_tracto * params.precio_diesel

        # 3. CÁLCULO DE COMBUSTIBLE THERMO (REFRIGERACIÓN)
        # Fórmula: Horas Encendido * Consumo/Hora * Precio Diesel
        litros_thermo = Decimal(0)
        costo_diesel_thermo = Decimal(0)
        
        if self.es_refrigerado:
            litros_thermo = self.horas_thermo_motor * params.consumo_thermo_hora
            costo_diesel_thermo = litros_thermo * params.precio_diesel

        # 4. COSTOS DE DESGASTE OPERATIVO (LLANTAS Y MTTO)
        # Fórmula: Kms Recorridos * (Factor Llantas + Factor Mtto)
        factor_desgaste = params.costo_km_llantas + params.costo_km_mantenimiento
        costo_desgaste = Decimal(dist_total) * factor_desgaste

        # 5. PRORRATEO DE COSTOS FIJOS
        # Fórmula: (Costo Mensual Unidad / 30 días) * Días de Viaje
        costo_fijos_viaje = self.unidad.costo_fijo_diario() * self.dias_viaje

        # 6. INTEGRACIÓN DEL COSTO TOTAL (COSTO DE VENTA)
        costo_total_operativo = (
            costo_diesel_tracto + 
            costo_diesel_thermo +
            costo_desgaste + 
            costo_fijos_viaje + 
            self.costo_casetas + 
            self.sueldo_operador + 
            self.viaticos + 
            self.costo_maniobras
        )

        # 7. DETERMINACIÓN DE PRECIO Y KPIs
        # Precio Venta = Costo Total / (1 - %Margen)
        # Esto asegura que el margen sea sobre la VENTA, no sobre el costo (Markup vs Margin)
        factor_margen = 1 - (self.margen_utilidad_deseado / 100)
        if factor_margen <= 0: factor_margen = Decimal("0.01") # Evitar división por cero
        
        subtotal_venta = costo_total_operativo / factor_margen
        utilidad_monetaria = subtotal_venta - costo_total_operativo
        
        iva = subtotal_venta * Decimal("0.16")
        retencion = subtotal_venta * Decimal("0.04")
        gran_total_factura = subtotal_venta + iva - retencion

        return {
            'kpis': {
                'distancia_total': dist_total,
                'litros_totales': litros_tracto + litros_thermo,
                'costo_por_km': costo_total_operativo / dist_total if dist_total > 0 else 0,
                'precio_por_km': subtotal_venta / dist_total if dist_total > 0 else 0,
            },
            'desglose': {
                'diesel_tracto': costo_diesel_tracto,
                'diesel_thermo': costo_diesel_thermo,
                'desgaste_unidad': costo_desgaste,
                'fijos_prorrateados': costo_fijos_viaje,
                'sueldo': self.sueldo_operador,
                'casetas': self.costo_casetas,
                'gastos_viaje': self.viaticos + self.costo_maniobras
            },
            'financiero': {
                'costo_total': costo_total_operativo,
                'subtotal_venta': subtotal_venta,
                'utilidad': utilidad_monetaria,
                'iva': iva,
                'retencion': retencion,
                'gran_total': gran_total_factura
            }
        }