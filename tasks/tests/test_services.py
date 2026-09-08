"""
Capa de Dominio: tests de services.py (reglas de negocio puras).

Evalúan creación de tareas, transición de estados, excepciones de
dominio (ValueError / PermissionError) y autorización a nivel negocio.
NO simulan HTTP: llaman funciones Python con objetos del modelo.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from tasks import services
from tasks.models import Task

User = get_user_model()


class TaskCreateServiceTests(TestCase):
    """Reglas de creación de tareas."""

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

    def test_create_task_rejects_blank_title(self):
        with self.assertRaises(ValueError):
            services.create_task(user=self.ana, title='   ', due_date='2026-09-20')


class TaskStatusTransitionTests(TestCase):
    """Reglas de transición de estado (update_task_status)."""

    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='clave-123')
        self.beto = User.objects.create_user(username='beto', password='clave-123')
        self.task = services.create_task(
            user=self.ana,
            title='Revisar informe de notas',
            description='Pendiente de revisión',
            due_date='2026-09-25',
        )

    def test_update_task_status_marks_task_as_completed(self):
        """Regla de negocio: la transición actualiza el estado a COMPLETED."""
        result = services.update_task_status(
            task=self.task,
            new_status=Task.Status.COMPLETED,
            user=self.ana,
        )
        self.task.refresh_from_db()
        self.assertEqual(result.status, Task.Status.COMPLETED)
        self.assertEqual(self.task.status, Task.Status.COMPLETED)

    def test_update_task_status_accepts_any_valid_status(self):
        services.update_task_status(
            task=self.task,
            new_status=Task.Status.IN_PROGRESS,
            user=self.ana,
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.IN_PROGRESS)

    def test_update_task_status_raises_permission_error_for_foreign_task(self):
        """Regla de autorización en dominio: otro usuario no puede cambiarlo."""
        with self.assertRaises(PermissionError):
            services.update_task_status(
                task=self.task,
                new_status=Task.Status.COMPLETED,
                user=self.beto,
            )
        # La tarea no debe haber cambiado de estado.
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.PENDING)

    def test_update_task_status_rejects_invalid_status(self):
        """Estado no definido en Task.Status -> ValueError."""
        with self.assertRaises(ValueError):
            services.update_task_status(
                task=self.task,
                new_status='URGENTE',
                user=self.ana,
            )

    def test_mark_as_completed_delegates_to_update_task_status(self):
        result = services.mark_as_completed(self.task)
        self.task.refresh_from_db()
        self.assertEqual(result.status, Task.Status.COMPLETED)
        self.assertEqual(self.task.status, Task.Status.COMPLETED)
