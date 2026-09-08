"""
Capa de Persistencia: tests del modelo Task.

Evalúan el esquema (valores por defecto, __str__), la integridad
referencial y el QuerySet personalizado `for_user`. NO simulan HTTP:
crean objetos y consultan la base de datos directamente.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from tasks.models import Task

User = get_user_model()


class TaskModelTests(TestCase):
    """Esquema, valores por defecto y custom queryset for_user."""

    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='clave-123')
        self.beto = User.objects.create_user(username='beto', password='clave-123')
        self.task = Task.objects.create(
            title='Estudiar capas de Django',
            description='Modelo, vista, servicio y template',
            due_date='2026-09-15',
            user=self.ana,
        )

    def test_creation_defaults_to_pending_status(self):
        """Al crearse, una tarea nace con status='PENDING' por defecto."""
        self.assertEqual(self.task.status, Task.Status.PENDING)
        self.assertEqual(self.task.status, 'PENDING')

    def test_string_representation_uses_title(self):
        self.assertEqual(str(self.task), 'Estudiar capas de Django')

    def test_for_user_only_returns_own_tasks(self):
        """for_user(user) devuelve única y exclusivamente sus tareas."""
        Task.objects.create(
            title='Tarea de otro usuario',
            due_date='2026-09-16',
            user=self.beto,
        )
        tasks = Task.objects.for_user(self.ana)
        self.assertEqual(tasks.count(), 1)
        self.assertIn(self.task, tasks)

    def test_verbose_names_are_set(self):
        self.assertEqual(Task._meta.verbose_name, 'tarea')
        self.assertEqual(Task._meta.verbose_name_plural, 'tareas')

    # --- Rama dev (WIP): campo priority ---

    def test_priority_defaults_to_medium(self):
        self.assertEqual(self.task.priority, Task.Priority.MEDIUM)

    def test_priority_accepts_high_value(self):
        self.task.priority = Task.Priority.HIGH
        self.task.save(update_fields=['priority'])
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, Task.Priority.HIGH)
