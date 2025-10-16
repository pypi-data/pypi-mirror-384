"""Custom entity schema that holds entities of a specific type (e.g. files)"""


def type_uri(suffix: str) -> str:
    """Create a new entity schema type URI."""
    return "https://vocab.eccenca.com/di/entity/" + suffix


def path_uri(suffix: str) -> str:
    """Create a new entity schema path."""
    return "https://vocab.eccenca.com/di/entity/" + suffix


def instance_uri(suffix: str) -> str:
    """Create a new typed entity instance URI"""
    return "https://eccenca.com/di/entity/" + suffix
