from collections.abc import Sequence
from typing import TypeVar

_T = TypeVar("_T")
Many = Sequence[_T]
Many2D = Many[Many[_T]]
Many3D = Many[Many2D[_T]]
OneOrMany = _T | Many[_T]
OneOrMany2D = _T | Many2D[_T]

Scalar = int | float
OneOrManyScalars = OneOrMany[Scalar]
ManyScalars = Many[Scalar]
OneOrMany2DScalars = OneOrMany2D[Scalar]
Many2DScalars = Many2D[Scalar]
Many3DScalars = Many3D[Scalar]

Vector1D = tuple[Scalar, ...]
Vector2D = tuple[Vector1D, ...]
Vector3D = tuple[Vector2D, ...]
