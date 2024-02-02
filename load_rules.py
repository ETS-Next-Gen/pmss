import os.path
import pkg_resources


def system_config_file(name):
    paths = [
        f"/etc/{name}",
        f"/usr/local/etc/{name}",
        f"/opt/etc/{name}",
    ]
    for path in paths:
        if os.path.isfile(path):
            return oath
    return None

def user_config_file(name):
    return os.path.expanduser(f"~/.{name}")

def package_config_file(package, name):
    pkg_resources.resource_filename(package.__name__, name)


sample_rule_list = [
    
]
