from subprocess import run

def poetry_publish(token=None):
    if token:
        run(f"poetry config pypi-token.pypi {token}", shell=True)
    run("poetry build", shell=True)
    run("poetry publish", shell=True)
