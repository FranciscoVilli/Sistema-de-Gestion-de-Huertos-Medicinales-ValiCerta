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
- **Whitenoise** (archivos estáticos); la caché usa la memoria del proceso (LocMemCache), sin Redis
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

### 5. Cargar el contenido educativo (obligatorio)

Sin este paso, el módulo **Aprender** aparece vacío y no se desbloquean plantas:

```powershell
uv run python manage.py seed_curriculum              # 6 módulos, 24 capítulos y sus lecciones
uv run python manage.py seed_plant_routes            # una ruta educativa por planta
uv run python manage.py agregar_saberes_ancestrales  # saberes ancestrales del MSP en Aprender
uv run python manage.py configurar_roles             # grupos de facilitadores y gestores
```

Opcional, solo para demostraciones (crea datos marcados como `[DEMO]`, sin duplicarlos):

```powershell
uv run python manage.py seed_community_demo
uv run python manage.py seed_mapa_demo
uv run python manage.py seed_ranking_demo
```

Los contenidos educativos (módulos, capítulos, lecciones, evaluaciones y rutas) se administran en `/admin/` → *Aprendizaje*.

### 6. Ejecutar el servidor

```powershell
uv run python manage.py runserver
```

Abrir http://127.0.0.1:8000/ y el panel de administración en http://127.0.0.1:8000/admin/. Detener el servidor con `Ctrl+C`.

> Atajo: una vez configurado el `.env`, el script `iniciar.ps1` levanta la base de datos, aplica las migraciones y ejecuta el servidor en un solo comando (la carga de contenido del paso 5 se hace una sola vez): `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1`

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

## Experiencia y ranking (resumen)

- **XP de aprendizaje** (HU-004): 10 por lección completada y 40 por capítulo aprobado en *Aprender*; repetir una evaluación no duplica la experiencia.
- **Ranking de comunidades** (HU-013): suma los puntos de los integrantes con membresía aprobada por actividades de cultivo completadas y observaciones registradas; los empates comparten puesto.

## Recorrido de demostración (Versión 1)

Sigue las historias de usuario entregadas (HU-001 a HU-015):

1. **Cuenta y perfil** (HU-001, HU-002): registrarse o ingresar, completar el perfil y consultar el código único.
2. **Aprender** (HU-003, HU-004): abrir un módulo, completar lecciones en orden y aprobar la evaluación del capítulo.
3. **Mi rincón verde** (HU-005, HU-006): colocar una planta desbloqueada en el jardín, registrar un cuidado con foto y consultar la bitácora.
4. **Calendario y clima** (HU-007, HU-008): programar una actividad (también escrita libremente) y consultar el clima del jardín.
5. **Comunidad y mapa** (HU-009 a HU-013): crear una comunidad, publicar en el foro con adjuntos o encuestas, explorar el mapa y consultar el ranking.
6. **Privacidad y administración** (HU-014, HU-015): preferencias de cookies y mapas; gestión de contenidos en `/admin/`.

## Documentación adicional

La documentación de la entrega **Versión 1** (historias de usuario, casos de prueba con resultados e informe) está en [`docs/v1/`](docs/v1/).

Cada funcionalidad tiene además su propio documento técnico en `docs/` (por ejemplo `docs/gamificacion-comunitaria.md`, `docs/huerto-real.md`, `docs/catalogo-plantas-enriquecido.md`).
