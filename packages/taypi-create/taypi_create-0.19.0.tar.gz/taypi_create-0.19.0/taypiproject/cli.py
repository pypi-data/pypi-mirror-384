import argparse

from taypiproject.microservice_generator import create as microservice
from taypiproject.docker_modified import modify as docker_modify
from taypiproject.migration_generator import create as migration
from taypiproject.readme_modified import modify as readme_modify
from taypiproject.main_modified import modify as main_modify
from taypiproject.project_generator import create as project
from taypiproject.git_generator import create as git_create
from taypiproject.entity_generator import create as entity
from taypiproject.site_generator import create as site
from taypiproject.envdocker import create as envdocker_create

def main():
    parser = argparse.ArgumentParser(description="Generador de proyectos FastAPI con docker-compose y base de datos postgres.")
    subparsers = parser.add_subparsers(dest="accion", required=True, help="Acciones disponibles.")
    # Comando para inicializar un nuevo proyecto
    init_parser = subparsers.add_parser("init", help="Iniciar un nuevo proyecto.")
    init_parser.add_argument("name", help="Nombre del proyecto.")

    # Comando para crear un microservicio
    microservice_parser = subparsers.add_parser("microservice", help="Crear un microservicio con Arquitectura Hexagonal.")
    microservice_parser.add_argument("name", help="Nombre del microservicio.")
    microservice_parser.add_argument("entity", help="Nombre de la entidad.")

    # Comando para crear una entity
    entity_parser = subparsers.add_parser("entity", help="Crear una entity con Arquitecura Hexagonal.")
    entity_parser.add_argument("name", help="Nombre de la entity.")

    # Comando para agregar en .env y el Dockerfile
    envdocker_parser = subparsers.add_parser("envdocker", help="Agregar en .env y el Dockerfile.")

    args = parser.parse_args()

    if args.accion == "init":
        print("[INFO] Iniciando un nuevo proyecto...")
        project(args.name)
        git_create("init", args.name)

    elif args.accion == "microservice":
        microservice(args.name)
        docker_modify(args.name)
        site(args.name)
        entity(args.entity, args.name)
        migration(args.entity, args.name)
        main_modify(args.entity, args.name)
        readme_modify(args.entity, args.name)
        git_create("microservice", args.name)

    elif args.accion == "entity":
        entity(args.name)
        migration(args.name)
        main_modify(args.name)
        readme_modify(args.name)

    #comando para agregar en .enc y el Dockerfile
    elif args.accion == "envdocker":
        envdocker_create()

if __name__ == "__main__":
    main()
