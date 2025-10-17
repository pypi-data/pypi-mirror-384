"""Вспомогательные утилиты и типы предметной области."""
from dataclasses import asdict as asdict_
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import Protocol
from typing import TypeVar
from typing import Union

from pydantic import validator
from pydantic.main import BaseModel
from pydantic.validators import _VALIDATORS


if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr


class __IsDataclass(Protocol):  # pylint: disable=invalid-name
    """Протокол датакласса.

    Лучший из известных способов сделать соответствующую подсказку.
    """
    __dataclass_fields__: ClassVar[Dict]


T = TypeVar('T')


class __SingletonMeta(type, Generic[T]):  # pylint: disable=invalid-name

    _instances: 'Dict[__SingletonMeta[T], T]' = {}  # pylint: disable=invalid-sequence-index

    def __call__(cls: '__SingletonMeta', *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Unset(metaclass=__SingletonMeta):
    """Sentinel type.

    Обозначает отсутствие значения, в т.ч. None.
    """

    def __bool__(self):
        """Проверка на истинность.

        Всегда возвращает False, т.к. обозначает отсутствующее значение.

        Например:

            class Model:
                some_attr = unset

            if Model().some_attr:
                print('Model has some_attr')

        """
        return False

    def __repr__(self):
        return '<unset>'


unset = Unset()  # Sentinel value


def is_unset(obj) -> bool:
    return isinstance(obj, Unset)


def unset_validator(v):
    return v


_VALIDATORS.append((Unset, [unset_validator]))


class HasUnsetValues(BaseModel):

    """Примесь к моделям, значения которых могут быть не заданы."""

    @validator('*', pre=True)
    def _unset_validator(cls, v):   # pylint: disable=no-self-argument
        return v

    def dict(self, *args, **kwargs):
        """Формирует словарь из данных объекта, отбрасывая не установленные значения.

        .. code-block:: python

            class DocumentDTO(DTOBase):
                series = unset
                number = unser

            DocumentDTO(number='1').dict() == {'number': '1'}

        """
        return dict(
            (k, v)
            for k, v in super().dict(*args, **kwargs).items()
            if not is_unset(v)
        )


def filter_unset(d: Any):
    if not isinstance(d, dict):
        return d

    return dict(
        (k, filter_unset(v))
        for k, v in d.items() if not is_unset(v)
    )


def asdict(
    obj: Union[__IsDataclass, 'HasUnsetValues'],
    include: Union['AbstractSetIntStr', None] = None,
    exclude: Union['AbstractSetIntStr', None] = None,
) -> dict:

    """Формирует словарь из данных объекта, отбрасывая не установленные значения.

    .. code-block:: python

        @dataclass
        class Document:
            series = unset
            number = unser

        asdict(Document(number='1')) == {'number': '1'}

    """

    if isinstance(obj, BaseModel):
        data = obj.dict(exclude=exclude, include=include)

    else:
        unfiltered_data = asdict_(obj)
        data = dict(
            (k, v)
            for k, v in unfiltered_data.items()
            if (
                k in (include or unfiltered_data) and
                k not in (exclude or ())
            )
        )

    return filter_unset(data)
