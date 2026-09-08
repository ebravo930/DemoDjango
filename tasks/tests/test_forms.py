"""
Capa de Validación: tests de forms.py.

Evalúan sanitización de inputs, formato de fecha ISO (YYYY-MM-DD),
reglas de clean_due_date y el render del widget date. NO simulan HTTP.
"""
from datetime import date, timedelta

from django.test import TestCase

from tasks.forms import TaskForm
from tasks.models import Task


class TaskFormTests(TestCase):
    """Validación de entradas del usuario en TaskForm."""

    def test_form_excludes_user_field(self):
        """`user` no es un campo de formulario: lo asigna la capa de servicio."""
        self.assertNotIn('user', TaskForm.base_fields)

    def test_form_accepts_iso_date_format(self):
        """Una fecha en formato ISO YYYY-MM-DD es aceptada como válida."""
        iso_date = (date.today() + timedelta(days=5)).isoformat()
        form = TaskForm(
            data={
                'title': 'Preparar evaluación',
                'description': '',
                'due_date': iso_date,
                'status': Task.Status.PENDING,
                'priority': Task.Priority.MEDIUM,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['due_date'], date.fromisoformat(iso_date))

    def test_form_rejects_past_due_date(self):
        """clean_due_date: fecha anterior a hoy -> error en el campo due_date."""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        form = TaskForm(
            data={
                'title': 'Tarea con fecha vencida',
                'description': '',
                'due_date': past_date,
                'status': Task.Status.PENDING,
                'priority': Task.Priority.MEDIUM,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)
        self.assertIn('no puede ser anterior', form.errors['due_date'][0])

    def test_due_date_widget_renders_html_date_input(self):
        """El widget renderiza type="date": el navegador exige ISO YYYY-MM-DD."""
        form = TaskForm()
        rendered = str(form['due_date'])
        self.assertIn('type="date"', rendered)
        self.assertIn('name="due_date"', rendered)
