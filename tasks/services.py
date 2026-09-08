"""
Capa de dominio (servicios): reglas de negocio puras.

Las funciones de servicio encapsulan la creación y las transiciones de
estado de una tarea SIN depender del objeto `request` ni de formularios:
reciben datos y devuelven entidades del dominio.
"""
from .models import Task


def create_task(*, user, title, description='', due_date, status=Task.Status.PENDING):
    """Crea una tarea para `user` aplicando las reglas de negocio."""
    if not title or not title.strip():
        raise ValueError('El título de la tarea no puede estar vacío.')

    return Task.objects.create(
        user=user,
        title=title.strip(),
        description=description,
        due_date=due_date,
        status=status,
    )


def mark_as_completed(task):
    """Transición de estado: marca la tarea como completada (idempotente)."""
    if task.status == Task.Status.COMPLETED:
        return task

    task.status = Task.Status.COMPLETED
    task.save(update_fields=['status'])
    return task
