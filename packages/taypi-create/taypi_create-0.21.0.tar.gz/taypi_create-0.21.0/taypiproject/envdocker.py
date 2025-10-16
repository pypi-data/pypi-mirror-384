from jinja2 import Environment, FileSystemLoader
from importlib.resources import files
import taypiproject
import sys
import os

def create():

    # comprobar que exista la carpeta app
    if not os.path.isdir(f"{os.getcwd()}/app"):
        print("[INFO] No se encuentra en la carpeta del un microservicio.")
        sys.exit()

    TEMPLATE_DIR = str(files(taypiproject).joinpath("templates"))
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    archivos = {
        '.env': 'env.txt',
        'Dockerfile': 'dockerfile.txt',
    }

    # Crear archivos
    for archivo, path_template in archivos.items():
        try:
            content = env.get_template(path_template).render()
        except Exception as e:
            print(f"[ERROR] El template del archivo '{archivo}' no existe: {e}")
            return

        ruta_archivo = os.path.join('', archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[OK] Se crearon los archivo Dockerfile y .env creado con éxito.")