from django.db import models
from django.db.models.constraints import CheckConstraint
from decimal import Decimal

from wise.utils.numbers import safe_mult

MIN_NOTIONAL_MARGIN_COEFFICIENT = 1.2
MIN_NOTIONAL_MARGIN_CONST = 5.0
DEFAULT_MIN_NOTIONAL = 0.1


def get_margined_min_notional(min_notional: float) -> float:
    return min_notional * MIN_NOTIONAL_MARGIN_COEFFICIENT + MIN_NOTIONAL_MARGIN_CONST


def is_more_than_min_notional(
    size: float, price: float | None, margined: bool = False
) -> bool:
    if price is None:
        return True
    equity = safe_mult(abs(size), price)
    threshold = (
        get_margined_min_notional(DEFAULT_MIN_NOTIONAL)
        if margined
        else DEFAULT_MIN_NOTIONAL
    )
    return equity >= threshold


def ExactlyOneNonNullConstraint(*, fields: list[str]) -> CheckConstraint:
    # Ref: https://stackoverflow.com/questions/69014785/compare-expression-with-constant-in-check-constraint
    return CheckConstraint(
        check=models.expressions.ExpressionWrapper(
            models.Q(
                models.lookups.Exact(
                    lhs=models.expressions.Func(
                        *fields,
                        function="num_nonnulls",
                        output_field=models.IntegerField(),
                    ),
                    rhs=models.Value(1),
                )
            ),
            output_field=models.BooleanField(),
        ),
        name=f"exactly_one_non_null__{'__'.join(fields)}",
    )
