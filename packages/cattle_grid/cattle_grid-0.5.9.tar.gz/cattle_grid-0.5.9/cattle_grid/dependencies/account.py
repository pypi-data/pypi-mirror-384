from typing import Annotated

from fast_depends import Depends
from cattle_grid.dependencies.processing import RoutingKey


def name_from_routing_key(
    routing_key: RoutingKey,
) -> str:
    """
    ```pycon
    >>> name_from_routing_key("receiving.alice")
    'alice'

    >>> name_from_routing_key("receiving.alice.action.fetch")
    'alice'

    ```
    """
    return routing_key.split(".")[1]


AccountName = Annotated[str, Depends(name_from_routing_key)]
"""Assigns the account name extracted from the routing key"""
