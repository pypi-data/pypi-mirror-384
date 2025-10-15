from importlib.metadata import version


def get_package_version(package):
    return version(package)
