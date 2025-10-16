import os
import shutil


def django_clear_migrations(appname):
    migrations_path = os.path.join(appname, "migrations")
    if os.path.exists(migrations_path):
        shutil.rmtree(migrations_path)
    os.makedirs(migrations_path)
    open(os.path.join(migrations_path, "__init__.py"), "w").close()
