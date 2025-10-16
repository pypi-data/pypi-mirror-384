import contextlib
import importlib
import inspect
import io
import pathlib
import subprocess
import textwrap
import traceback
import webbrowser

import colorama

import pypipr
import settings


from tomlkit import parse, dumps
from packaging.version import Version


def build_import():
    folder = pathlib.Path("./pypipr/")
    init_file = folder / "__init__.py"
    files = [f for f in folder.rglob("*.py") if not f.name.startswith("__")]
    import_list = [f"from .{f.stem} import {f.stem}" for f in files]
    init_file.write_text("\n".join(import_list) + "\n", encoding="utf-8")


def run_test():
    def get_output(func):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                func()
        except Exception:
            traceback.print_exc(file=buf)
        return buf.getvalue()

    def func(module):
        # print(f"{module} : ", end="")
        try:
            mod = importlib.import_module(f"pypipr.{module}")
            res_func = getattr(mod, module)
            res_test = getattr(mod, "test")
            # pypipr.print_colorize("found", color=colorama.Fore.GREEN)
            res = {
                "module": mod,
                "module_name": module,
                "test_func": res_test,
                "func": res_func,
            }
        except Exception:
            # pypipr.print_colorize("not found", color=colorama.Fore.RED)
            res = None
        return res

    folder = pathlib.Path("./pypipr/")
    files = [f.stem for f in folder.rglob("*.py")]
    result = []
    for file in files:
        fungsi = func(file)
        if fungsi is not None:
            fungsi["output"] = get_output(fungsi["test_func"])
            result.append(fungsi)
    return result


def create_readme(results):
    daftar = ["# PYPIPR"]
    writes = []
    for r in results:
        f_name = r["module_name"]
        f_doc = textwrap.dedent(inspect.getdoc(r["func"]) or "")
        f_code = inspect.getsource(r["test_func"])
        f_clean_code = textwrap.dedent("\n".join(f_code.splitlines()[1:]))
        f_output = r["output"]
        
        daftar.append(f"- [{f_name}](#{f_name.lower()})")

        writes.append("")
        writes.append(f"# {f_name}")
        writes.append(f_doc)
        writes.append("")
        writes.append("example : ")
        writes.append("```python")
        writes.append(f_clean_code)
        writes.append("```")
        writes.append("")
        writes.append("result : ")
        writes.append("```shell")
        writes.append(f_output)
        writes.append("```")
        writes.append("")

    with open("readme.md", "w") as f:
        f.write("\n".join(daftar))
        f.write("\n\n")
        f.write("\n".join(writes))

def update_version(rule="patch"):
    path = "pyproject.toml"
    doc = parse(open(path, encoding="utf-8").read())
    v_old = Version(str(doc["project"]["version"]))
    v_new = {
        "major": f"{v_old.major + 1}.0.0",
        "minor": f"{v_old.major}.{v_old.minor + 1}.0",
        "patch": f"{v_old.major}.{v_old.minor}.{v_old.micro + 1}",
    }[rule]
    doc["project"]["version"] = v_new
    open(path, "w", encoding="utf-8").write(dumps(doc))
    print(str(v_old), ' -> ', v_new)
    return str(v_old), v_new

def publish_package():
    subprocess.run("git pull", shell=True)
    update_version()
    subprocess.run("flit build", shell=True)
    subprocess.run("flit publish", shell=True)
    pypipr.github_push("Publish to pypi.org")


if __name__ == "__main__":
    build_import()
    result = run_test()
    create_readme(result)
    publish_package()
