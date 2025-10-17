from typing import List

from fast_depends import inject

from cattle_grid.extensions import Extension
from cattle_grid.model.lookup import LookupMethod, Lookup


def ordered_lookups(extensions: List[Extension]) -> List[LookupMethod]:
    """Returns a list of LookupMethod ordered by lookup order"""
    sorted_extensions = sorted(
        extensions, key=lambda extension: extension.lookup_order or 0, reverse=True
    )

    return [
        extension.lookup_method
        for extension in sorted_extensions
        if extension.lookup_method
    ]


def build_lookup(extensions: list[Extension]) -> LookupMethod:
    """Builds the lookup method"""
    methods = ordered_lookups(extensions)

    async def lookup_result(lookup: Lookup) -> Lookup:
        for method in methods:
            lookup = await inject(method)(lookup)
            if lookup.result is not None:
                return lookup
        return lookup

    return lookup_result
