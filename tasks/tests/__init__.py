"""Paquete de tests de la aplicación `tasks`, organizado por capas.

Cada módulo prueba UNA capa de responsabilidad:

- test_models.py   -> Capa de persistencia (ORM, constraints, querysets)
- test_services.py -> Capa de dominio (reglas de negocio puras)
- test_forms.py    -> Capa de validación (inputs, fechas, mensajes)
- test_views.py    -> Capa de control (HTTP, permisos, renders)
"""
