# forms.py (Modificado para Pruebas)

from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .models import (
    TareaMantenimiento, CatalogoHerramienta, 
    CatalogoMantenimientoCorrectivo, TareaPreventivaSubtask
)

class CatalogoHerramientaForm(forms.ModelForm):
    class Meta:
        model = CatalogoHerramienta
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CatalogoMantenimientoCorrectivoForm(forms.ModelForm):
    class Meta:
        model = CatalogoMantenimientoCorrectivo
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AsignarTareaForm(forms.ModelForm):
    tecnico = forms.ModelChoiceField(
        queryset=User.objects.filter(
            Q(groups__name='Tecnico') | Q(groups__name='Supervisor')
        ).distinct().order_by('username'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Técnico Asignado"
    )

    class Meta:
        model = TareaMantenimiento
        fields = [
            'tecnico', 'unidad', 'tipo_mantenimiento', 
            'prioridad', 
            'mantenimiento_correctivo', 'notas_admin'
        ]
        widgets = {
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'tipo_mantenimiento': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}), 
            'mantenimiento_correctivo': forms.Select(attrs={'class': 'form-select'}),
            'notas_admin': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mantenimiento_correctivo'].required = False
        self.fields['unidad'].widget.attrs.update({'class': 'form-select select2-widget-unidad'})

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_mantenimiento')
        correctivo = cleaned_data.get('mantenimiento_correctivo')

        if tipo == 'CORRECTIVO' and not correctivo:
            self.add_error('mantenimiento_correctivo', 
                           'Debe seleccionar una tarea específica para el mantenimiento correctivo.')
        
        return cleaned_data
class SeleccionarHerramientasForm(forms.Form):
    herramientas = forms.ModelMultipleChoiceField(
        queryset=CatalogoHerramienta.objects.all().order_by('nombre'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'id': 'select2-herramientas'}),
        required=True,
        label="Seleccionar Herramientas Requeridas"
    )
    
    def __init__(self, *args, **kwargs):
        self.tarea = kwargs.pop('tarea', None)
        super().__init__(*args, **kwargs)
        
        if self.tarea:
            self.fields['herramientas'].initial = self.tarea.herramientas_solicitadas.all()


# --- ESTA CLASE FUE MODIFICADA ---

class TareaPreventivaSubtaskForm(forms.ModelForm):
    completada = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input me-2'}))
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Notas, mm, psi...'})
    )
    
    foto_evidencia = forms.ImageField(
        required=False, 
        widget=forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'})
    )

    # Lista de tareas que requieren foto
    TAREAS_SUSPENSION = [
        'susp_amortiguadores', 
        'susp_bolsa_aire', 
        'susp_bujes_muelle', 
        'susp_bujes_tirantes'
    ]

    class Meta:
        model = TareaPreventivaSubtask
        fields = ['completada', 'observaciones', 'foto_evidencia']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['completada'].label = self.instance.get_nombre_subtask_display()

            if self.instance.nombre_subtask in self.TAREAS_SUSPENSION:
                # Mantenemos la etiqueta para que el usuario sepa que la necesitará
                self.fields['foto_evidencia'].label = "Foto de Evidencia (Requerida al completar)"
            

    # --- MÉTODO CLEAN MODIFICADO PARA PRUEBAS ---
    def clean(self):
        cleaned_data = super().clean()
        
        # --- VALIDACIÓN DESACTIVADA PARA PRUEBAS ---
        
        # completada = cleaned_data.get('completada')
        # foto_subida_ahora = cleaned_data.get('foto_evidencia') 
        # foto_existente = self.instance.foto_evidencia 
        # es_tarea_suspension = self.instance.nombre_subtask in self.TAREAS_SUSPENSION
        #
        # if completada and es_tarea_suspension:
        #     if not foto_subida_ahora and not foto_existente:
        #         self.add_error('foto_evidencia', 'Debe subir una foto de evidencia para completar esta tarea de suspensión.')
        
        # --- FIN DE DESACTIVACIÓN ---
        
        return cleaned_data


# Creamos un FormSet para el checklist preventivo
TareaPreventivaFormSet = forms.inlineformset_factory(
    TareaMantenimiento,
    TareaPreventivaSubtask,
    form=TareaPreventivaSubtaskForm,
    fields=('completada', 'observaciones', 'foto_evidencia'),
    extra=0, 
    can_delete=False
)