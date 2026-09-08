"""
Tests de las capas de persistencia (modelo) y dominio (servicios).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from . import services
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


class TaskServiceTests(TestCase):
    """Pruebas de la capa de dominio (services.py)."""

    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='clave-123')

    def test_create_task_assigns_user_and_default_status(self):
        task = services.create_task(
            user=self.ana,
            title='  Preparar guía de laboratorio  ',
            description='Material para la clase',
            due_date='2026-09-20',
        )
        self.assertEqual(task.user, self.ana)
        self.assertEqual(task.title, 'Preparar guía de laboratorio')
        self.assertEqual(task.status, Task.Status.PENDING)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_create_task_rejects_blank_title(self):
        with self.assertRaises(ValueError):
            services.create_task(user=self.ana, title='   ', due_date='2026-09-20')

    def test_mark_as_completed_transitions_status(self):
        task = services.create_task(
            user=self.ana,
            title='Corregir evaluaciones',
            due_date='2026-09-22',
        )
        services.mark_as_completed(task)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.COMPLETED)

    def test_mark_as_completed_is_idempotent(self):
        task = services.create_task(
            user=self.ana,
            title='Publicar notas',
            due_date='2026-09-25',
            status=Task.Status.COMPLETED,
        )
        result = services.mark_as_completed(task)
        self.assertEqual(result.status, Task.Status.COMPLETED)
