"""
Dependency injection container for SurfDataverse.
"""

from dependency_injector import containers, providers

from .core import DataverseClient, DataverseEntity, DataverseTable


class Container(containers.DeclarativeContainer):
    """Main dependency injection container for SurfDataverse"""

    # Configuration
    config = providers.Configuration()

    # Core client as singleton
    client = providers.Singleton(DataverseClient, config_path=config.config_path)

    # Table factory - creates DataverseTable instances with injected client
    table_factory = providers.Factory(DataverseTable, client=client)

    # Entity factory - creates DataverseEntity instances with injected client
    entity_factory = providers.Factory(DataverseEntity, client=client)


# Global container instance
container = Container()


def get_client(config_path=None) -> DataverseClient:
    """Get the singleton DataverseClient instance"""
    if config_path:
        container.config.config_path.from_value(config_path)
    return container.client()


def connect_table(logical_name: str = "") -> DataverseTable:
    """Connect to a Dataverse table"""
    return container.table_factory(logical_name)


def connect_entity(table_logical_name: str) -> DataverseEntity:
    """Connect to a new Dataverse entity instance"""
    return container.entity_factory(table_logical_name)


def reset_container():
    """Reset the container - useful for testing"""
    container.reset_singletons()
