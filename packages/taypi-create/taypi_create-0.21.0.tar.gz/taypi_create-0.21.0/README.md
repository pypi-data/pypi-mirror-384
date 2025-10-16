# 🚀 taypi-create

**taypi-create** Es un proyecto de Docker que implementa una arquitectura **hexagonal** (puertos y adaptadores) con **FastAPI**, **PostGreSQL**, **SQLAlchemy** y **Alembic**. Está pensado para escalar y adaptarse a microservicios, con gestion de migraciones.

---

## 📦 Características

- 🐍 Python (FastApi)
- ✅ Arquitectura hexagonal (Domain Driven Design)
- 🛢️ PostgreSQL para manjo de base de datos
- 🧱 ORM SQLAlchemy
- 📜 Control de versiones en base de dats con Alembic
- 🐳 Soporte para Docker usando docker-compose
- ⚙️ Configuración por entorno
- 🔧 Creación de CRUD para entidades

---

# Comandos cli

## 🐳 Crear proyecto
```
taypi-create init <project-name>
```

## 🧩 Crear microservicio
```
taypi-create microservice <microservice-naem> <entity-name>
```

## 🐍 Crear entidad
```
taypi-create entity <entity-name>
```

## 🍃 Agregar Dockerfile y .env
```
taypi-create envdocker
```

