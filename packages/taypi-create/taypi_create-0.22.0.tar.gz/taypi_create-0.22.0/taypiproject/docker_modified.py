from ruamel.yaml.compat import StringIO
from ruamel.yaml import YAML
import os

def modify(name):

    yaml = YAML()
    yaml.preserve_quotes = True

    compose_file = "docker-compose.yaml"

    block = (
        f"  {name}:\n"
        "    build:\n"
        f"      context: ./{name}\n"
        "      dockerfile: Dockerfile\n"
        f"    container_name: {name}-service\n"
        "    volumes:\n"
        f"      - ./{name}:/app\n"
        "    command: uvicorn app.main:run --host 0.0.0.0 --port ${SERVICE_PORT} --reload\n"
        "    networks:\n"
        "      - project-network\n"
        "    expose:\n"
        "      - ${SERVICE_PORT}\n"
        "    depends_on:\n"
        "      - localdb\n"
    )

    # Leer el contenido actual
    with open(compose_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Buscar el índice de la línea que contiene el servicio nginx
    insert_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("nginx:") and line.startswith("  "):  # indentación 2 espacios
            insert_index = i
            break

    # Insertar el bloque antes de nginx si no está presente
    if insert_index is not None:
        if f"{name}:" not in "".join(lines):  # Evitar insertar duplicado
            lines.insert(insert_index, block)
            with open(compose_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"[OK] Servicio '{name}' insertado correctamente antes de 'nginx'")
        else:
            print(f"[INFO] El servicio '{name}' ya existe en el archivo docker-compose.yaml")
    else:
        print("[ERROR] No se encontró el servicio 'nginx:' en el archivo")

    with open(compose_file, 'r') as file:
        data = yaml.load(file)

    # Verifica si 'nginx' y su sección 'depends_on' existen
    nginx_service = data['services'].get('nginx', {})
    depends_on = nginx_service.get('depends_on', [])

    # Agrega el servicio al nginx
    if name not in depends_on:
        depends_on.append(name)

        # Actualiza el servicio nginx
        data['services']['nginx']['depends_on'] = depends_on

        # Guardar los cambios de vuelta en el archivo
        with open(compose_file, 'w') as file:
            yaml.dump(data, file)

        print(F"[OK] Se ha agregado el servicio '{name}' al 'depends_on' de nginx.")
    else:
        print(f"[INFO] El servicio '{name}' ya está presente en 'depends_on' de nginx.")
