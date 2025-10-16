# Proyecto FastAPI
Este es un proyecto FastAPI con arquitectura Hexagonal.
## Crear un nuevo proyecto
```bash
taypi-create init <nombre_proyecto>
```
## Crear un microservicio
```bash
taypi-create microservice <nombre_microservicio> <nombre_entidad>
```
## Crear una entity
```bash
taypi-create entity <nombre_entity>
```
## Agregar Dockerfile y .env
```bash
taypi-create envdocker
```
## Ejecutar el projecto
```bash
docker-compose up --build --force-recreate -d
```
## Destruir el projecto
```bash
docker-compose down
```

# 📌 Guía de Comandos Alembic

Alembic es una herramienta de migración de bases de datos para SQLAlchemy. Permite **crear, aplicar y revertir** cambios en la base de datos sin perder datos.

## 📌 Tabla de Comandos Alembic

| Comando | Descripción |
|---------|------------|
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic revision --autogenerate -m "Descripción"` | Crea una nueva migración detectando cambios automáticamente. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic upgrade heads` | Aplica todas las migraciones pendientes. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic upgrade <revision_id>` | Aplica una migración específica. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic downgrade -1` | Revierte la última migración aplicada. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic downgrade <revision_id>` | Revierte a una versión específica. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic downgrade base` | Elimina todas las migraciones y deja la base vacía. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic history` | Lista todas las migraciones creadas. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic current` | Muestra la versión de migración actualmente aplicada. |
| `docker-compose exec -e --connection=<connection_name> <microservicio> alembic stamp head` | Marca todas las migraciones como aplicadas sin ejecutarlas. |

## 🛠️ Tabla de Comandos seeders

| Comando | Descripción |
|---------|------------|
| `docker-compose exec <microservicio> python command seed:all` | Ejecuta todos los seeders. |
| `docker-compose exec <microservicio> python command seed --class=<NameSeeder> --connection=<connection_name>` | Ejecuta el seeder especifico. |