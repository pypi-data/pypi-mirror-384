"""Tests for the QUBOEstimator ABC."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from numpy.typing import ArrayLike, NDArray
from sklearn.utils.estimator_checks import check_estimator
from tno.quantum.optimization.qubo.components import QUBO, SolverConfig

from tno.quantum.ml.components import QUBOEstimator
from tno.quantum.ml.components._qubo_estimator import get_default_solver_config_if_none
from tno.quantum.ml.components._serialization import check_estimator_serializable

if TYPE_CHECKING:
    from tno.quantum.utils import BitVectorLike


class DummyEstimator(QUBOEstimator):
    def _check_X_and_y(  # noqa: N802
        self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
    ) -> None:
        pass

    def _make_qubo(
        self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
    ) -> QUBO:
        return QUBO([[1, 0], [2, 0]])

    def _check_constraints(self, bit_vector: BitVectorLike) -> bool:
        return True

    def _decode_bit_vector(self, bit_vector: BitVectorLike) -> QUBOEstimator:
        return self


@pytest.mark.parametrize(
    ("solver_config", "expected_name", "expected_options"),
    [
        (None, "simulated_annealing_solver", {"random_state": 42}),
        (
            SolverConfig(name="custom_solver", options={"max_iter": 100}),
            "custom_solver",
            {"max_iter": 100},
        ),
        (
            {"name": "tree_decomposition_solver", "options": {}},
            "tree_decomposition_solver",
            {},
        ),
    ],
)
def test_get_default_solver_config_if_none(
    solver_config: SolverConfig | Mapping[str, Any] | None,
    expected_name: str,
    expected_options: Mapping[str, Any],
) -> None:
    result = get_default_solver_config_if_none(solver_config)

    assert isinstance(result, SolverConfig)
    assert result.name == expected_name
    assert result.options == expected_options


@pytest.mark.parametrize(
    "y",
    [
        [0, 1],  # supervised
        None,  # unsupervised
    ],
)
def test_fit_stores_X_and_y(y: ArrayLike | None) -> None:  # noqa: N802
    X = [[1.0, 2.0], [3.0, 4.0]]
    estimator = DummyEstimator()
    estimator.fit(X, y)

    assert np.array_equal(estimator.X_, np.asarray(X))
    if y is None:
        assert estimator.y_ is None
    else:
        assert isinstance(estimator.y_, np.ndarray)
        assert np.array_equal(estimator.y_, np.asarray(y))


def test_qubo_estimator_is_abstract() -> None:
    with pytest.raises(TypeError):
        QUBOEstimator()


def test_inherrit_from_qubo_estimator() -> None:
    estimator = DummyEstimator()
    estimator.fit(np.zeros((2, 2)), np.zeros(2))


def test_check_estimator() -> None:
    """Check sklearn compliance of DummyEstimator."""
    estimator = DummyEstimator()
    check_estimator(estimator)


@pytest.mark.parametrize(
    ("solver_config_1", "solver_config_2", "expected_result"),
    [
        (
            SolverConfig(name="simulated_annealing_solver", options={}),
            SolverConfig(name="simulated_annealing_solver", options={}),
            True,
        ),
        (
            SolverConfig(name="simulated_annealing_solver", options={}),
            SolverConfig(name="tree_decomposition_solver", options={}),
            False,
        ),
        (
            SolverConfig(name="simulated_annealing_solver", options={}),
            {"name": "simulated_annealing_solver", "options": {}},
            False,  # Different type of solver config means different estimator.
        ),
        (
            SolverConfig(name="simulated_annealing_solver", options={}),
            {"name": "tree_decomposition_solver", "options": {}},
            False,
        ),
        (
            SolverConfig(name="simulated_annealing_solver", options={}),
            None,
            False,
        ),
    ],
)
def test_eq_solver_config(
    solver_config_1: SolverConfig | Mapping[str, Any],
    solver_config_2: SolverConfig | Mapping[str, Any] | None,
    expected_result: bool,
) -> None:
    """Test equality of QUBOEstimator with different solver configurations."""
    estimator_1 = DummyEstimator(solver_config=solver_config_1)
    estimator_2 = DummyEstimator(solver_config=solver_config_2)
    assert (estimator_1 == estimator_2) == expected_result

    estimator_3 = DummyEstimator()
    estimator_4 = DummyEstimator()
    estimator_3.fit(np.array([[1, 2, 3]]))
    estimator_4.fit(np.array([[1, 2, 3]]))
    assert estimator_3 == estimator_4


def test_serialization() -> None:
    """Test correct serialization of estimator."""
    estimator1 = DummyEstimator()
    check_estimator_serializable(estimator1)
    estimator2 = DummyEstimator()
    X = [[1.0, 2.0], [3.0, 4.0]]
    estimator2.fit(X)
    check_estimator_serializable(estimator2)
