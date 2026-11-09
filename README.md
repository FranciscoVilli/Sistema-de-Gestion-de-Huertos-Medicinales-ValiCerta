# Huertos Medicinales Comunitarios (ValiCerta)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## ¿Para qué sirve el sistema?

Es un sistema web para gestionar huertos medicinales comunitarios. Desarrollado como proyecto académico de la materia de Calidad de Software (marca de créditos de desarrollo: **ValiCerta**). Se presenta explícitamente como un piloto académico, **no como un servicio oficial del MSP** (Ministerio de Salud Pública) — esta aclaración aparece en el pie legal y en los textos de la aplicación y debe mantenerse.

Con él se puede gestionar:

- **Aprendizaje de plantas medicinales**: lecciones, evaluaciones y catálogo de plantas (familia, ciclo, región, clasificación tradicional caliente/fría), con progresión por XP.
- **Prácticas reales de siembra ("Mis prácticas")**: registro con fecha real de inicio, etapa calculada (semilla / creciendo / madura) según el tiempo transcurrido, observaciones con foto, calendario de actividades con aviso de fase lunar, y empaquetado/etiquetado con caducidad según región.
- **Comunidades**: directorio público con mapa, solicitud y aprobación de miembros, talentos certificados, huerto real y bodega por comunidad, foro con reglas de participación, y un sistema de gamificación (puntos, niveles, insignias y misiones).
- **Privacidad**: páginas legales, consentimiento de cookies y gestión de derechos de datos personales.
- **Panel**: tablero general para el usuario.

## Tecnologías usadas

- **Python 3.14** + **Django 6.0** (framework web principal)
- **PostgreSQL 18** como base de datos, corriendo en **Docker** (vía `compose.database.yml`)
- **django-allauth** (autenticación, incluye verificación en dos pasos/MFA)
- **uv** como gestor de dependencias y entorno virtual de Python
- **Redis** (caché) y **Whitenoise** (archivos estáticos)
- **Pillow** (manejo de imágenes/fotos de las prácticas)
- **Gunicorn** (servidor para producción)
- **pytest**, **ruff**, **mypy**, **pre-commit** (pruebas, lint y tipado para desarrollo)

## Cómo ejecutar el proyecto en local

Requisitos previos: **Docker Desktop**, **Python 3.14** y **uv** instalados.

### 1. Clonar el repositorio e instalar dependencias

```powershell
git clone https://github.com/FranciscoVilli/Sistema-de-Gestion-de-Huertos-Medicinales-ValiCerta.git
cd Sistema-de-Gestion-de-Huertos-Medicinales-ValiCerta
uv sync --locked
```

### 2. Configurar las variables de entorno

Copiar `.env.example` como `.env` y completar los valores (clave local, etc.). **No subir `.env` a Git** — ya está ignorado por `.gitignore`.

```powershell
copy .env.example .env
```

### 3. Descargar y levantar el contenedor de la base de datos

Este paso descarga la imagen de PostgreSQL (si no la tienes) y la deja corriendo en segundo plano antes de ejecutar la aplicación:

```powershell
docker compose -f compose.database.yml up -d --wait
```

### 4. Aplicar las migraciones y crear un usuario

```powershell
$env:DJANGO_READ_DOT_ENV_FILE = 'True'
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

### 5. Ejecutar el servidor

```powershell
uv run python manage.py runserver
```

Abrir http://127.0.0.1:8000/ y el panel de administración en http://127.0.0.1:8000/admin/. Detener el servidor con `Ctrl+C`.

> Atajo: una vez configurado el `.env`, el script `iniciar.ps1` hace los pasos 3 a 5 en un solo comando: `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1`

### Detener la base de datos sin borrar los datos

```powershell
docker compose -f compose.database.yml stop
```

## Cuentas de usuario

- Para crear una **cuenta normal**, ir a "Registrarse" y llenar el formulario. En desarrollo, el correo de verificación se imprime en la consola — copiar el enlace desde ahí.
- Para crear una **cuenta de superusuario** (acceso al panel de administración):

  ```powershell
  uv run python manage.py createsuperuser
  ```

## Pruebas

```powershell
$env:DJANGO_READ_DOT_ENV_FILE = 'True'
uv run python manage.py check
uv run pytest
```

### Cobertura de pruebas

```powershell
uv run coverage run -m pytest
uv run coverage html
```

### Verificación de tipos (mypy)

```powershell
uv run mypy huertos_medicinales
```

### Lint

```powershell
uv run ruff check .
```

## Documentación adicional

Cada funcionalidad nueva tiene su propio documento en `docs/` (por ejemplo `docs/gamificacion-comunitaria.md`, `docs/huerto-real.md`, `docs/catalogo-plantas-enriquecido.md`). El alcance, la arquitectura y la trazabilidad de requisitos del proyecto viven fuera del código, en las carpetas `documentacion/` y `entregas/` del repositorio raíz del proyecto (`Proyecto Huertos Medicinales/`).
