from .print_colorize import print_colorize



def log(text=None):
    """
    Decorator untuk mempermudah pembuatan log karena tidak perlu mengubah
    fungsi yg sudah ada.
    Melakukan print ke console untuk menginformasikan proses yg sedang
    berjalan didalam program.

    ```py
    @log
    def some_function():
        pass

    @log()
    def some_function_again():
        pass

    @log("Calling some function")
    def some_function_more():
        pass

    some_function()
    some_function_again()
    some_function_more()
    ```
    """

    def inner_log(func=None):
        def callable_func(*args, **kwargs):
            main_function(text)
            result = func(*args, **kwargs)
            return result

        def main_function(param):
            print_colorize(param)

        if func is None:
            return main_function(text)
        return callable_func

    if text is None:
        return inner_log
    elif callable(text):
        return inner_log(text)
    else:
        # inner_log(None)
        return inner_log
