# Inicio local

Requisitos: Python 3.14, uv y Docker Desktop iniciado. La aplicación utiliza Django 6.0 y PostgreSQL 18.

En este equipo ya están instaladas las dependencias. Para iniciar, abrir PowerShell en esta carpeta y ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
```

La opción Bypass se aplica únicamente a ese proceso, sin modificar la política del equipo. Abrir http://127.0.0.1:8000/. Detener el servidor con Ctrl+C.

Para preparar el entorno desde cero, instalar uv y ejecutar desde esta carpeta:

```powershell
uv sync --locked
docker compose -f compose.database.yml up -d --wait
$env:DJANGO_READ_DOT_ENV_FILE = 'True'
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Abrir http://127.0.0.1:8000/ y el panel http://127.0.0.1:8000/admin/.

Para otra computadora: copiar `.env.example` como `.env`, establecer una clave local y seguir los pasos. No compartir `.env` ni subirlo a Git. Los correos se imprimen en la consola durante desarrollo.

Pruebas de la base generada:

```powershell
$env:DJANGO_READ_DOT_ENV_FILE = 'True'
uv run python manage.py check
uv run pytest
```

Detener la base local sin borrar datos:

```powershell
docker compose -f compose.database.yml stop
```

La portada es la página de ejemplo de la plantilla. Los mockups y las funciones de negocio aún no están implementados. Falta configurar fotografías y correo real antes de un despliegue de producción.
