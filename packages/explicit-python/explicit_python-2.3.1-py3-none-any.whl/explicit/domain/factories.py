"""Объекты передачи данных."""
from abc import ABCMeta
from abc import abstractmethod

from pydantic.main import BaseModel  # pylint: disable=no-name-in-module

from .model import HasUnsetValues


class DTOBase(HasUnsetValues, BaseModel):

    """Базовый объект передачи данных.

    .. code-block::python

       dto = DeclarationDTO(last_name='Иванов', first_name='Иван')
       declaration: Declaration = declaration_factory.create(dto)

    """

    class Config:
        arbitrary_types_allowed = False


class AbstractDomainFactory(metaclass=ABCMeta):

    @abstractmethod
    def create(self, data):
        """Сборка объекта модели предметной области из переданных данных.

        Например:

        .. code-block:: python

          dto = DeclarationDTO(last_name='Иванов', first_name='Иван')
          declaration: Declaration = declaration_factory.create(dto)
        """
