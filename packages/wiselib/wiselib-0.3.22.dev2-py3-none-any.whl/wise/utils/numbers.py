from decimal import Decimal, ROUND_HALF_EVEN
from typing import Iterable, Any

EPSILON4 = 1e-1
EPSILON5 = 1e-5
EPSILON6 = 1e-6
EPSILON7 = 1e-7
EPSILON8 = 1e-8
EPSILON9 = 1e-9
EPSILON10 = 1e-10

EPSILON = EPSILON6


def to_decimal(value: float | int | str | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def is_zero(value: float | Decimal, eps: float | Decimal = EPSILON) -> bool:
    return safe_abs(to_decimal(value)) < to_decimal(eps)


def safe_sum(col: Iterable[float | Decimal]) -> float:
    return float(sum([to_decimal(x) for x in col], Decimal(0)))


def safe_prod(col: Iterable[float | Decimal]) -> float:
    d = Decimal("1")
    for item in col:
        d *= to_decimal(item)
    return float(d)


def safe_add(a: float | Decimal, b: float | Decimal) -> float:
    return float(to_decimal(a) + to_decimal(b))


def safe_sub(a: float | Decimal, b: float | Decimal) -> float:
    return float(to_decimal(a) - to_decimal(b))


def safe_mult(a: float | Decimal, b: float | Decimal) -> float:
    return float(to_decimal(a) * to_decimal(b))


def safe_div(a: float | Decimal, b: float | Decimal) -> float:
    return float(to_decimal(a) / to_decimal(b))


def safe_abs(a: float | Decimal) -> float:
    return float(abs(to_decimal(a)))


def safe_eq(
    a: float | Decimal, b: float | Decimal, eps: float | Decimal = EPSILON
) -> bool:
    return is_zero(safe_sub(a, b), eps=eps)


def safe_ne(
    a: float | Decimal, b: float | Decimal, eps: float | Decimal = EPSILON
) -> bool:
    return not safe_eq(a, b, eps=eps)


def safe_gt(
    a: float | Decimal, b: float | Decimal, eps: float | Decimal = EPSILON
) -> bool:
    return safe_sub(a, b) > to_decimal(eps)


def safe_lt(
    a: float | Decimal, b: float | Decimal, eps: float | Decimal = EPSILON
) -> bool:
    return safe_sub(a, b) < -to_decimal(eps)


def safe_gte(
    a: float | Decimal, b: float | Decimal, eps: float | Decimal = EPSILON
) -> bool:
    return safe_sub(a, b) >= -to_decimal(eps)


def safe_lte(
    a: float | Decimal, b: float | Decimal, eps: float | Decimal = EPSILON
) -> bool:
    return safe_sub(a, b) <= to_decimal(eps)


def safe_max(a: float | Decimal, b: float | Decimal) -> float:
    return float(max(to_decimal(a), to_decimal(b)))


def safe_min(a: float | Decimal, b: float | Decimal) -> float:
    return float(min(to_decimal(a), to_decimal(b)))


def format_decimal(
    v: float | int | str | Decimal,
    decimals: int,
    *,
    rounding: str = ROUND_HALF_EVEN,
    normalize: bool = True,
) -> str:
    f = to_decimal(v).quantize(Decimal(f"1e-{decimals}"), rounding=rounding)
    if normalize:
        f = f.normalize()
    return format(f, "f")


def smart_format_decimal(
    v: float | int | str | Decimal,
    decimals: int,
    **kwargs: Any,
) -> str:
    """
    Format a decimal number in a context-aware way.
    Formats small numbers like 0.0000123456 with `decimals` digits after the leading zeros.
    For example with decimals=3, this would be 0.0000123, not 0 (what 'format_decimal' would yield).
    """
    d = to_decimal(v)
    s = format(d, "f")
    if not s.startswith("0."):
        return format_decimal(d, decimals, **kwargs)

    fractional_part = s.split(".")[1]
    zero_count = len(fractional_part) - len(fractional_part.lstrip("0"))
    return format_decimal(d, zero_count + decimals, **kwargs)
