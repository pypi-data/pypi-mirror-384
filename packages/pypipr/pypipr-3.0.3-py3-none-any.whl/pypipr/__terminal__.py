import inspect
import pprint
import colorama
import pypipr


def input_parameter(o):
    try:
        return eval(o)
    except Exception:
        return o



def main(module="pypipr"):
    module = __import__(module)
    m = pypipr.ivars(module)
    m = m.get("module", {}) | m.get("variable", {}) | m.get("class", {}) | m.get("function", {})
    # m = m["variable"] | m["function"]
    m = [x for x in m]
    m.sort()

    a = pypipr.iargv(1)
    p = "Masukan Nomor Urut atau Nama Fungsi : "
    m = pypipr.choices(daftar=m, contains=a, prompt=p)

    f = getattr(module, m)

    if a != m:
        pypipr.print_colorize(m)
        print(f.__doc__)


    if inspect.isclass(f):
        pypipr.print_colorize("Class tidak dapat dijalankan.")
    elif inspect.ismodule(f):
        pypipr.print_colorize("Module tidak dapat dijalankan.")
        main(f.__name__)
        return
    elif inspect.isfunction(f):
        s = inspect.signature(f)

        if not a:
            print(m, end="")
            pypipr.print_colorize(s)

        k = {}
        for i, v in s.parameters.items():
            o = input(f"{i} [{v.default}] : ")
            if len(o):
                try:
                    k[i] = input_parameter(o)
                except Exception:
                    pypipr.print_colorize(
                        "Input harus dalam syntax python.",
                        color=colorama.Fore.RED,
                    )

        f = f(**k)

    else:
        # variable
        pass

    # pypipr.iprint(f)
    pprint.pprint(f)


if __name__ == "__main__":
    main()
