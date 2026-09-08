"""
Capa de dominio (servicios): reglas de negocio puras.

Las funciones de servicio encapsulan la creación y las transiciones de
estado de una tarea SIN depender del objeto `request` ni de formularios:
reciben datos y devuelven entidades del dominio.

Rama `dev` (WIP): soporte de `priority` y auditoría en consola ([AUDIT])
en cada creación y cambio de estado.

Toda transición de estado pasa por UNA única puerta: `update_task_status`,
que valida el estado destino (ValueError) y la autorización del actor
(PermissionError). La seguridad vive en dos niveles: el controlador
protege la ruta (UI) y el servicio protege la regla de negocio (dominio).
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


def update_task_status(*, task, new_status, user):
    """Transición de estado con validación y autorización de dominio.

    - `new_status` debe existir en Task.Status      -> lanza ValueError
    - solo el dueño puede cambiar el estado         -> lanza PermissionError

    Devuelve la tarea ya persistida con el nuevo estado.
    """
    if new_status not in Task.Status.values:
        raise ValueError(
            f"Estado inválido: '{new_status}'. "
            f"Opciones válidas: {', '.join(Task.Status.values)}."
        )

    if task.user_id != user.id:
        raise PermissionError('No puedes modificar una tarea de otro usuario.')

    previous = task.get_status_display()
    task.status = new_status
    task.save(update_fields=['status'])

    # Auditoría de negocio (rama dev): registro del cambio de estado.
    logger.info(
        '[AUDIT] tarea #%s "%s" cambió de estado (%s -> %s), responsable: %s',
        task.pk,
        task.title,
        previous,
        task.get_status_display(),
        task.user.username,
    )
    return task


def mark_as_completed(task):
    """Caso de uso de alto nivel: marcar la tarea como completada.

    Delega en `update_task_status` usando al dueño como actor. Es seguro
    únicamente en flujos donde la autorización ya fue verificada (las
    vistas acotan con Task.objects.for_user()).
    """
    return update_task_status(
        task=task,
        new_status=Task.Status.COMPLETED,
        user=task.user,
    )
