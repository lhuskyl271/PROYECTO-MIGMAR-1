# RH/forms.py
from django import forms
from django.db.models import Q
from django.forms import ModelForm
from .models import (
    Empleado, Departamento, Puesto, MotivoInactivacion,
    TipoDocumentoOperador, DocumentoOperador, HistorialLaboral,
    Salario, Contrato, DivisionOperativa, TipoCarga, TipoViaje,
    Hijo
)

class EmpleadoForm(ModelForm):
    # Hacer los campos no requeridos por defecto.
    tipo_carga = forms.ModelMultipleChoiceField(
        queryset=TipoCarga.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False, 
        label="Tipo de Carga"
    )
    tipo_viaje = forms.ModelMultipleChoiceField(
        queryset=TipoViaje.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tipo de Viaje"
    )
    division_operativa = forms.ModelMultipleChoiceField(
        queryset=DivisionOperativa.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="División Operativa"
    )

    class Meta:
        model = Empleado
        fields = '__all__'
        widgets = {
            'numero_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            # Puesto y Depto se configuran como Select en el __init__
            'puesto': forms.Select(attrs={'class': 'form-select'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'fecha_contratacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_activo_toggle'}),
            'motivo_inactivacion': forms.Select(attrs={'class': 'form-select', 'id': 'id_motivo_inactivacion'}),
            'fecha_inactivacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_fecha_inactivacion'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle y Número Ext/Int'}),
            'colonia': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'nombre_conyuge': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_conyuge': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+521234567890'}),
            'telefono_personal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+521234567890'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control'}),
            'curp': forms.TextInput(attrs={'class': 'form-control'}),
            'rfc': forms.TextInput(attrs={'class': 'form-control'}),
            'nss': forms.TextInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'clabe_interbancaria': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_tarjeta': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_referencia_1': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_referencia_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+521234567890'}),
            'relacion_referencia_1': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_referencia_2': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_referencia_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+521234567890'}),
            'relacion_referencia_2': forms.TextInput(attrs={'class': 'form-control'}),
            'ine_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'comprobante_domicilio': forms.FileInput(attrs={'class': 'form-control'}),
            'curriculum_vitae': forms.FileInput(attrs={'class': 'form-control'}),
            'acta_nacimiento_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'comprobante_estudios_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'carta_recomendacion_1_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'carta_recomendacion_2_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'constancia_fiscal_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'aviso_retencion_infonavit_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'semanas_cotizadas_imss_documento': forms.FileInput(attrs={'class': 'form-control'}),
            'empresa': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'numero_empleado': 'Número de Empleado Interno',
            'nombre_conyuge': 'Nombre del Cónyuge o Pareja',
            'numero_tarjeta': 'Número de Tarjeta (16 dígitos)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. ARREGLO DE DROPDOWNS (Puesto y Departamento)
        # Como ahora son texto en la BD, cargamos las opciones manualmente para que el usuario vea una lista
        puestos_disponibles = Puesto.objects.all().order_by('nombre')
        choices_puestos = [(p.nombre, p.nombre) for p in puestos_disponibles]
        choices_puestos.insert(0, ('', '---------'))
        self.fields['puesto'].widget = forms.Select(attrs={'class': 'form-select'}, choices=choices_puestos)

        deptos_disponibles = Departamento.objects.all().order_by('nombre')
        choices_deptos = [(d.nombre, d.nombre) for d in deptos_disponibles]
        choices_deptos.insert(0, ('', '---------'))
        self.fields['departamento'].widget = forms.Select(attrs={'class': 'form-select'}, choices=choices_deptos)

        # 2. ARREGLO DEL ERROR DE FILTRO (Supervisor)
        # Cambiamos 'puesto__nombre__icontains' -> 'puesto__icontains' (búsqueda directa en texto)
        supervisor_query = Q(puesto__icontains='Supervisor') | Q(puesto__icontains='Gerente')
        
        potential_supervisors = Empleado.objects.filter(supervisor_query).order_by('apellido', 'nombre')

        if self.instance and self.instance.pk:
            self.fields['supervisor'].queryset = potential_supervisors.exclude(pk=self.instance.pk)
        else:
            self.fields['supervisor'].queryset = potential_supervisors
        
        # Etiqueta personalizada para el supervisor
        self.fields['supervisor'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido}"

        # 3. CAMPOS NO REQUERIDOS
        for field_name, field in self.fields.items():
            field.required = False
            widget_attrs = field.widget.attrs
            if 'class' in widget_attrs:
                widget_attrs['class'] = widget_attrs['class'].replace('is-required', '')
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = Empleado.objects.filter(email=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Este correo electrónico ya está asignado a otro empleado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data



class HijoForm(forms.ModelForm):
    class Meta:
        model = Hijo
        fields = ['nombre', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # --- NUEVO: Hacer todos los campos no obligatorios ---
        for field_name, field in self.fields.items():
            field.required = False


class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nombre': 'Nombre del Departamento',
            'descripcion': 'Descripción',
        }

class PuestoForm(forms.ModelForm):
    class Meta:
        model = Puesto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salario_base': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre del Puesto',
            'descripcion': 'Descripción',
            'salario_base': 'Salario Base',
        }

class MotivoInactivacionForm(forms.ModelForm):
    class Meta:
        model = MotivoInactivacion
        fields = '__all__'
        widgets = {
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'motivo': 'Motivo de Inactivación',
            'descripcion': 'Descripción del Motivo',
        }

class TipoDocumentoOperadorForm(forms.ModelForm):
    class Meta:
        model = TipoDocumentoOperador
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requiere_fecha_vencimiento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre del Tipo de Documento',
            'descripcion': 'Descripción',
            'requiere_fecha_vencimiento': '¿Requiere Fecha de Vencimiento?',
        }

class DocumentoOperadorForm(forms.ModelForm):
    class Meta:
        model = DocumentoOperador
        fields = ['tipo_documento', 'archivo', 'numero_documento', 'fecha_expedicion', 'fecha_vencimiento', 'observaciones']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select document-type-select'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_expedicion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control expiry-date-field'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # --- NUEVO: Hacer todos los campos no obligatorios ---
        for field_name, field in self.fields.items():
            field.required = False
            
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_documento')
        archivo = cleaned_data.get('archivo')
        # Verificamos si escribió algo en la fila
        has_data = tipo or archivo or cleaned_data.get('numero_documento')

        if has_data:
            if not tipo:
                self.add_error('tipo_documento', 'El tipo de documento es obligatorio.')
            # Dependiendo de tu lógica, el archivo podría ser obligatorio o no.
            # Si es obligatorio en la BD, descomenta la siguiente línea:
            # if not archivo and not self.instance.pk: # Solo si es nuevo
            #     self.add_error('archivo', 'Debes subir el archivo.')

        return cleaned_data

class SalarioForm(forms.ModelForm):
    class Meta:
        model = Salario
        fields = ['sueldo_diario', 'fecha_efectiva', 'observaciones']
        widgets = {
            'sueldo_diario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_efectiva': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mantienes tu lógica de hacerlos opcionales visualmente
        for field_name, field in self.fields.items():
            field.required = False

    # --- AGREGAR ESTA VALIDACIÓN ---
    def clean(self):
        cleaned_data = super().clean()
        sueldo = cleaned_data.get('sueldo_diario')
        fecha = cleaned_data.get('fecha_efectiva')
        observaciones = cleaned_data.get('observaciones')

        # Lógica: Si se llenó ALGUN campo, los obligatorios deben estar presentes.
        # Si todos están vacíos, se asume que no se quiere guardar nada en esta fila.
        has_data = sueldo or fecha or observaciones

        if has_data:
            if not sueldo:
                self.add_error('sueldo_diario', 'Este campo es obligatorio al registrar un salario.')
            if not fecha:
                self.add_error('fecha_efectiva', 'La fecha efectiva es obligatoria.')

        return cleaned_data

class HistorialLaboralForm(forms.ModelForm):
    class Meta:
        model = HistorialLaboral
        fields = ['tipo_evento', 'fecha_inicio', 'fecha_fin', 'puesto', 'departamento', 'descripcion', 'motivo_salida', 'documento_adjunto']
        widgets = {
            'tipo_evento': forms.Select(attrs={'class': 'form-select history-event-type'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'motivo_salida': forms.Select(attrs={'class': 'form-select history-reason-select'}),
            'documento_adjunto': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # --- NUEVO: Hacer todos los campos no obligatorios ---
        for field_name, field in self.fields.items():
            field.required = False
            
            
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_evento')
        fecha = cleaned_data.get('fecha_inicio')
        # Verificar si hay algún dato ingresado en los campos principales
        has_data = tipo or fecha or cleaned_data.get('puesto') or cleaned_data.get('descripcion')

        if has_data:
            if not tipo:
                self.add_error('tipo_evento', 'El tipo de evento es obligatorio.')
            if not fecha:
                self.add_error('fecha_inicio', 'La fecha de inicio es obligatoria.')
        
        return cleaned_data

class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['tipo_contrato', 'fecha_inicio', 'fecha_fin', 'archivo_contrato', 'comentarios']
        widgets = {
            'tipo_contrato': forms.Select(attrs={'class': 'form-select contract-type-select'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control contract-end-date'}),
            'archivo_contrato': forms.FileInput(attrs={'class': 'form-control'}),
            'comentarios': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # --- NUEVO: Hacer todos los campos no obligatorios ---
        for field_name, field in self.fields.items():
            field.required = False
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_contrato')
        fecha = cleaned_data.get('fecha_inicio')
        archivo = cleaned_data.get('archivo_contrato')
        comentarios = cleaned_data.get('comentarios')

        # Si hay algún dato en la fila
        has_data = tipo or fecha or archivo or comentarios

        if has_data:
            if not tipo:
                self.add_error('tipo_contrato', 'El tipo de contrato es obligatorio.')
            if not fecha:
                self.add_error('fecha_inicio', 'La fecha de inicio es obligatoria.')
        
        return cleaned_data