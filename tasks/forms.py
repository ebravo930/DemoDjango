"""
Capa de validación: sanitización de datos e inputs del usuario.

Los formularios convierten el POST crudo en datos limpios y concentran
las reglas de validación específicas (por ejemplo, clean_due_date).
"""
from datetime import date

from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    """Formulario de tareas con widgets Bootstrap 5."""

    class Meta:
        model = Task
        # `user` NO está en el formulario: lo asigna la capa de servicio.
        fields = ['title', 'description', 'due_date', 'status', 'priority']
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej.: Preparar clase de Django',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Detalle opcional de la tarea...',
                }
            ),
            'due_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_due_date(self):
        """Regla de validación: la fecha de vencimiento no puede ser pasada."""
        due_date = self.cleaned_data.get('due_date')

        if due_date and due_date < date.today():
            raise forms.ValidationError(
                'La fecha de vencimiento no puede ser anterior a hoy.'
            )
        return due_date
