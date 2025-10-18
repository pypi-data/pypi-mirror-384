def __get_version():
    import importlib.metadata

    try:
        return importlib.metadata.version(__name__)
    except Exception:
        return None


__version__ = __get_version()


del __get_version


def main():
    print("Hello from CodeAPI!")
