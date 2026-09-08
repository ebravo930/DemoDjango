"""
Capa de control: flujo HTTP, permisos y orquestación de capas.

Vistas basadas en clases protegidas con `LoginRequiredMixin`. La vista
de creación delega en `services.create_task`; la actualización orquesta
formulario + servicio; el listado usa el QuerySet `for_user` para aislar
los datos de cada usuario.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from . import services
from .forms import TaskForm
from .models import Task


class TaskListView(LoginRequiredMixin, ListView):
    """Lista las tareas del usuario autenticado."""

    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # Persistencia: el QuerySet personalizado aísla por usuario.
        return Task.objects.for_user(self.request.user)


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Crea una tarea orquestando formulario y capa de servicio."""

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')

    def form_valid(self, form):
        # Dominio: la creación pasa por el servicio (sin objeto request).
        # La entidad creada queda en self.object para la URL de éxito.
        self.object = services.create_task(
            user=self.request.user, **form.cleaned_data
        )
        messages.success(self.request, 'Tarea creada correctamente.')
        return HttpResponseRedirect(self.get_success_url())


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Actualiza una tarea del usuario autenticado."""

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        # Seguridad: solo el dueño puede editar su propia tarea.
        return Task.objects.for_user(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance.status == Task.Status.COMPLETED:
            # Dominio: la transición a completada la gobierna el servicio
            # (en la rama dev este punto registra auditoría de negocio).
            services.mark_as_completed(form.instance)
        messages.success(self.request, 'Tarea actualizada correctamente.')
        return response


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Elimina una tarea del usuario autenticado (con confirmación)."""

    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        # Seguridad: solo el dueño puede eliminar su propia tarea.
        return Task.objects.for_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Tarea eliminada correctamente.')
        return super().form_valid(form)
