import os


def get(name: str) -> str:
    """Return environment variable value for key.

    This is a convenience function for getting a secret value from the environment,
    for legacy Databutton apps that use db.secrets.get(name) to get a secret value.

    You should replace this with os.environ[name] in your app.
    """
    print(
        "WARNING: db.secrets.get(name) is deprecated. Please use os.environ.get(name) instead."
    )
    return os.environ[name]
