"""Реестр событий по топикам."""
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Dict
from typing import Type
from typing import Union
import logging


if TYPE_CHECKING:
    from explicit.messagebus.events import Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Message:
    topic: str
    """Наименование топика."""

    type: str
    """Наименование типа события."""

    body: dict
    """Тело события."""


class Registry:

    """Реестр событий по топикам."""

    _registry: Dict[str, list[Type['Event']]]

    def __init__(self):
        self._registry = defaultdict(list)

    def register(self, topic: str, *events: Type['Event']) -> None:
        """Регистрирует сопоставление топика с типом события."""
        self._registry[topic].extend(events)

    def resolve(self, message: Message) -> Union['Event', None]:
        """
        Определяет подходящий тип события и возвращает экземпляр для передачи на обработку в шину событий либо None.
        """
        event = None

        for event_cls in self._registry[message.topic]:
            if event_cls.__name__ == message.type:
                event = event_cls(**message.body)

        if event is None:
            logger.warning('Событие "%s" не определено', message.type)

        return event
