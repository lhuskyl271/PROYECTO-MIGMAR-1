from django.contrib import admin
from .models import ParametrosGlobales, Unidad, Cliente, Cotizacion

admin.site.register(ParametrosGlobales)
admin.site.register(Unidad)
admin.site.register(Cliente)
admin.site.register(Cotizacion)