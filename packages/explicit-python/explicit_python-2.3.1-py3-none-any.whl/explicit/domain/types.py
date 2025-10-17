"""Набор типов полей объектов предметной области.

Пример использования:

    class SomeData(DTOBase):

        global_id: Int = Field(alias='external_id')
        first_name: Str = Field(alias='firstname')
        second_name: NoneStr = Field(alias='patronymic')
        birth_date: NoneStr = Field(alias='date_of_birth')
        gender: NoneInt = Field(alias='gender_id')
        inn_num: NoneStr = Field(alias='inn')
        snils_num: NoneStr = Field(alias='snils')

"""
from typing import Union
from uuid import UUID as UUID_
import datetime

from .model import Unset


Bool = Union[bool, Unset]
NoneBool = Union[Bool, None]

Str = Union[str, Unset]
NoneStr = Union[Str, None]

Int = Union[int, Unset]
NoneInt = Union[Int, None]

Date = Union[datetime.date, Unset]
NoneDate = Union[Date, None]

UnsetUUID = Union[UUID_, Unset]  # pylint: disable=invalid-name
NoneUnsetUUID = Union[UnsetUUID, None]  # pylint: disable=invalid-name
