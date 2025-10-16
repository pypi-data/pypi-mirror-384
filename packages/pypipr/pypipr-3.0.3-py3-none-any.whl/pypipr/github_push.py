from subprocess import run

from .print_colorize import print_colorize


def github_push(commit_msg=None):
    def console_input(prompt, default):
        print_colorize(prompt, text_end="")
        if default:
            print(default)
            return default
        return input()

    run("git status", shell=True)
    msg = console_input("Commit Message if any or empty to exit : ", commit_msg)
    if msg:
        run("git add .", shell=True)
        run(f'git commit -m "{msg}"', shell=True)
        run("git push", shell=True)
