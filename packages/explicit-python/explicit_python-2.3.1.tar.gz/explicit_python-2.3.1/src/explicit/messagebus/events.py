"""Шина сообщений: обработка событий."""
from abc import ABC
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from uuid import uuid4
import json

from more_itertools.recipes import consume
from pydantic.fields import Field
from pydantic.json import pydantic_encoder

from explicit.domain.model import asdict


if TYPE_CHECKING:
    from dataclasses import dataclass  # noqa

    from explicit.unit_of_work import AbstractUnitOfWork  # noqa
else:
    from pydantic.dataclasses import dataclass  # noqa


@dataclass
class EventMeta:
    id: str = Field(default_factory=lambda: str(uuid4()))
    transaction_id: Optional[str] = None
    payload: Dict = Field(default_factory=dict)


@dataclass
class Event:
    """Событие."""
    meta: EventMeta = Field(default_factory=EventMeta)

    def set_transaction_id(self, transaction_id: str):
        self.meta.transaction_id = transaction_id

    def get_transaction_id(self) -> Optional[str]:
        return self.meta.transaction_id

    def set_payload(self, payload: Dict):
        assert isinstance(payload, dict)
        self.meta.payload = payload

    def get_payload(self):
        return self.meta.payload

    @classmethod
    def from_event(cls, event: 'Event', **kwargs) -> 'Event':
        return cls(
            meta=EventMeta(transaction_id=event.meta.transaction_id, payload=event.meta.payload),
            **kwargs
        )

    def configure_meta(
        self, transaction_id: Optional[str] = None, payload: Optional[Dict] = None
    ) -> None:
        self.meta.transaction_id = transaction_id
        if payload:
            assert isinstance(payload, dict)
            self.meta.payload = payload

    def dump(self) -> str:
        return json.dumps(
            {
                'type': type(self).__name__,
                'body': asdict(self)
            },
            default=pydantic_encoder
        )


EventHandler = Callable[[Event], Any]
"""Обработчик события.

.. code-block:: python

   def student_registered(event: StudentRegistered, uow: UnitOfWork) -> None:
       assert isinstance(event, Event)
       ...
"""


class EventBusMixin(ABC):

    """Примесь к шине сообщений, реализует обработку событий."""

    _event_handlers_value: Dict[Type[Event], List[EventHandler]]

    @property
    def _event_handlers(self) -> Dict[Type[Event], List[EventHandler]]:
        if not hasattr(self, '_event_handlers_value'):
            self._event_handlers_value = {}
        return self._event_handlers_value

    def add_event_handler(
        self, event: Type[Event], handler: EventHandler
    ) -> None:
        """Регистрация обработчика события."""

        assert issubclass(event, Event)
        assert callable(handler)
        self._event_handlers.setdefault(event, []).append(handler)

    def handle_event(self, event: Event):
        """Передача события списку обработчиков типа данного события."""

        assert isinstance(event, Event)

        try:
            consume(
                handler(event)
                for handler in self._event_handlers[type(event)]
            )
        except KeyError as e:
            raise ValueError(f'No handler for {type(event)}') from e
