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
    """Lista las tareas del usuario autenticado con filtros rápidos."""

    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # Persistencia: el QuerySet personalizado aísla por usuario.
        queryset = Task.objects.for_user(self.request.user)

        # Rama dev (WIP): filtros rápidos por estado y prioridad (?status=).
        status = self.request.GET.get('status', '')
        if status in Task.Status.values:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get('priority', '')
        if priority in Task.Priority.values:
            queryset = queryset.filter(priority=priority)

        return queryset

    def get_context_data(self, **kwargs):
        # Rama dev (WIP): métricas rápidas para el widget resumen.
        context = super().get_context_data(**kwargs)
        base = Task.objects.for_user(self.request.user)

        context['total_count'] = base.count()
        context['pending_count'] = base.filter(status=Task.Status.PENDING).count()
        context['in_progress_count'] = base.filter(
            status=Task.Status.IN_PROGRESS
        ).count()
        context['completed_count'] = base.filter(
            status=Task.Status.COMPLETED
        ).count()
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        return context


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
