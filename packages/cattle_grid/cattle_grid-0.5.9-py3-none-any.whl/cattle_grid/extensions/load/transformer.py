from collections.abc import Callable, Awaitable

from fast_depends import inject
from cattle_grid.extensions import Extension
from .types import Transformer


def resolvable_transformers(transformers: set[Transformer], available_fields: set[str]):
    """
    Determines the set of resolvable transformers based on the available fields.

    """
    return {
        transformer
        for transformer in transformers
        if transformer.inputs.issubset(available_fields)
    }


def get_transformers(extensions: list[Extension]) -> set[Transformer]:
    result = set()

    for extension in extensions:
        if extension.transformer:
            if not extension.transformer_inputs or not extension.transformer_outputs:
                raise ValueError(
                    "transformer_inputs and transformer_outputs are required when transformer is set"
                )

            result.add(
                Transformer(
                    name=extension.name,
                    transformer=extension.transformer,
                    inputs=set(extension.transformer_inputs),
                    outputs=set(extension.transformer_outputs),
                )
            )

    return result


def transformation_steps(transformers: set[Transformer]) -> list[set[Transformer]]:
    to_process = transformers.copy()
    steps = []

    available_fields = {"raw"}

    while len(to_process) > 0:
        resolvable = resolvable_transformers(to_process, available_fields)

        if len(resolvable) == 0:
            raise Exception("Could not resolve plugins")
        steps.append(resolvable)
        for x in resolvable:
            available_fields = available_fields | x.outputs
        to_process = to_process - resolvable

    return steps


def build_transformer(extensions: list[Extension]) -> Callable[[dict], Awaitable[dict]]:
    """Builds the transformer"""
    transformers = get_transformers(extensions)
    steps = transformation_steps(transformers)

    async def transformer(data: dict, **kwargs):
        for step in steps:
            for plugin in step:
                data.update(await inject(plugin.transformer)(data=data, **kwargs))  # type: ignore

        return data

    return transformer
