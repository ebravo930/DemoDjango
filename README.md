# TaskFlow INACAP 🎓

Proyecto **formativo** desarrollado con **Django**, **Bootstrap 5** y la paleta
institucional **INACAP**. Su propósito es enseñar dos habilidades centrales del
desarrollo de software:

1. **Arquitectura por capas de responsabilidad** dentro de una aplicación Django.
2. **Buenas prácticas de Git** con una estrategia de ramas `main` / `dev`
   (versión estable vs. características en desarrollo).

> Uso académico · Asignatura Programación Back End · INACAP

---

## 🧱 Mapeo de capas de responsabilidad

Cada capa vive en un archivo único y tiene **una sola responsabilidad**:

| Capa | Archivo | Responsabilidad |
|---|---|---|
| 🎨 **Presentación** | `tasks/templates/tasks/*.html` y `templates/base.html` | Interfaz responsive (móvil/escritorio) con Bootstrap 5 e identidad INACAP |
| ✅ **Validación** | `tasks/forms.py` | Sanitización de datos e inputs del usuario (`TaskForm`, `clean_due_date`) |
| 🎮 **Controlador** | `tasks/views.py` | Flujo HTTP, permisos (`LoginRequiredMixin`), orquestación de capas |
| ⚙️ **Servicio (dominio)** | `tasks/services.py` | Reglas de negocio puras (`create_task`, `mark_as_completed`), sin `request` |
| 🗄️ **Persistencia** | `tasks/models.py` | Esquema de base de datos y consultas ORM (`Task`, `TaskQuerySet.for_user`) |

La **configuración** del proyecto (`settings.py`, `urls.py` raíz) vive en la
carpeta `taskflow/`, y las URLs de la aplicación en `tasks/urls.py`.

### ¿Por qué separar capas?

- Un cambio de regla de negocio toca `services.py`, **no** los templates.
- Un cambio de base de datos toca `models.py` + migraciones, **no** las vistas.
- La lógica de negocio se puede probar con tests unitarios **sin HTTP**.

---

## 🌿 Estrategia de ramas Git (`main` vs `dev`)

| Rama | Contenido | Estado |
|---|---|---|
| `main` | CRUD esencial + autenticación + separación estricta de capas | ✅ Estable / productiva |
| `dev` | Agrega **prioridades** (BAJA/MEDIA/ALTA), **filtros** y **auditoría de negocio** | 🚧 En desarrollo (WIP) |

La rama `dev` **nace de `main`** y avanza en paralelo, tal como se trabaja en
equipos reales: las características nuevas se desarrollan en `dev` y viajan a
`main` cuando terminan (merge o Pull Request).

### Diferencias entre ramas `main` y `dev`

**`main` (estable):** CRUD esencial, autenticación y una responsabilidad por
archivo (modelo, formulario, servicio, vista, template).

**`dev` (en desarrollo) agrega:**

1. **Prioridades y filtros** — campo `priority` (Baja/Media/Alta) y barra de
   filtrado rápido por estado/prioridad. Un requerimiento así impacta *varias
   capas a la vez*: modelo, migración, formulario, servicio, vista y template.
2. **Auditoría y métricas** — `services.py` registra en consola cada creación
   y cambio de estado (`[AUDIT]`), y la vista de listado muestra contadores de
   tareas (pendientes / en progreso / completadas).
3. **Endpoint de estado (kanban WIP)** — `TaskStatusUpdateView` acepta
   `POST /tareas/<pk>/estado/` con `status=...` y responde `JsonResponse`
   (200/400/403/404); la transición la gobierna `update_task_status` del
   servicio (validación + autorización de dominio).

Para mostrar a los alumnos el viaje de una feature entre ramas:

```bash
# Archivos que cambiaron entre la versión estable y dev
git diff main..dev --stat

# El impacto de "prioridades" capa por capa
git diff main..dev -- taskflow/settings.py tasks/models.py tasks/forms.py
git diff main..dev -- tasks/services.py
git diff main..dev -- tasks/views.py
git diff main..dev -- tasks/templates/tasks/task_list.html
```

### Comandos de inspección para la clase

```bash
# Ver el historial completo como grafo de ramas
git log --oneline --graph --all

# ¿Qué commits tiene dev que main no tenga?
git log main..dev --oneline

# ¿Qué archivos cambian entre la versión estable y la versión en desarrollo?
git diff main..dev --stat

# Ver el impacto de un requerimiento nuevo (p. ej. "prioridades") capa por capa
git diff main..dev -- tasks/models.py
git diff main..dev -- tasks/forms.py
git diff main..dev -- tasks/services.py
git diff main..dev -- tasks/templates/tasks/task_list.html
```

> 💡 Un requerimiento nuevo casi siempre impacta **varias capas a la vez**:
> el modelo (nuevo campo), el formulario (nuevo widget), el servicio (nueva
> regla) y el template (nueva UI). `git diff main..dev` lo muestra de un vistazo.

---

## 🚀 Instalación y despliegue local

```bash
# 1. Crear y activar el entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows (cmd o PowerShell)

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear y aplicar las migraciones (base de datos SQLite)
python manage.py migrate

# 4. Crear un usuario para ingresar (se puede repetir las veces que quieras)
python manage.py createsuperuser

# 5. Levantar el servidor de desarrollo
python manage.py runserver
```

Abre <http://127.0.0.1:8000> en tu navegador e inicia sesión con el usuario
creado. La base de datos `db.sqlite3` está **ignorada por Git** (`.gitignore`),
así que cada persona crea su propio usuario local.

---

## 🧪 Estrategia de testing por capas

Los tests viven en `tasks/tests/` como un **paquete Python con un módulo por
capa de responsabilidad** (`tasks/tests/test_<capa>.py`). Así se aprende qué
tipo de test corresponde a cada componente y se ejecuta solo la capa que
interesa:

```bash
# Ejecutar todas las pruebas del proyecto
python manage.py test

# Probar únicamente la capa de lógica de negocio (servicios)
python manage.py test tasks.tests.test_services

# Probar únicamente la capa de validación de formularios
python manage.py test tasks.tests.test_forms

# Probar la capa de persistencia o la capa de control
python manage.py test tasks.tests.test_models
python manage.py test tasks.tests.test_views
```

### Tabla comparativa: ¿qué prueba cada capa?

| Capa probada | Archivo de prueba | ¿Qué se evalúa? | ¿Requiere simular HTTP? |
|---|---|---|---|
| **Modelos** (persistencia) | `test_models.py` | Esquema, valores por defecto, integridad referencial y custom querysets (`for_user`) | No |
| **Servicios** (dominio) | `test_services.py` | Reglas de negocio puras, excepciones de dominio (`ValueError` / `PermissionError`) y cambios de estado | No |
| **Formularios** (validación) | `test_forms.py` | Validación de inputs, formato de fechas ISO y mensajes de error | No |
| **Vistas** (control) | `test_views.py` | Control de acceso (`LoginRequiredMixin`), respuestas HTTP, redirecciones y renders | Sí (`self.client.get/post`) |

### ¿Por qué esta estructura?

1. **Desmitifica que todo se prueba con `self.client`**: los alumnos suelen
   creer que en Django siempre hay que hacer peticiones HTTP. Ver que
   `test_services.py` solo crea objetos y llama funciones Python estándar
   refuerza de inmediato la ventaja de tener una capa de servicios.
2. **Verificación rápida de bugs**: con `test_forms.py` se comprueba
   programáticamente por qué el formato de fecha ISO `YYYY-MM-DD` es el único
   que pasa la validación del navegador y de Django.
3. **Seguridad reforzada**: al testear `PermissionError` en el servicio y el
   redirect en las vistas, se ve la seguridad en dos niveles: el controlador
   (UI/ruta) y el dominio (negocio).

---

## 🖥️ Vistas y URLs

| Ruta | Vista | Descripción |
|---|---|---|
| `/` | `TaskListView` | Mis tareas + contadores y filtros `?status=` / `?priority=` (rama dev) |
| `/nueva/` | `TaskCreateView` | Crear tarea |
| `/tareas/<pk>/editar/` | `TaskUpdateView` | Editar tarea |
| `/tareas/<pk>/eliminar/` | `TaskDeleteView` | Eliminar tarea (con confirmación) |
| `/tareas/<pk>/estado/` | `TaskStatusUpdateView` | Cambio de estado asíncrono vía JSON (rama dev, kanban WIP) |
| `/accounts/login/` | Auth nativa Django | Iniciar sesión |
| `/accounts/logout/` | Auth nativa Django | Cerrar sesión |
| `/admin/` | Django Admin | Panel administrativo |

---

## 🎨 Identidad visual (INACAP + Bootstrap 5)

- **Rojo institucional:** `#D3141F` (hover `#B50E17`) — botones `.btn-inacap`.
- **Gris carbón:** `#1E242B` — navbar con franja roja decorativa de 3px.
- **Fondo suave:** `#F4F6F9` · **Bordes:** `#E2E8F0`.
- **Mobile first:** contenedor `container py-4`, columnas `col-12 col-md-6 col-lg-4`,
  navbar colapsable (hamburguesa) en móviles.
- **Badges de estado:** `Pendiente` (warning), `En progreso` (info),
  `Completada` (success).
- **Badges de prioridad (rama dev):** `Alta` (danger), `Media` (secondary),
  `Baja` (light con borde).
- Bootstrap 5 y Bootstrap Icons vía **CDN** (sin dependencias locales).

---

## 📂 Estructura del proyecto

```
DemoDjango/
├── manage.py
├── requirements.txt
├── .gitignore
├── taskflow/                  # Configuración del proyecto
│   ├── settings.py            # Apps, templates, auth, idioma es-cl
│   └── urls.py                # Rutas raíz (admin, accounts, tasks)
├── authentication/            # App de autenticación (espacio para futuras vistas)
├── templates/                 # Templates compartidos (proyecto)
│   ├── base.html              # Layout INACAP + Bootstrap 5
│   └── registration/login.html
└── tasks/                     # App principal (una capa por archivo)
    ├── models.py              # 🗄️ Persistencia (Task + TaskQuerySet)
    ├── services.py            # ⚙️ Dominio / reglas de negocio
    ├── forms.py               # ✅ Validación
    ├── views.py               # 🎮 Controlador (CBV + LoginRequiredMixin)
    ├── urls.py                # Rutas de la app
    ├── admin.py
    ├── migrations/
    ├── tests/                 # 🧪 Suite por capas (un módulo por capa)
    │   ├── test_models.py     #    Persistencia: ORM, defaults, for_user
    │   ├── test_services.py   #    Dominio: reglas de negocio y excepciones
    │   ├── test_forms.py      #    Validación: fechas ISO, clean_due_date
    │   └── test_views.py      #    Control: HTTP, permisos y renders
    └── templates/tasks/       # 🎨 Presentación (list / form / delete)
```

---

## 📜 Historial de commits (línea base `main`)

```bash
chore: initialize django project structure and gitignore
feat(auth): add responsive inacap base layout and auth views
feat(tasks): create task model, status choices and user relationships
feat(tasks): implement domain service layer for business logic
feat(tasks): implement task form with bootstrap widgets and validation
feat(tasks): create crud views orchestrating forms and services
feat(tasks): add fully responsive templates for task management
docs: add comprehensive readme explaining architecture and setup
```

Rama `dev` (características en desarrollo):

```bash
feat(tasks): add task priority field and service handling [WIP]
feat(ui): implement status filtering and summary counters in dev branch
```

*Proyecto con fines exclusivamente académicos. Django, Bootstrap y las marcas
mencionadas pertenecen a sus respectivos dueños.*
