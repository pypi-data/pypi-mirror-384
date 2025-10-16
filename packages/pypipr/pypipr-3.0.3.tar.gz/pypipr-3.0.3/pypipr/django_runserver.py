from queue import Queue
from subprocess import run

from .RunParallel import RunParallel


def collectstatic():
    run("python manage.py collectstatic --noinput", shell=True)


def makemigrations():
    run("python manage.py makemigrations", shell=True)


def migrate():
    run("python manage.py migrate", shell=True)


def runserver():
    run("python -Wa manage.py runserver 0.0.0.0:8080", shell=True)


class RP(RunParallel):
    def static_update(self, result: dict, q: Queue):
        collectstatic()

    def database_update(self, result: dict, q: Queue):
        makemigrations()
        migrate()


def django_runserver():
    try:
        RP().run_multi_threading()
        runserver()
    except KeyboardInterrupt:
        pass
