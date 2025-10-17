import importlib
import logging

from fastapi import FastAPI
from faststream.rabbit import RabbitBroker

from cattle_grid.model.extension import MethodInformationModel
from cattle_grid.extensions import Extension

from .transformer import build_transformer
from .lookup import build_lookup
from .lifespan import lifespan_from_extensions

logger = logging.getLogger(__name__)

__all__ = [
    "load_extension",
    "load_extensions",
    "set_globals",
    "lifespan_from_extensions",
    "add_routers_to_broker",
    "add_routes_to_api",
    "collect_method_information",
    "build_transformer",
    "build_lookup",
]


def load_extension(extension_information: dict) -> Extension:
    """Loads a single extension"""
    module_name = extension_information.get("module")

    if module_name is None:
        raise ValueError("module is required")

    module = importlib.import_module(module_name)
    extension = module.extension
    extension.configure(extension_information.get("config", {}))

    if extension.description is None and module.__doc__ is not None:
        extension.description = module.__doc__

    if "lookup_order" in extension_information:
        extension.lookup_order = extension_information["lookup_order"]
    if "api_prefix" in extension_information:
        extension.api_prefix = extension_information["api_prefix"]

    return extension


def load_extensions(settings) -> list[Extension]:
    """Loads the extensions from settings"""

    extensions = [
        load_extension(extension_information)
        for extension_information in settings.extensions
    ]

    logger.info("Loaded extensions: %s", ", ".join(f"'{e.name}'" for e in extensions))

    return extensions


def set_globals(extensions: list[Extension]):
    """Sets global variables in cattle_grid.dependencies"""
    from cattle_grid.dependencies.globals import global_container

    global_container.transformer = build_transformer(extensions)
    global_container.lookup = build_lookup(extensions)

    for extension in extensions:
        if extension.rewrite_group_name:
            if not global_container._rewrite_rules:
                raise Exception("Rewrite rules not loaded yet")
            global_container._rewrite_rules.add_rules(
                extension.rewrite_group_name, extension.rewrite_rules
            )


def add_routers_to_broker(broker: RabbitBroker, extensions: list[Extension]):
    """Adds the routers to the broker"""

    for extension in extensions:
        if extension.activity_router:
            broker.include_router(extension.activity_router)


def add_routes_to_api(app: FastAPI, extensions: list[Extension]):
    """Adds the routes to the api"""
    for extension in extensions:
        if extension.api_router:
            if extension.api_prefix:
                app.include_router(extension.api_router, prefix=extension.api_prefix)


def collect_method_information(
    extensions: list[Extension],
) -> list[MethodInformationModel]:
    """Collects the method information from the extensions"""
    return sum((extension.method_information for extension in extensions), [])
