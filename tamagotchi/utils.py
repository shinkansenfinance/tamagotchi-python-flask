import os


def required_env(key):
    if key not in os.environ:
        raise RuntimeError(f"Required {key} variable not present in environment")
    return os.environ[key]
