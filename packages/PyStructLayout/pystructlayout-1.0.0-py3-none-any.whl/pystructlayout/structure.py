from struct import unpack
from typing import Protocol
import re


def _parse_format(fmt: str) -> list[str]:
    """Expand format specifiers like 4I -> ['I','I','I','I'], but keep 4s as ['4s']"""
    tokens = re.findall(r'(\d*[A-Za-z?])', fmt)
    result = []
    for token in tokens:
        m = re.match(r'(\d*)([A-Za-z?])', token)
        count, code = m.groups()
        count = int(count or 1)
        if code == 's':  # keep '4s' together
            result.append(token)
        else:
            result.extend([code] * count)
    return result


def struct():
    def decorator(cls):
        if not hasattr(cls, "format"):
            raise TypeError(f"{cls.__name__}: error: missing type specifier")

        fmt = getattr(cls, "format")
        if fmt[0] in "<>@=!" :
            fmt = fmt[1:]  # skip endianness symbol

        c_types = _parse_format(fmt)
        hints = getattr(cls, "__annotations__", {})

        if len(c_types) != len(hints):
            raise TypeError(
                f"{cls.__name__}: error: field count ({len(hints)}) "
                f"does not match format specifiers ({len(c_types)})"
            )

        for i, (name, expected) in enumerate(hints.items()):
            if name in cls.__dict__:
                raise TypeError(
                    f"{cls.__name__}: error: initializer is not a constant for field '{name}'"
                )

            c = c_types[i]
            if expected is int:
                if not re.match(r'^\d*[IiLlQqHh]$', c):
                    raise TypeError(f"{cls.__name__}: error: incompatible types for field '{name}' (expected int)")
            elif expected in (bytes, bytearray):
                if not re.match(r'^\d*s$', c) and c not in 'Bb':
                    raise TypeError(f"{cls.__name__}: error: incompatible types for field '{name}' (expected bytes)")
            elif expected is float:
                if c not in 'fd':
                    raise TypeError(f"{cls.__name__}: error: incompatible types for field '{name}' (expected float)")
            elif expected is bool:
                if c != '?':
                    raise TypeError(f"{cls.__name__}: error: incompatible types for field '{name}' (expected bool)")
            else:
                raise TypeError(f"{cls.__name__}: error: unsupported field type '{expected.__name__}'")

        # Dynamically create an __init__ method
        field_names = list(hints.keys())

        def __init__(self, *args):
            if len(args) != len(field_names):
                raise TypeError(f"{cls.__name__}() takes {len(field_names)} arguments but {len(args)} were given")
            for name, value in zip(field_names, args):
                setattr(self, name, value)

        setattr(cls, "__init__", __init__)
        return cls

    return decorator


class Struct(Protocol):
    format: str = ...


def cast(struct: type[Struct], raw: bytes | bytearray) -> Struct:
    data = unpack(struct.format, raw)
    return struct(*data)