"""
Capa de dominio (servicios): reglas de negocio puras.

Las funciones de servicio encapsulan la creación y las transiciones de
estado de una tarea SIN depender del objeto `request` ni de formularios:
reciben datos y devuelven entidades del dominio.

Rama `dev` (WIP): agrega soporte de `priority` y un registro de auditoría
simple que escribe en consola cada creación y cambio de estado.
"""
import logging

from .models import Task

logger = logging.getLogger(__name__)


def create_task(
    *,
    user,
    title,
    description='',
    due_date,
    status=Task.Status.PENDING,
    priority=Task.Priority.MEDIUM,
):
    """Crea una tarea para `user` aplicando las reglas de negocio."""
    if not title or not title.strip():
        raise ValueError('El título de la tarea no puede estar vacío.')

    task = Task.objects.create(
        user=user,
        title=title.strip(),
        description=description,
        due_date=due_date,
        status=status,
        priority=priority,
    )

    # Auditoría de negocio (rama dev): cada creación queda registrada.
    logger.info(
        '[AUDIT] tarea #%s "%s" creada por %s (estado=%s, prioridad=%s)',
        task.pk,
        task.title,
        task.user.username,
        task.get_status_display(),
        task.get_priority_display(),
    )
    return task


def mark_as_completed(task):
    """Transición de estado: marca la tarea como completada (idempotente)."""
    if task.status == Task.Status.COMPLETED:
        return task

    previous = task.get_status_display()
    task.status = Task.Status.COMPLETED
    task.save(update_fields=['status'])

    # Auditoría de negocio (rama dev): registro del cambio de estado.
    logger.info(
        '[AUDIT] tarea #%s "%s" cambió de estado (%s -> COMPLETADA), '
        'responsable: %s',
        task.pk,
        task.title,
        previous,
        task.user.username,
    )
    return task
