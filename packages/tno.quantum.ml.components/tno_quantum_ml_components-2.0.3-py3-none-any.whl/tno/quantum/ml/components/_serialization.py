"""Class for serialization of sklearn compatible estimators."""

from __future__ import annotations

import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from tno.quantum.utils.serialization import Serializable, check_serializable


class SerializableEstimator(Serializable):
    """Framework for serializable estimators."""

    @override
    def _serialize(self) -> dict[str, Any]:
        """Serialize to dict for sklearn estimators."""
        # Serialize as usual to store constructor arguments
        dict_ = Serializable._serialize(self)  # noqa: SLF001

        # Store derived attributes as well (i.e. those with trailing underscore)
        for attr, value in self.__dict__.items():
            if attr.endswith("_"):
                dict_[attr] = Serializable.serialize(value)

        return dict_

    @override
    @classmethod
    def _deserialize(cls, data: dict[str, Any]) -> Any:
        """Deserialize to dict for sklearn estimators."""
        # Split attributes based on whether they have a trailing underscore
        attrs_init = [attr for attr in data if not attr.endswith("_")]
        attrs_other = [attr for attr in data if attr.endswith("_")]

        # Initialize with attributes without trailing underscores
        instance = cls(
            **{attr: Serializable.deserialize(data[attr]) for attr in attrs_init}
        )

        # Set additional attributes for attributes with trailing underscore
        for attr in attrs_other:
            setattr(instance, attr, Serializable.deserialize(data[attr]))

        return instance


def check_estimator_serializable(serializable_object: Any) -> None:
    """Test if object is serializable and can be reconstructed from its serialization.

    Args:
        serializable_object: Object to be serialized and reconstructed.

    Raises:
        AssertionError: If the object is not SerializableEstimator, or if the
            reconstruction of the object is not equal to the original object.
    """
    # Test if object is SerializableEstimator
    assert isinstance(serializable_object, SerializableEstimator), (  # noqa: S101
        "Object is not SerializableEstimator"
    )
    check_serializable(serializable_object)
