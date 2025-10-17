"""Base class for QUBO estimator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.base import BaseEstimator
from sklearn.utils.validation import validate_data
from tno.quantum.optimization.qubo.components import (
    SolverConfig,
)

from tno.quantum.ml.components._serialization import SerializableEstimator

if TYPE_CHECKING:
    from tno.quantum.optimization.qubo.components import (
        QUBO,
        ResultInterface,
    )
    from tno.quantum.utils import BitVector


def get_default_solver_config_if_none(
    solver_config: SolverConfig | Mapping[str, Any] | None = None,
) -> SolverConfig:
    """Set default solver configuration if None is provided.

    Default solver configuration:
        ``SolverConfig(name="simulated_annealing_solver", options={})``

    Args:
        solver_config: Solver configuration or None.

    Returns:
        Given solver configuration or default configuration.
    """
    return (
        SolverConfig.from_mapping(solver_config)
        if solver_config is not None
        else SolverConfig(
            name="simulated_annealing_solver", options={"random_state": 42}
        )
    )


class QUBOEstimator(BaseEstimator, SerializableEstimator, ABC):  # type:ignore[misc]
    """Base class for a scikit-learn estimator that relies on solving a QUBO problem."""

    def __init__(
        self,
        solver_config: SolverConfig | Mapping[str, Any] | None = None,
    ) -> None:
        """Init of the QUBOEstimator.

        Args:
            solver_config: A QUBO solver configuration or None. In the former case
                includes name and options. In the latter the default solver config from
                :py:func:`~get_default_solver_config_if_none` is used.

        Attributes:
            X_: Validated & formatted input data.
            y_: Validated & formatted target data.
        """
        self.solver_config = solver_config
        self.X_: NDArray[np.float64]
        self.y_: NDArray[np.float64] | None

    def fit(self, X: ArrayLike, y: ArrayLike | None = None) -> QUBOEstimator:
        """Fit the estimator.

        Args:
            X: training data with shape (`n_samples`, `n_features`).
            y: target values with shape (`n_samples`,) or None. Defaults to `None`.

        Returns:
            `QUBOEstimator`.
        """
        # Validate and format data according to sklearn standards
        if y is None:
            X = validate_data(self, X=X, reset=True)
        else:
            X, y = validate_data(self, X=X, y=y, reset=True)
            y = np.asarray(y)
        X = np.asarray(X)

        # Check according to own standards and store attributes
        self._check_X_and_y(X, y)
        self.X_ = X
        self.y_ = y

        # Create QUBO
        self.qubo_ = self._make_qubo(X, y)

        # Get solver instance
        solver_config = get_default_solver_config_if_none(self.solver_config)

        # Solve QUBO
        solver = solver_config.get_instance()
        result: ResultInterface = solver.solve(self.qubo_)
        best_bitvector = result.best_bitvector

        # Verify found bit vector
        self._check_constraints(best_bitvector)

        # Convert bit vector to labels_
        self._decode_bit_vector(best_bitvector)

        return self

    @abstractmethod
    def _check_X_and_y(  # noqa: N802
        self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
    ) -> None:
        """Check if `X` and `y` are as expected.

        Args:
            X: training data with shape (`n_samples`, `n_features`).
            y: target values with shape (`n_samples`,) or None. Defaults to `None`.

        Raises:
            ValueError: if data is not suitable for estimator.
        """

    @abstractmethod
    def _make_qubo(
        self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
    ) -> QUBO:
        """Create QUBO from provided data.

        Args:
            X: training data with shape (`n_samples`, `n_features`).
            y: target values with shape (`n_samples`,) or None. Defaults to `None`.

        Returns:
            QUBO object used for training the model.
        """

    @abstractmethod
    def _check_constraints(self, bit_vector: BitVector) -> bool:
        """Check if the found bit vector satisfies the imposed constraints.

        Raises warnings or errors if there are violations.

        Args:
            bit_vector: BitVector containing the found solution for the QUBO.

        Returns:
            True if there are no violations, False otherwise.
        """

    @abstractmethod
    def _decode_bit_vector(self, bit_vector: BitVector) -> QUBOEstimator:
        """Decode found bit vector and set internal attributes.

        Args:
            bit_vector: BitVector containing the solution of the QUBO.
        """
