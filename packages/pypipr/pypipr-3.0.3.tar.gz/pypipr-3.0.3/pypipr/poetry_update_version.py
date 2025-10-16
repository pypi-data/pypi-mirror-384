from subprocess import run


def poetry_update_version(major=False, minor=False, patch=False):
    if major:
        run("poetry version major", shell=True)
    if minor:
        run("poetry version minor", shell=True)
    if patch:
        run("poetry version patch", shell=True)
