"""This package contains components to define scikit-learn-compatible QUBO estimators.

These estimators depend on solving Quadratic Unconstrained Binary Optimization (QUBO)
problems. These problems are solved using the TNO Quantum Optimization Framework.

**Example**

The following example shows how to define a custom estimator by
subclassing :py:class:`~tno.quantum.ml.components.QUBOEstimator`. It demonstrates the
required structure, but does **not** implement a working estimator.

>>> import numpy as np
>>> from numpy.typing import NDArray
>>> from sklearn.base import ClusterMixin
>>> from tno.quantum.ml.components import QUBOEstimator
>>> from tno.quantum.optimization.qubo.components import QUBO
>>> from tno.quantum.utils import BitVectorLike
>>> from typing import Self
>>>
>>> class CustomQUBOClustering(ClusterMixin, QUBOEstimator):
...     def _check_X_and_y(
...         self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
...     ) -> None:
...         if y is None:
...             raise ValueError(
...                 "This estimator requires target values (y) to be provided "
...                 "for training."
...             )
...
...     def _make_qubo(
...         self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
...     ) -> QUBO:
...         # This should return a QUBO instance constructed from X and y.
...         pass
...
...     def _check_constraints(self, bit_vector: BitVectorLike) -> bool:
...         return True
...
...     def _decode_bit_vector(self, bit_vector: BitVectorLike) -> Self:
...         return self
>>>
>>> rng = np.random.default_rng()
>>> X = rng.random((10, 5))
>>> y = rng.integers(0, 2, size=10)
>>> model = CustomQUBOClustering()
>>> model.fit(X, y)  # doctest: +SKIP
"""

from tno.quantum.ml.components._qubo_estimator import (
    QUBOEstimator,
    get_default_solver_config_if_none,
)
from tno.quantum.ml.components._serialization import (
    SerializableEstimator,
    check_estimator_serializable,
)

__all__ = [
    "QUBOEstimator",
    "SerializableEstimator",
    "check_estimator_serializable",
    "get_default_solver_config_if_none",
]
__version__ = "2.0.3"
