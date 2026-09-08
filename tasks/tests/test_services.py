"""
Capa de Dominio: tests de services.py (reglas de negocio puras).

Evalúan creación de tareas, transición de estados, excepciones de
dominio (ValueError / PermissionError) y autorización a nivel negocio.
NO simulan HTTP: llaman funciones Python con objetos del modelo.
"""
import requests
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from tasks import services, supabase_client
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


class TaskSupabaseAuditTests(TestCase):
    """Rama dev: los servicios despachan auditoría externa a Supabase.

    Se usa unittest.mock.patch para NO realizar llamadas reales a
    internet: se verifica que el cliente sea invocado con los
    parámetros correctos y que el servicio siga operando sin red.
    """

    def setUp(self):
        self.ana = User.objects.create_user(username='ana', password='clave-123')

    @mock.patch('tasks.supabase_client.log_task_event_to_supabase')
    def test_create_task_dispatches_created_event(self, mock_log):
        task = services.create_task(
            user=self.ana,
            title='Tarea auditada',
            due_date='2026-10-01',
        )
        mock_log.assert_called_once_with(
            task.pk, 'Tarea auditada', 'CREATED', 'ana'
        )

    @mock.patch('tasks.supabase_client.log_task_event_to_supabase')
    def test_update_task_status_dispatches_status_changed_event(self, mock_log):
        task = services.create_task(
            user=self.ana,
            title='Tarea auditada',
            due_date='2026-10-01',
        )
        services.update_task_status(
            task=task,
            new_status=Task.Status.COMPLETED,
            user=self.ana,
        )
        mock_log.assert_called_with(
            task.pk, 'Tarea auditada', 'STATUS_CHANGED_TO_COMPLETED', 'ana'
        )

    @override_settings(
        SUPABASE_AUDIT_ENABLED=True,
        SUPABASE_URL='https://demo.supabase.co',
        SUPABASE_KEY='demo-key',
    )
    @mock.patch(
        'tasks.supabase_client.requests.post',
        side_effect=requests.exceptions.ConnectTimeout('sin red'),
    )
    def test_service_keeps_working_when_supabase_times_out(self, mock_post):
        """Si Supabase no responde, el cliente falla silencioso y el
        servicio crea la tarea con normalidad (fail-safe)."""
        task = services.create_task(
            user=self.ana,
            title='Tarea offline',
            due_date='2026-10-03',
        )
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.assertEqual(task.status, Task.Status.PENDING)
        self.assertEqual(mock_post.call_count, 1)


class SupabaseClientTests(TestCase):
    """Cliente fail-safe aislado: sin credenciales, sin red o error
    de API -> retorna False sin propagar excepciones."""

    @override_settings(SUPABASE_AUDIT_ENABLED=False)
    def test_disabled_without_credentials_returns_false(self):
        result = supabase_client.log_task_event_to_supabase(
            1, 'Cualquiera', 'CREATED', 'ana'
        )
        self.assertFalse(result)

    @override_settings(
        SUPABASE_AUDIT_ENABLED=True,
        SUPABASE_URL='https://demo.supabase.co/',
        SUPABASE_KEY='anon-key',
    )
    @mock.patch('tasks.supabase_client.requests.post')
    def test_success_post_payload_and_headers(self, mock_post):
        mock_post.return_value.status_code = 201
        mock_post.return_value.text = ''
        ok = supabase_client.log_task_event_to_supabase(
            7, 'Preparar clase', 'CREATED', 'ana', {'prioridad': 'alta'}
        )
        self.assertTrue(ok)
        url = mock_post.call_args.args[0]
        payload = mock_post.call_args.kwargs['json']
        headers = mock_post.call_args.kwargs['headers']
        self.assertEqual(url, 'https://demo.supabase.co/rest/v1/task_audit_log')
        self.assertEqual(payload['task_id'], 7)
        self.assertEqual(payload['task_title'], 'Preparar clase')
        self.assertEqual(payload['action'], 'CREATED')
        self.assertEqual(payload['user_username'], 'ana')
        self.assertEqual(payload['metadata'], {'prioridad': 'alta'})
        self.assertEqual(headers['apikey'], 'anon-key')
        self.assertEqual(headers['Authorization'], 'Bearer anon-key')

    @override_settings(
        SUPABASE_AUDIT_ENABLED=True,
        SUPABASE_URL='https://demo.supabase.co',
        SUPABASE_KEY='anon-key',
    )
    @mock.patch(
        'tasks.supabase_client.requests.post',
        side_effect=requests.exceptions.Timeout('timeout'),
    )
    def test_connection_error_returns_false(self, mock_post):
        result = supabase_client.log_task_event_to_supabase(
            1, 'Tarea', 'CREATED', 'ana'
        )
        self.assertFalse(result)

    @override_settings(
        SUPABASE_AUDIT_ENABLED=True,
        SUPABASE_URL='https://demo.supabase.co',
        SUPABASE_KEY='anon-key',
    )
    @mock.patch('tasks.supabase_client.requests.post')
    def test_api_error_returns_false(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = '{"message":"boom"}'
        result = supabase_client.log_task_event_to_supabase(
            1, 'Tarea', 'CREATED', 'ana'
        )
        self.assertFalse(result)
