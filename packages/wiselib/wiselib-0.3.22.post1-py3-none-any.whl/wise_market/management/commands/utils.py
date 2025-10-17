import importlib
import os

from django.conf import settings
from django.core.management import call_command


def get_empty_migration(app_label, migration_name):
    call_command("makemigrations", app_label, "--empty", "--name", migration_name)

    migrations_dir = os.path.join(settings.BASE_DIR, app_label, "migrations")
    migration_files = sorted(
        f for f in os.listdir(migrations_dir) if f.endswith(".py") and f.startswith("0")
    )

    migration_file = os.path.join(migrations_dir, migration_files[-1])

    spec = importlib.util.spec_from_file_location("migration_module", migration_file)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)

    return migration_module.Migration, migration_file
