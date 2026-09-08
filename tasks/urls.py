"""
Rutas de la aplicación `tasks` (capa de control).

Cada URL apunta a una vista basada en clase que protege el acceso.
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('nueva/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/editar/', views.TaskUpdateView.as_view(), name='task_update'),
    path('<int:pk>/eliminar/', views.TaskDeleteView.as_view(), name='task_delete'),
    # Rama dev (kanban WIP): cambio asíncrono de estado vía JSON
    path('<int:pk>/estado/', views.TaskStatusUpdateView.as_view(), name='task_status_update'),
]
