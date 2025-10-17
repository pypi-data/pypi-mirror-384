"""Набор полей объектов предметной области."""
from functools import partial

from pydantic import Field as DefaultField

from .model import unset


Field = partial(DefaultField, default=unset)
