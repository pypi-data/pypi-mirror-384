"""Шина сообщений."""
from typing import Type
import threading

from explicit.unit_of_work import AbstractUnitOfWork

from .commands import Command
from .commands import CommandBusMixin
from .commands import CommandHandler
from .dependency_injection import DependencyInjectionMixin
from .events import Event
from .events import EventBusMixin
from .events import EventHandler
from .queries import Query
from .queries import QueryBusMixin


class MessageBus(DependencyInjectionMixin, QueryBusMixin, CommandBusMixin, EventBusMixin):

    """Шина.

    Обеспечивает доставку команды соответствующему обработчику.

    .. code-block:: python

       from core import bus

       bus.handle(Command(...))

    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        **dependencies,
    ):
        self._thread_local = threading.local()
        self._uow = uow
        self._set_dependencies(uow=uow, **dependencies)

    def add_command_handler(self, command: Type[Command], handler: CommandHandler) -> None:
        """Внедрение зависимостей в обработчик и регистрация его обычным образом."""
        super().add_command_handler(
            command=command, handler=self._inject_dependencies(target=handler, exclude={'command'})
        )

    def add_event_handler(self, event: Type[Event], handler: EventHandler) -> None:
        """Внедрение зависимостей в обработчик и регистрация его обычным образом."""
        super().add_event_handler(event=event, handler=self._inject_dependencies(target=handler, exclude={'event'}))

    def get_uow(self) -> AbstractUnitOfWork:
        """Возвращает используемый UnitOfWork.

        Может использоваться, например, для динамической регистрации репозиториев.
        """
        return self._uow

    @property
    def _message_queue(self):
        if not hasattr(self._thread_local, 'message_bus_queue'):
            self._thread_local.message_bus_queue = []
        return self._thread_local.message_bus_queue

    def _collect_events(self):
        self._message_queue.extend(self._uow.collect_events())

    def handle(self, message):
        result = None

        self._message_queue[:] = [message]

        while self._message_queue:
            message = self._message_queue.pop(0)

            if isinstance(message, Query):
                result = self.handle_query(message)

            elif isinstance(message, Command):
                result = self.handle_command(message)

            elif isinstance(message, Event):
                # результат обработки события нас не интересует.
                self.handle_event(message)

            else:
                raise ValueError(f'Unknown message type: {message}')

            self._collect_events()

        return result
