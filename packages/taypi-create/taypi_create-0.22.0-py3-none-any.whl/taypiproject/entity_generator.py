from jinja2 import Environment, FileSystemLoader
from importlib.resources import files
import taypiproject
import inflection
import sys
import os

def create(name, microservice = None):

    camel_case_plural = lambda s: inflection.pluralize(s.split('_')[0]) + ''.join(word.capitalize() for word in s.split('_')[1:])
    pascal_case = ''.join(word.capitalize() for word in name.split('_'))
    name_plural = camel_case_plural(name)
    plural = inflection.pluralize(name)

    TEMPLATE_DIR = str(files(taypiproject).joinpath("templates"))
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    context = {
        'name': name,
        'pascal_case': pascal_case,
        'name_plural': name_plural,
        'name_plural_capitalized': name_plural.capitalize(),
        'plural': plural,
    }

    estructura = [
        "application/services",
        "application/use_cases",
        "domain/entities",
        "domain/repositories",
        "domain/value_objects",
        "infrastructure/dto",
        "infrastructure/models",
        "infrastructure/repositories",
        "infrastructure/routers",
        "infrastructure/validations",
    ]

    archivos = {
        f"application/services/{name}_service.py": 'entity/service.txt',
        f"application/use_cases/create_{name}.py": 'entity/use_case_create.txt',
        f"application/use_cases/delete_{name}.py": 'entity/use_case_delete.txt',
        f"application/use_cases/get_{name_plural}.py": 'entity/use_case_get_all.txt',
        f"application/use_cases/get_{name}_by_id.py": 'entity/use_case_get_by_id.txt',
        f"application/use_cases/update_{name}.py": 'entity/use_case_update.txt',
        f"domain/entities/{name}.py": 'entity/entity.txt',
        f"domain/repositories/{name}_repository.py": 'entity/repository.txt',
        f"domain/value_objects/datetime.py": 'entity/value_object_datetime.txt',
        f"infrastructure/dto/input_{name}.py": 'entity/input_dto.txt',
        f"infrastructure/dto/output_{name}.py": 'entity/output_dto.txt',
        f"infrastructure/models/{name}_model.py": 'entity/model.txt',
        f"infrastructure/repositories/{name}_repository_impl.py": 'entity/repository_impl.txt',
        f"infrastructure/routers/{name}_router.py": 'entity/router.txt',
        f"infrastructure/validations/insert.py": 'entity/insert_validation.txt',
        f"infrastructure/validations/update.py": 'entity/update_validation.txt',
    }

    if microservice is None and not os.path.isfile(f"{os.getcwd()}/Dockerfile"):
        print("[INFO] No se encuentra en la carpeta de un microservicio.")
        sys.exit()

    if microservice is not None:
        path = f"{microservice}/app/{name}"
    else:
        path = f"app/{name}"

    # Si la entidad ya existe, no la crea
    if os.path.exists(path):
        print(f"[INFO] La entidad {name} ya existe.")
        return

    if microservice is not None:
        os.makedirs(microservice + '/app/' + name, exist_ok=True)
    else:
        os.makedirs(path, exist_ok=True)

    # Crear subdirectorios
    for carpeta in estructura:
        os.makedirs(os.path.join(path, carpeta), exist_ok=True)

    # Crear archivos vacíos
    for archivo, path_template in archivos.items():
        try:
            content = env.get_template(path_template).render(**context)
        except Exception as e:
            print(f"[ERROR] No se pudo crear el archivo {archivo}: {e}")
            return

        ruta_archivo = os.path.join(path, archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[OK] Entidad {name} creada con éxito.")
