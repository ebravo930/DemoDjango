"""
Capa de Control: tests de las vistas CBV (tasks/views.py + urls).

Evalúan control de acceso (login required), redirecciones, códigos HTTP,
aislamiento de información entre usuarios y flujos CRUD. SÍ requieren
simular HTTP mediante self.client (GET/POST).
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tasks import services
from tasks.models import Task

User = get_user_model()


def future_date(days=3):
    """Fecha futura en formato ISO (independiente de la fecha actual)."""
    return (date.today() + timedelta(days=days)).isoformat()


class TaskViewTests(TestCase):
    """Control de acceso, aislamiento de datos y flujos CRUD."""

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

    # --- Protección de rutas (LoginRequiredMixin) ---

    def test_task_list_requires_login(self):
        """Usuarios anónimos son redirigidos a /accounts/login/."""
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
        self.assertIn('/accounts/login/', response.url)

    def test_task_delete_requires_login(self):
        response = self.client.get(reverse('task_delete', args=[self.ana_task.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    # --- Aislamiento de información ---

    def test_task_list_shows_only_logged_user_tasks(self):
        """El HTML/contexto de la lista no incluye tareas de otros usuarios."""
        self.client.force_login(self.ana)
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tarea de Ana')
        self.assertNotContains(response, 'Tarea de Beto')

    def test_user_cannot_update_other_users_task(self):
        self.client.force_login(self.beto)
        response = self.client.get(reverse('task_update', args=[self.ana_task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_other_users_task(self):
        self.client.force_login(self.beto)
        url = reverse('task_delete', args=[self.ana_task.pk])
        self.assertEqual(self.client.post(url).status_code, 404)

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
        past_date = (date.today() - timedelta(days=1)).isoformat()
        data = {
            'title': 'Tarea inválida',
            'description': '',
            'due_date': past_date,
            'status': Task.Status.PENDING,
        }
        response = self.client.post(reverse('task_create'), data)
        self.assertEqual(response.status_code, 200)  # formulario re-renderizado
        self.assertContains(response, 'no puede ser anterior')
        self.assertFalse(Task.objects.filter(title='Tarea inválida').exists())

    def test_update_form_loads_with_initial_values(self):
        """Flujo de edición: TaskUpdateView responde 200 con los valores cargados."""
        self.client.force_login(self.ana)
        response = self.client.get(reverse('task_update', args=[self.ana_task.pk]))
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.instance.pk, self.ana_task.pk)
        self.assertEqual(form['title'].value(), 'Tarea de Ana')
        self.assertContains(response, 'Tarea de Ana')

    def test_update_task_via_post_persists_changes(self):
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
        response = self.client.post(reverse('task_delete', args=[self.ana_task.pk]))
        self.assertRedirects(response, reverse('task_list'))
        self.assertFalse(Task.objects.filter(pk=self.ana_task.pk).exists())
