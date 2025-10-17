# TNO Quantum: Machine Learning - Components

TNO Quantum provides generic software components aimed at facilitating the development
of quantum applications.

This package contains generic components for our machine learning packages.

*Limitations in (end-)use: the content of this software package may solely be used for applications 
that comply with international export control laws.*

## Documentation

Documentation of the `tno.quantum.ml.components` package can be found [here](https://tno-quantum.github.io/documentation/).

## Install

Easily install the `tno.quantum.ml.components` package using pip:

```console
$ python -m pip install tno.quantum.ml.components
```

## Usage

The Quantum Machine Learning Components package allows you to define custom `scikit-learn`-compatible estimators that depend on solving QUBO problems.

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Self

import numpy as np
from numpy.typing import NDArray
from sklearn.base import ClusterMixin

from tno.quantum.ml.components import QUBOEstimator

if TYPE_CHECKING:
    from tno.quantum.optimization.qubo.components import QUBO
    from tno.quantum.utils import BitVectorLike


class CustomQUBOClustering(ClusterMixin, QUBOEstimator):
    """Custom QUBO clustering for demonstration purposes.

    This is **NOT** a functional clustering class but serves as an example of how to 
      implement a QUBO estimator in the TNO Quantum framework.
    """

    def _check_X_and_y(
        self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
    ) -> None:
        if y is None:
            error_msg = (
                "This estimator requires target values (y) to be provided for training."
            )
            raise ValueError(error_msg)

    def _make_qubo(
        self, X: NDArray[np.float64], y: NDArray[np.float64] | None = None
    ) -> QUBO:
        # Create here the QUBO matrix based on the input data.
        pass

    def _check_constraints(self, bit_vector: BitVectorLike) -> bool:
        # No specific constraints for this classifier.
        return True

    def _decode_bit_vector(self, bit_vector: BitVectorLike) -> Self:
        # Decode the bit vector to return the classifier instance.
        return self
```

For a more complete and functional example, see the [`QKMedoids`](https://github.com/TNO-Quantum/ml.clustering.kmedoids) implementation.
