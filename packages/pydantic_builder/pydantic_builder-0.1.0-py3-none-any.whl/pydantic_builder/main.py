"""`pydantic_builders.main` module."""

import sys
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AbstractBaseBuilder(ABC, Generic[T]):
    """Base class to create builders for pydantic models subclasses.

    Attributes:
    ------------------------
        attributes: dict[str, Any] = {}

    """

    def __init__(self) -> None:
        """Initializes the builder."""

        self.attributes: dict[str, Any] = self.default_instance.model_dump()

    @property
    @abstractmethod
    def default_instance(self) -> T:
        """Returns the default instance of the parameter class.


        This method must be implemented in the subclass.
        The `default_instance` purpose is to define the default values for the attributes.

        """

        return T()

    def get_parameter_class(self) -> type[T]:
        """Returns the parameter class."""

        # NOTE : Useful link to understand the below <VM, 28/02/2024>
        # https://discuss.python.org/t/runtime-access-to-type-parameters/37517

        return self.__orig_bases__[0].__args__[0]

    def build(self) -> T:
        """Creates instance of the parameter class."""

        cls = self.get_parameter_class()
        return cls(**self.attributes)

    def with_(self, **kwargs: Any) -> Self:
        """Sets an attribute of the class to be built.

        Args:
        ------------------------------
        **kwargs: Any
            The attribute to be set.

        """

        self.attributes.update(kwargs)

        return self
