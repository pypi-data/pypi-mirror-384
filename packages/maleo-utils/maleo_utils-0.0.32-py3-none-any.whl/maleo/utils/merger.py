from collections.abc import Mapping
from typing import Union
from maleo.types.dict import StrToAnyDict
from maleo.types.mapping import StrToAnyMapping


def merge_dicts(*obj: StrToAnyDict) -> StrToAnyDict:
    def _merge(
        a: Union[StrToAnyDict, StrToAnyMapping],
        b: Union[StrToAnyDict, StrToAnyMapping],
    ) -> StrToAnyDict:
        result = dict(a)  # create a mutable copy
        for key, value in b.items():
            if (
                key in result
                and isinstance(result[key], Mapping)
                and isinstance(value, Mapping)
            ):
                result[key] = _merge(result[key], value)
            else:
                result[key] = value
        return result

    merged: StrToAnyDict = {}
    for ob in obj:
        merged = _merge(merged, ob)
    return merged
