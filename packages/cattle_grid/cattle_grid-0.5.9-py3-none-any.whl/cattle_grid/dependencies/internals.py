from typing import Annotated, Awaitable, Callable

from fast_depends import Depends
from faststream import Context
from faststream.rabbit import RabbitExchange

from cattle_grid.config.rewrite import RewriteConfiguration
from cattle_grid.model.extension import MethodInformationModel
from cattle_grid.model.lookup import LookupMethod
from .globals import (
    get_transformer,
    get_lookup,
    global_container,
    get_method_information,
)


Transformer = Annotated[Callable[..., Awaitable[dict]], Depends(get_transformer)]
"""The transformer loaded from extensions"""

LookupAnnotation = Annotated[LookupMethod, Depends(get_lookup)]
"""The lookup method loaded from extensions"""


InternalExchange = Annotated[
    RabbitExchange, Depends(global_container.get_internal_exchange)
]
"""The interal activity exchange"""

CorrelationId = Annotated[str, Context("message.correlation_id")]
"""The correlation id of the message"""

MethodInformation = Annotated[
    list[MethodInformationModel], Depends(get_method_information)
]
"""Returns the information about the methods that are a part of the exchange"""


RewriteRules = Annotated[
    RewriteConfiguration, Depends(global_container.get_rewrite_rules)
]
"""Rewturns the rewrite configuration"""
