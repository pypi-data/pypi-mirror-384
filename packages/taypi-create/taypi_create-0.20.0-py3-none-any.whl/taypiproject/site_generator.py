import os

def create(name):
    archivos = {
        f"{name}.conf" : (
            "server {\n"
        "    #listen 443 ssl;\n"
        "    listen 80;\n"
        f"    server_name {name}.app;\n"
        "    #ssl_certificate /etc/nginx/ssl/certificate.crt; # managed by Certbot\n"
        "    #ssl_certificate_key /etc/nginx/ssl/private.key; #\n"
        "\n"
        "    location / {\n"
        f"        proxy_pass http://{name}:5000;\n"
        "        proxy_set_header Host $host;\n"
        "        proxy_set_header X-Real-IP $remote_addr;\n"
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
        "        proxy_set_header X-Forwarded-Proto $scheme;\n"
        "    }\n"
        "}\n"
        )
    }

    # Crear archivos vacíos
    for archivo, content in archivos.items():
        ruta_archivo = os.path.join('nginx/sites', archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[OK] Se configuro el DNS '{name}.app' agregalo en el archivo host del sistema.")