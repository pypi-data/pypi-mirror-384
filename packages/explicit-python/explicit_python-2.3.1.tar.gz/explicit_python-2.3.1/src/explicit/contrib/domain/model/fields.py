"""Поля модели предметной области."""
from uuid import uuid4

from pydantic.fields import Field


def identifier(**kwargs):
    return Field(
        None,
        title='Идентификатор',
        description=(
            'Идентификатор записи. '
            'Может отсутствовать у создаваемых объектов, '
            'но обязан присутствовать у существующих.'
        ),
        gt=0,
        **kwargs
    )


def uuid_identifier(**kwargs):
    return Field(
        default_factory=uuid4,
        title='Идентификатор UUID',
        description=(
            'Идентификатор записи. '
            'Может отсутствовать у создаваемых объектов, '
            'но обязан присутствовать у существующих.'
        ),
        **kwargs
    )
