import sys

argv = sys.argv[1:]
argv_iter = iter(argv)


def iinput(*args, **kwargs):
    """
    iinput()
    iinput("pesan")
    iinput("pesan", default)
    iinput(msg="...", default="...")
    iinput(default="...")
    """
    global argv_iter
    k = {}

    try:
        _next = next(argv_iter)
        if _next != "_":
            return _next
        k["_"] = True
    except Exception:
        pass


    def get_args(indeks):
        try:
            return args[indeks]
        except Exception:
            raise

    def get_kwargs(key, indeks):
        if key in kwargs:
            return kwargs[key]
        return get_args(indeks)

    try:
        k["msg"] = get_kwargs("msg", 0)
    except Exception:
        pass

    try:
        k["default"] = get_kwargs("default", 1)
    except Exception:
        pass

    use_default = "_" in k
    no_msg = "msg" not in k
    no_default = "default" not in k
    has_msg = "msg" in k
    has_default = "default" in k

    if use_default and has_default:
        return k["default"]

    if has_default and no_msg:
        return k["default"]

    if has_msg and no_default:
        return input(k["msg"])

    if has_msg and has_default:
        return input(k["msg"]) or k["default"]
