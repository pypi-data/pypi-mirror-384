from subprocess import run

from .input_char import input_char


def github_init():
    """
    Menyiapkan folder offline untuk dikoneksikan ke repository
    kosong github.
    Akan langsung di upload dan di taruh di branch main.


    ```py
    github_init()
    ```

    or run in terminal

    ```py
    pypipr github_init
    ```
    """
    u = input("username : ")
    p = input("password : ")
    g = input("github account name : ")
    r = input("repository name : ")

    url = f"https://{u}:{p}@github.com/{g}/{r}.git"
    if input_char(f"Apakah benar {url} ? [y] ") == "y":
        run("git init", shell=True)
        run("git add .", shell=True)
        run("git commit -m first_commit", shell=True)
        run("git branch -M main", shell=True)
        run(f"git remote add origin {url}", shell=True)
        run("git push -u origin main", shell=True)
