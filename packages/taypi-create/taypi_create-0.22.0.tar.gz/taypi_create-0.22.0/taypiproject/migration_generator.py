from datetime import datetime
import inflection
import uuid
import os
import re

def create(name, microservice = None):

    revision_id = uuid.uuid4().hex[:12]
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    nametimestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    
    # Si existe el microservicio crea el path de la migración dentro del microservicio
    if microservice is not None:
        path = f"{microservice}/database/migrations"
    else:
        path = "database/migrations"
        
    
    down_revision = get_last_revision_id(path)
    down_revision_value = f"'{down_revision}'" if down_revision is not None else "None"
    
    archivos = {
        f"database/migrations/{nametimestamp}_{revision_id}_create_{name}_table.py":(
            f"\"\"\"create {inflection.pluralize(name)} table\n"
            "\n"
            f"Revision ID: {revision_id}\n"
            "Revises:\n"
            f"Create Date: {timestamp}\n"
            "\n"
            "\"\"\"\n"
            "from typing import Sequence, Union\n"
            "\n"
            "from alembic import op\n"
            "import sqlalchemy as sa\n"
            "from sqlalchemy.dialects import postgresql\n"
            "\n"
            "# revision identifiers, used by Alembic.\n"
            f"revision: str = '{revision_id}'\n"
            f"down_revision: Union[str, None] = {down_revision_value}\n"
            "branch_labels: Union[str, Sequence[str], None] = None\n"
            "depends_on: Union[str, Sequence[str], None] = None\n"
            "\n"
            "\n"
            "def upgrade() -> None:\n"
            f"    op.create_table('{inflection.pluralize(name)}',\n"
            "    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),\n"
            "    sa.Column('example', sa.VARCHAR(), autoincrement=False, nullable=False),\n"
            "    sa.Column('active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),\n"
            "    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),\n"
            "    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),\n"
            "    sa.Column('deleted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),\n"
            f"    sa.PrimaryKeyConstraint('id', name='{inflection.pluralize(name)}_pkey')\n"
            "    )\n"
            f"    op.create_index('ix_{inflection.pluralize(name)}_example', '{inflection.pluralize(name)}', ['example'], unique=False)\n"
            "\n"
            "def downgrade() -> None:\n"
            f"    op.drop_index('ix_{inflection.pluralize(name)}_example', table_name='{inflection.pluralize(name)}')\n"
            f"    op.drop_table('{inflection.pluralize(name)}')\n"
        )
    }

    patron = re.compile(rf"_create_{name}_table")
    for nombre_archivo in os.listdir(path):
        if patron.search(nombre_archivo):
            print(f"[INFO] Ya existe una migración que crea la tabla {inflection.pluralize(name)}")
            return True

    if microservice is not None:
        path = f"{microservice}"
    else:
        path = ""

    # Crear archivos vacíos
    for archivo, content in archivos.items():
        ruta_archivo = os.path.join(path , archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(content)
            print(f"[OK] Se ha creado la migración {archivo} para crear la tabla {inflection.pluralize(name)}")

def get_last_revision_id(path):
    # Listar todos los archivos .py (migraciones)
    files = [f for f in os.listdir(path) if f.endswith(".py") and f != "__init__.py"]
    
    if not files:
        return None

    # Ordenar por nombre
    files.sort()
    
    last_file = os.path.join(path, files[-1])

    # Leer el contenido del archivo y buscar la línea de revision
    with open(last_file, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"revision\s*:\s*str\s*=\s*['\"]([a-f0-9]+)['\"]", content)
    if match:
        return match.group(1)

    return None