import logging
from typing import Callable, Dict, Awaitable, List, Annotated, Any
from dataclasses import dataclass, field
from contextlib import AbstractAsyncContextManager

from pydantic import BaseModel
from fast_depends import Depends

from faststream.rabbit import RabbitRouter, RabbitRoute
from fastapi import APIRouter, Depends as FastAPIDepends

from cattle_grid.model.lookup import Lookup
from cattle_grid.model.extension import MethodInformationModel
from cattle_grid.dependencies.globals import global_container

from .util import skip_method_information, rabbit_queue_for_name_and_routing_key

logger = logging.getLogger(__name__)


class BaseConfig(BaseModel): ...


@dataclass
class Extension:
    """Data model for an extension"""

    name: str
    """name of the extension, must be unique"""

    module: str
    """module the extension is defined in, should be set to `__name__`"""

    description: str | None = field(
        default=None,
        metadata={
            "description": "description of the extension. If not set is populated from the docstring of the extension"
        },
    )

    rewrite_group_name: str | None = field(
        default=None,
        metadata={"description": "group name this extensions' rewrite rules apply to"},
    )
    rewrite_rules: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "description": "rewrite rules, for these to take effect the rewrite_group_name has to be set"
        },
    )

    lifespan: Callable[[Any], AbstractAsyncContextManager[None]] | None = None
    """The lifespan function"""

    config_class: Any = BaseConfig
    """Expected configuration class"""

    Config: Any | None = None
    """Annotation to retrieve the configuration, e.g.

    ```python
    @extension.lookup()
    async def lookup(
        lookup: Lookup, config: extension.Config
    ) -> Lookup: ...
    ```
    """
    ConfigFastAPI: Any | None = field(
        default=None,
        metadata={
            "description": """Annotation to retrieve the configuration using FastAPI Depends"""
        },
    )

    configuration: Any | None = None

    api_router: APIRouter = field(
        default_factory=APIRouter, metadata={"description": "API router"}
    )
    api_prefix: str = ""

    transformer: Callable[[Dict], Awaitable[Dict]] | None = None
    transformer_inputs: List[str] | None = None
    transformer_outputs: List[str] | None = None

    lookup_method: Callable[[Lookup], Awaitable[Lookup]] | None = None
    lookup_order: int | None = None

    method_information: List[MethodInformationModel] = field(default_factory=list)

    _rabbit_routes: list[RabbitRoute] = field(default_factory=list)

    def __post_init__(self):
        def get_config():
            return self.configuration

        self.Config = Annotated[self.config_class, Depends(get_config)]
        self.ConfigFastAPI = Annotated[self.config_class, FastAPIDepends(get_config)]

    @property
    def activity_router(self) -> RabbitRouter | None:
        if len(self._rabbit_routes) == 0:
            return None
        return RabbitRouter(handlers=self._rabbit_routes)

    def configure(self, config: dict):
        """Configures the extension

        The configuration is validated using the config_class.
        """
        self.configuration = self.config_class.model_validate(config)

    def transform(self, inputs: List[str] = [], outputs: List[str] = []):
        """Allows building the extension via decorator. Usage:

        ```python
        extension = Extension("my extension")

        @extension.transform(inputs=["inputs"], outputs=["outputs"])
        async def transformer(a: dict):
            ...
        ```
        """
        if self.transformer:
            raise ValueError("You should not override an existing transformer")

        def inner(func):
            self.transformer = func
            self.transformer_inputs = inputs
            self.transformer_outputs = outputs

            return func

        return inner

    def subscribe(
        self, routing_key: str, description: str | None = None, replies: bool = False
    ):
        """Allows building the extension via decorator.

        ```python
        extension = Extension("my extension")

        @extension.subscribe("routing_key")
        async def subscriber(message: dict): ...
        ```

        Dependency injection is available for the subscriber function.
        """

        def inner(func):
            if description is None:
                function_description = func.__doc__
            else:
                function_description = description

            self._rabbit_routes.append(
                RabbitRoute(
                    func,
                    queue=rabbit_queue_for_name_and_routing_key(self.name, routing_key),
                    exchange=global_container.exchange,
                    title=routing_key,
                )
            )

            if not skip_method_information(routing_key):
                self.method_information.append(
                    MethodInformationModel(
                        module=self.module,
                        routing_key=routing_key,
                        description=function_description,
                        replies=replies,
                    )
                )

            return func

        return inner

    def subscribe_on_account_exchange(self, routing_key: str):
        """Allows building the extension via decorator.

        Dependency injection is available for the subscriber function.
        """

        def inner(func):
            self._rabbit_routes.append(
                RabbitRoute(
                    func,
                    queue=rabbit_queue_for_name_and_routing_key(self.name, routing_key),
                    exchange=global_container.account_exchange,
                    title=routing_key,
                )
            )

            return func

        return inner

    def lookup(self):
        """Allows building the extension via decorator.

        ```python
        extension = Extension("my extension")

        @extension.lookup()
        async def lookup(l: Lookup) -> Lookup:
            ...
        ```
        Dependency injection is available for the lookup function.
        """

        def inner(func):
            self.lookup_method = func
            return func

        return inner

    def get(self, path, **kwargs):
        """Allows one to add a get endpoint to the API Router
        of the extension

        Usage:

        ```python
        @extension.get("/path")
        async def get_endpoint():
            pass

        ```
        """

        def inner(func):
            self.api_router.get(path, **kwargs)(func)
            return func

        return inner

    def post(self, path, **kwargs):
        """Allows one to add a post endpoint to the API Router
        of the extension

        Usage:

        ```python
        @extension.post("/path")
        async def post_endpoint():
            pass

        ```
        """

        def inner(func):
            self.api_router.post(path, **kwargs)(func)
            return func

        return inner

    def include_router(self, router: APIRouter, **kwargs):
        """Includes the router as an api router"""

        self.api_router.include_router(router, **kwargs)
