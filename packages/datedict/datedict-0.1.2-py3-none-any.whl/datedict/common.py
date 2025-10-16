from decimal import Decimal


ZERO = Decimal("0")


def to_decimal(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, str)):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(str(x))
    raise TypeError(f"Unsupported type for Decimal: {type(x)}")
