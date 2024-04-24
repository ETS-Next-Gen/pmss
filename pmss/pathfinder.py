'''
Utility functions to help find settings files in standard system
paths.
'''

import os.path
import pkg_resources
import types
import sys


def system_config_file(name):
    paths = [
        f"/etc/{name}",
        f"/usr/local/etc/{name}",
        f"/opt/etc/{name}",
    ]
    for path in paths:
        if os.path.isfile(path):
            return path
    return None


def user_config_file(name):
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, f".{name}")


def cwd_config_file(name):
    return os.path.join(os.getcwd(), name)


def source_config_file(name):
    if getattr(sys, 'frozen', False):
        # Running as a compiled executable
        base = os.path.dirname(sys.executable)
    elif '__file__' in globals():
        # Running from a script
        base = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
    else:
        # Running interactively. To do: Which of these three options makes sense?
        return None
        # return local_config_file(name)
        # raise ValueError("Interactive mode / ...")

    return os.path.join(base, name)


def package_config_file(package, name):
    if isinstance(package, types.ModuleType):
        package = package.__name__
    if not isinstance(package, str):
        raise ValueError("Package {package} is not a module or a string")
        # Or maybe: return None

    return pkg_resources.resource_filename(package, name)


if __name__ == "__main__":
    print("System Config File:")
    print(system_config_file("system.pmss"))
    print
    print("User Config File:")
    print(user_config_file("user"))
    print
    print("Current Working Directory Config File:")
    print(cwd_config_file("cwd.pmss"))
    print
    print("Source Relative Config File:")
    print(source_config_file("source.pmss"))
    print
    print("ply Package Config File:")
    print(package_config_file("ply", "package.pmss"))
