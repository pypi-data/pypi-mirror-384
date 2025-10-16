from jinja2 import Environment, FileSystemLoader
from importlib.resources import files
import taypiproject
import sys
import os

def create(name):
    # Si el nombre del microservicio ya existe, no lo creamos
    if os.path.exists(name):
        print(f"[INFO] El microservicio '{name}' ya existe.")
        return

    # si no esta ubicado en la carpeta del proyecto que debe contener un docker-compose.yaml para toda la ejecucion
    if not os.path.isfile(f"{os.getcwd()}/docker-compose.yaml"):
        print("[INFO] No se encuentra en la carpeta del proyecto.")
        sys.exit()

    TEMPLATE_DIR = str(files(taypiproject).joinpath("templates"))
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    context = {
        'name': name
    }


    estructura = [
        "app/components/filter/domain/value_objects",
        "app/components/filter/infrastructure/dto",
        "app/Traits",
        "commands",
        "config",
        "config/translate",
        "config/database",
        "database",
        "middleware",
        "middleware/exceptions",
        "database/migrations",
    ]

    archivos = {
        '.env': 'env.txt',
        'alembic.ini': 'microservice/alembic.ini.txt',
        "command": 'microservice/command.txt',
        'Dockerfile': 'dockerfile.txt',
        'requirements.txt': 'requirements.txt',
        'README.md': 'microservice/readme.txt',
        'app/main.py': 'microservice/main.txt',
        'app/components/filter/domain/filter.py': 'microservice/domain_filter.txt',
        'app/components/filter/domain/value_objects/filter.py': 'microservice/value_object_filter.txt',
        'app/components/filter/infrastructure/dto/input_filter.py': 'microservice/input_filter.txt',
        "app/Traits/filters.py": 'microservice/trait_filter.txt',
        "commands/seeder.py": 'microservice/command_seeder.txt',
        "config/database/settings.py": 'microservice/database_settings.txt',
        "config/database/connections.py": 'microservice/connections.txt',
        "config/secret.py": 'microservice/secret.txt',
        "config/settings.py": 'microservice/settings.txt',
        "config/translate/messages.py": 'microservice/messages.txt',
        "database/env.py": 'microservice/alembic_env.txt',
        "database/script.py.mako": 'microservice/alembic_script.txt',
        "middleware/validation.py": 'microservice/validation.txt',
        "middleware/exceptions/handler.py": 'microservice/handler.txt',
    }

    os.makedirs(name, exist_ok=True)

    # Crear subdirectorios
    for carpeta in estructura:
        os.makedirs(os.path.join(name, carpeta), exist_ok=True)

    # Crear archivos
    for archivo, path_template in archivos.items():
        try:
            content = env.get_template(path_template).render(**context)
        except Exception as e:
            print(f"[ERROR] El template del archivo '{archivo}' no existe: {e}")
            return

        ruta_archivo = os.path.join(name, archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[OK] El microservicio '{name}' creado con éxito.")