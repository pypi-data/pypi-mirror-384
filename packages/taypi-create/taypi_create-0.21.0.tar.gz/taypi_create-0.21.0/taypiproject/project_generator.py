from jinja2 import Environment, FileSystemLoader
from importlib.resources import files
import taypiproject
import os

def create(name):

    TEMPLATE_DIR = str(files(taypiproject).joinpath("templates"))
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    estructura = [
        "nginx/ssl",
        "nginx/sites",
        "example_entity/app",
    ]

    archivos = {
        "README.md" : 'project/README.txt',
        ".env" : 'project/env.txt',
        "docker-compose.yaml": 'project/docker-compose.txt',
        "nginx/sites/example_entity.conf": 'project/site_example.txt',
        "example_entity/app/main.py" : 'project/main_example.txt',
        "example_entity/requirements.txt": 'requirements.txt',
        "example_entity/Dockerfile": 'dockerfile.txt',
    }

    # Crear directorio base
    os.makedirs(name, exist_ok=True)

    print(f"[INFO] Creando proyecto '{name}'...")

    # Crear subdirectorios
    for carpeta in estructura:
        os.makedirs(os.path.join(name, carpeta), exist_ok=True)

    # Crear archivos vacíos
    for archivo, path_template in archivos.items():
        try:
            content = env.get_template(path_template).render()
        except Exception as e:
            print(f"[ERROR] El template del archivo'{archivo}' no existe.")
            return

        ruta_archivo = os.path.join(name, archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[OK] Proyecto '{name}' creado con exito.")