from subprocess import run


def github_user(email=None, name=None):
    """
    Menyimpan email dan nama user secara global sehingga tidak perlu
    menginput nya setiap saat.

    ```py
    github_user('my@emil.com', 'MyName')
    ```
    """
    if email:
        run(f"git config --global user.email {email}", shell=True)
    if name:
        run(f"git config --global user.name {name}", shell=True)
