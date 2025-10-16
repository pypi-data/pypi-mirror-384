
def modify(name, microservice=None):

    if microservice is not None:
        main_file = f"{microservice}/app/main.py"
    else:
        main_file = "app/main.py"
        
    pascal_case = ''.join(word.capitalize() for word in name.split('_'))
    
    import_line = f"from app.{name}.infrastructure.routers.{name}_router import router as {name}_router\n"
    router_line = f"run.include_router({name}_router, prefix=\"/api/v1\", tags=[\"{pascal_case}\"])\n"

    # Leer contenido actual
    with open(main_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Verificar si ya existe
    if import_line in lines and router_line in lines:
        print("[INFO] Las líneas ya están en main.py")
    else:
        # === 1. Insertar IMPORT si no existe ===
        if import_line not in lines:
            import_indices = [i for i, line in enumerate(lines) if line.startswith("import") or line.startswith("from")]
            last_import_idx = import_indices[-1] if import_indices else 0
            lines.insert(last_import_idx + 2, import_line + "\n")

        # === 2. Insertar include_router en el lugar correcto ===
        # Buscar todas las líneas que incluyen run.include_router
        router_indices = [i for i, line in enumerate(lines) if "run.include_router" in line]

        if router_indices:
            # Insertar justo después del último include_router
            last_router_idx = router_indices[-1]
            if router_line not in lines:
                lines.insert(last_router_idx + 1, router_line)
        else:
             # Si no hay ningún run.include_router, insertar al final del archivo
            if not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append("\n" + router_line)

        # Guardar archivo actualizado
        with open(main_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print("[OK] main.py actualizado exitosamente.")