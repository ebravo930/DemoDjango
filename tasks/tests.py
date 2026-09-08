"""
Tests de la capa de persistencia (modelo Task y QuerySet for_user).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Task

User = get_user_model()


class TaskModelTests(TestCase):
    """Pruebas del modelo Task y su QuerySet personalizado."""

    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='clave-123')
        self.beto = User.objects.create_user(username='beto', password='clave-123')
        self.task = Task.objects.create(
            title='Estudiar capas de Django',
            description='Modelo, vista, servicio y template',
            due_date='2026-09-15',
            user=self.ana,
        )

    def test_string_representation_uses_title(self):
        self.assertEqual(str(self.task), 'Estudiar capas de Django')

    def test_status_defaults_to_pending(self):
        self.assertEqual(self.task.status, Task.Status.PENDING)

    def test_for_user_only_returns_own_tasks(self):
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
