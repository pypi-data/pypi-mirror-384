"""Auto-discovery of endpoint modules"""
import pkgutil
import importlib
from typing import Dict, Type
from .base import Endpoint

# Dictionary to store discovered endpoints
registry: Dict[str, Type[Endpoint]] = {}


def discover_endpoints():
    """Discover and register all endpoint modules"""
    # Import all modules in this package
    for _, name, _ in pkgutil.iter_modules(__path__):
        if name != "base":  # Skip the base module
            importlib.import_module(f".{name}", __package__)
    
    return registry


def register_endpoint(endpoint_class: Type[Endpoint]):
    """Register an endpoint class"""
    registry[endpoint_class.name] = endpoint_class
    return endpoint_class