"""
SurfDataverse - A Python package for Microsoft Dataverse integration

This package provides a clean, object-oriented interface for connecting to,
reading from, and writing to Microsoft Dataverse environments.

Main Components:
- DataverseClient: Authentication and connection management
- DataverseRow: Base class for entity operations
- Entity classes: Article, Recipe, Ingredient, etc.
"""

from .container import connect_entity, connect_table, container, get_client, reset_container
from .core import DataverseClient, DataverseEntity, DataverseTable, is_valid_guid
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    DataverseAPIError,
    EntityError,
    SurfDataverseError,
    ValidationError,
)

__author__ = "Friedemann Heinz"

__all__ = [
    "DataverseClient",
    "DataverseTable",
    "DataverseEntity",
    "is_valid_guid",
    "get_client",
    "connect_table",
    "connect_entity",
    "reset_container",
    "container",
    "SurfDataverseError",
    "AuthenticationError",
    "ConnectionError",
    "ConfigurationError",
    "DataverseAPIError",
    "EntityError",
    "ValidationError",
]
