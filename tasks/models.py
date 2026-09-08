"""
Capa de persistencia: esquema de base de datos y consultas ORM.

El modelo `Task` NO conoce HTTP ni formularios: solo representa el dato
y expone consultas reutilizables a través de su QuerySet personalizado.
"""
from django.conf import settings
from django.db import models


class TaskQuerySet(models.QuerySet):
    """QuerySet personalizado con consultas de dominio reutilizables."""

    def for_user(self, user):
        """Devuelve únicamente las tareas que pertenecen a `user`."""
        return self.filter(user=user)


class Task(models.Model):
    """Tarea del sistema TaskFlow."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        IN_PROGRESS = 'IN_PROGRESS', 'En progreso'
        COMPLETED = 'COMPLETED', 'Completada'

    title = models.CharField('título', max_length=200)
    description = models.TextField('descripción', blank=True)
    due_date = models.DateField('fecha de vencimiento')
    status = models.CharField(
        'estado',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='usuario',
        on_delete=models.CASCADE,
        related_name='tasks',
    )

    # Manager con QuerySet personalizado (Task.objects.for_user(...))
    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ['due_date', 'title']
        verbose_name = 'tarea'
        verbose_name_plural = 'tareas'

    def __str__(self):
        return self.title
