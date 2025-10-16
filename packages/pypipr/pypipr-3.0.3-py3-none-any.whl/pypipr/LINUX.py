import platform

"""
True on linux
"""
LINUX = platform.system() == "Linux"

def test():
    print(LINUX)
