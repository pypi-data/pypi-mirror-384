__all__ = [
    "camelcase",
    "is_prefixed",
    "is_suffixed",
    "lowercase",
    "pascalcase",
    "removeprefix",
    "removesuffix",
    "snakecase",
    "spinalcase",
    "uppercase",
]


from dataclasses_json import stringcase


def is_prefixed(value: str, prefix: str) -> bool:
    return value[: len(prefix)] == prefix


def is_suffixed(value: str, suffix: str) -> bool:
    return value[-len(suffix) :] == suffix


def removeprefix(value: str, prefix: str) -> str:
    return value.removeprefix(prefix)


def removesuffix(value: str, suffix: str) -> str:
    return value.removesuffix(suffix)


camelcase = stringcase.camelcase
spinalcase = stringcase.spinalcase
snakecase = stringcase.snakecase
pascalcase = stringcase.pascalcase


def lowercase(value: str) -> str:
    return value.lower()


def uppercase(value: str) -> str:
    return value.upper()
