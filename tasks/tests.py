"""
Tests de las capas del proyecto: persistencia (modelo), dominio
(servicios), validación (formularios) y control (vistas CBV).
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import services
from .forms import TaskForm
from .models import Task

User = get_user_model()


def future_date(days=3):
    """Fecha futura en formato ISO (evita depender de la fecha actual)."""
    return (date.today() + timedelta(days=days)).isoformat()


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

    def test_priority_defaults_to_medium(self):
        self.assertEqual(self.task.priority, Task.Priority.MEDIUM)

    def test_priority_accepts_high_value(self):
        self.task.priority = Task.Priority.HIGH
        self.task.save(update_fields=['priority'])
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, Task.Priority.HIGH)

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

    def test_create_task_stores_priority(self):
        task = services.create_task(
            user=self.ana,
            title='Tarea urgente',
            due_date='2026-09-21',
            priority=Task.Priority.HIGH,
        )
        self.assertEqual(task.priority, Task.Priority.HIGH)

    def test_create_task_defaults_priority_to_medium(self):
        task = services.create_task(
            user=self.ana,
            title='Tarea sin prioridad definida',
            due_date='2026-09-21',
        )
        self.assertEqual(task.priority, Task.Priority.MEDIUM)


class TaskFormTests(TestCase):
    """Pruebas de la capa de validación (forms.py)."""

    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='clave-123')

    def test_form_excludes_user_field(self):
        self.assertNotIn('user', TaskForm.base_fields)

    def test_form_includes_priority_field(self):
        self.assertIn('priority', TaskForm.base_fields)

    def test_form_is_valid_with_future_due_date(self):
        form = TaskForm(
            data={
                'title': 'Preparar evaluación',
                'description': '',
                'due_date': future_date(),
                'status': Task.Status.PENDING,
                'priority': Task.Priority.MEDIUM,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_rejects_past_due_date(self):
        past = (date.today() - timedelta(days=1)).isoformat()
        form = TaskForm(
            data={
                'title': 'Tarea con fecha vencida',
                'description': '',
                'due_date': past,
                'status': Task.Status.PENDING,
                'priority': Task.Priority.MEDIUM,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)
        self.assertIn('no puede ser anterior', form.errors['due_date'][0])


class TaskViewTests(TestCase):
    """Pruebas de la capa de control (views.py + urls.py)."""

    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='clave-123')
        self.beto = User.objects.create_user(username='beto', password='clave-123')
        self.ana_task = services.create_task(
            user=self.ana,
            title='Tarea de Ana',
            description='Visible solo para Ana',
            due_date=future_date(5),
        )
        services.create_task(
            user=self.beto,
            title='Tarea de Beto',
            description='No debe aparecerle a Ana',
            due_date=future_date(6),
        )

    # --- Protección de acceso (LoginRequiredMixin) ---

    def test_task_list_requires_login(self):
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_task_create_requires_login(self):
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_task_update_requires_login(self):
        response = self.client.get(reverse('task_update', args=[self.ana_task.pk]))
        self.assertEqual(response.status_code, 302)

    def test_task_delete_requires_login(self):
        response = self.client.get(reverse('task_delete', args=[self.ana_task.pk]))
        self.assertEqual(response.status_code, 302)

    # --- Aislamiento de datos por usuario ---

    def test_task_list_shows_only_logged_user_tasks(self):
        self.client.force_login(self.ana)
        response = self.client.get(reverse('task_list'))
        self.assertContains(response, 'Tarea de Ana')
        self.assertNotContains(response, 'Tarea de Beto')

    def test_user_cannot_update_other_users_task(self):
        self.client.force_login(self.beto)
        url = reverse('task_update', args=[self.ana_task.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_other_users_task(self):
        self.client.force_login(self.beto)
        url = reverse('task_delete', args=[self.ana_task.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    # --- Flujos CRUD ---

    def test_create_task_via_post(self):
        self.client.force_login(self.ana)
        data = {
            'title': 'Nueva tarea por POST',
            'description': 'Creada desde la vista',
            'due_date': future_date(2),
            'status': Task.Status.PENDING,
            'priority': Task.Priority.MEDIUM,
        }
        response = self.client.post(reverse('task_create'), data)
        self.assertRedirects(response, reverse('task_list'))
        self.assertTrue(
            Task.objects.filter(title='Nueva tarea por POST', user=self.ana).exists()
        )

    def test_create_task_rejects_past_due_date(self):
        self.client.force_login(self.ana)
        past = (date.today() - timedelta(days=1)).isoformat()
        data = {
            'title': 'Tarea inválida',
            'description': '',
            'due_date': past,
            'status': Task.Status.PENDING,
        }
        response = self.client.post(reverse('task_create'), data)
        self.assertEqual(response.status_code, 200)  # formulario re-renderizado
        self.assertContains(response, 'no puede ser anterior')
        self.assertFalse(Task.objects.filter(title='Tarea inválida').exists())

    def test_update_task_via_post(self):
        self.client.force_login(self.ana)
        data = {
            'title': 'Tarea de Ana (editada)',
            'description': 'Nueva descripción',
            'due_date': future_date(4),
            'status': Task.Status.COMPLETED,
            'priority': Task.Priority.HIGH,
        }
        response = self.client.post(
            reverse('task_update', args=[self.ana_task.pk]), data
        )
        self.assertRedirects(response, reverse('task_list'))
        self.ana_task.refresh_from_db()
        self.assertEqual(self.ana_task.title, 'Tarea de Ana (editada)')
        self.assertEqual(self.ana_task.status, Task.Status.COMPLETED)

    def test_delete_task_via_post(self):
        self.client.force_login(self.ana)
        response = self.client.post(
            reverse('task_delete', args=[self.ana_task.pk])
        )
        self.assertRedirects(response, reverse('task_list'))
        self.assertFalse(Task.objects.filter(pk=self.ana_task.pk).exists())
