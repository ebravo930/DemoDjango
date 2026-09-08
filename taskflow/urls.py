"""
Configuración de URLs del proyecto taskflow.

Las URLs de la aplicación `tasks` se incorporan en la FASE de controladores
(commit de vistas CRUD). Aquí viven las rutas administrativas y las URLs
nativas de autenticación de Django.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Home: aplicación de tareas (vistas CRUD de la capa de control)
    path('', include('tasks.urls')),
    # URLs nativas de autenticación: login, logout, cambio de contraseña, etc.
    path('accounts/', include('django.contrib.auth.urls')),
]
