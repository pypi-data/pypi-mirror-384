from typing import Annotated

from pydantic import AfterValidator


def at_least_one_element(value: list) -> list:
    if len(value) == 0:
        raise ValueError("List must contain at least one value")
    return value


ListOfStringsWithAtLeastOneElement = Annotated[
    list[str], AfterValidator(at_least_one_element)
]
