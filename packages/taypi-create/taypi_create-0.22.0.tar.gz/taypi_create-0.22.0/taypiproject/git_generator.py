from pathlib import Path
import subprocess
import time
import sys
import os

def run_command(command, cwd=None):
    subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        check=True,
        stdout=subprocess.DEVNULL,   # No mostrar salida estándar
    )

def ensure_git_identity(project_path):
    """Valida si Git tiene configurado user.name y user.email en este repo."""
    def get_config(key):
        result = subprocess.run(
            f"git config --get {key}",
            cwd=project_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()

    username = get_config("user.name")
    email = get_config("user.email")

    if not username:
        username = input("[!] No se encontró un user.name en Git. Ingresa tu nombre: ").strip()
        run_command(f'git config user.name "{username}"', cwd=project_path)

    if not email:
        email = input("[!] No se encontró un user.email en Git. Ingresa tu email: ").strip()
        run_command(f'git config user.email "{email}"', cwd=project_path)

    print(f"[OK] Git identity configurada: {username} <{email}>")

def create(proccess, name):
    if proccess == "init":
        gitignore = (
            ".env\n"
            ".DS_Store\n"
            ".vscode/\n"
            ".idea/\n"
            "example_entity\n"
            "nginx/sites/example_entity.conf\n"
        )
    elif proccess == "microservice":
        gitignore = (
            "# Entornos virtuales\n"
            "venv/\n"
            ".env\n"
            "\n"
            "# Archivos de Python compilados\n"
            "__pycache__/\n"
            "*.py[cod]\n"
            "*.pyo\n"
            "\n"
            "# Configuración de IDE\n"
            ".vscode/\n"
            ".idea/\n"
            "\n"
            "# Archivos temporales\n"
            "*.log\n"
            ".DS_Store\n"
            "\n"
            "# Build\n"
            "dist/\n"
            "build/\n"
            "*.egg-info/\n"
            "\n"
            "# Archivos de configuración de Docker\n"
            "Dockerfile\n"
            ".dockerignore\n"
        )

    archivos = {
        ".gitignore": gitignore,
        ".gitmodules": "[submodule]\n"
    }

    project_path = Path.cwd() / name
    gitignore_path = project_path / ".gitignore"

    if gitignore_path.exists():
        print("[INFO] El proyecto git ya esta inicializado.")
        sys.exit(0)

    # Crear archivos
    for archivo, content in archivos.items():
        ruta_archivo = os.path.join(name, archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(content)

    if proccess == "init":
        tipo = "proyecto"
    elif proccess == "microservice":
        tipo = "microservicio"

    print(f"[OK] Se creo el archivo .gitignore para el {tipo} '{name}' con exito.")

    # Ejecutar comandos de git en el directorio del proyecto
    run_command("git init", cwd=project_path)
    ensure_git_identity(project_path)
    run_command("git add .", cwd=project_path)
    result = subprocess.run(
        "git status --porcelain",
        cwd=project_path,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.stdout.strip():
        run_command('git commit -m "Initial commit"', cwd=project_path)
        run_command("git branch -M main", cwd=project_path)
        print("[OK] Commit inicial.")
    else:
        print("[WARN] No hay archivos para commitear.")


    print(f"[OK] Se inicializo el repositorio git para el {tipo} '{name}' con exito.")

