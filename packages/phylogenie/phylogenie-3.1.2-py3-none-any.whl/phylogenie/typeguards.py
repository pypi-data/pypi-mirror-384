from collections.abc import Sequence
from typing import Any, TypeGuard

import phylogenie.typings as pgt


def is_many(x: Any) -> TypeGuard[pgt.Many[Any]]:
    return isinstance(x, Sequence) and not isinstance(x, str)


def is_many_scalars(x: Any) -> TypeGuard[pgt.Many[pgt.Scalar]]:
    return is_many(x) and all(isinstance(i, pgt.Scalar) for i in x)


def is_many_ints(x: Any) -> TypeGuard[pgt.Many[int]]:
    return is_many(x) and all(isinstance(i, int) for i in x)


def is_one_or_many_scalars(x: Any) -> TypeGuard[pgt.OneOrManyScalars]:
    return isinstance(x, pgt.Scalar) or is_many_scalars(x)


def is_many_one_or_many_scalars(x: Any) -> TypeGuard[pgt.Many[pgt.OneOrManyScalars]]:
    return is_many(x) and all(is_one_or_many_scalars(i) for i in x)


def is_many_2D_scalars(x: Any) -> TypeGuard[pgt.Many2DScalars]:
    return is_many(x) and all(is_many_scalars(i) for i in x)


def is_one_or_many_2D_scalars(x: Any) -> TypeGuard[pgt.OneOrMany2DScalars]:
    return isinstance(x, pgt.Scalar) or is_many_2D_scalars(x)


def is_many_one_or_many_2D_scalars(
    x: Any,
) -> TypeGuard[pgt.Many[pgt.OneOrMany2DScalars]]:
    return is_many(x) and all(is_one_or_many_2D_scalars(i) for i in x)


def is_many_3D_scalars(x: Any) -> TypeGuard[pgt.Many3DScalars]:
    return is_many(x) and all(is_many_2D_scalars(i) for i in x)
