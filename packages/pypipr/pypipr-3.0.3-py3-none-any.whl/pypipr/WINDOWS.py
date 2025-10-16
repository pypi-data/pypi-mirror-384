import platform

"""
True on windows
"""
WINDOWS = platform.system() == "Windows"


def test():
    print(WINDOWS)
