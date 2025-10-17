"""Шина сообщений: обработка команд на обновление данных."""
from abc import ABC
from typing import Any
from typing import Dict
from typing import Protocol
from typing import Tuple
from typing import Type

from pydantic.main import BaseModel

from explicit.domain import HasUnsetValues

from .exceptions import NoHandlerError


class Command(HasUnsetValues, BaseModel):

    """Объект запроса на обновление данных.

    .. code-block:: python

       class RegisterStudent(Command):
           last_name: str
           first_name: str

    """

    def dict_by_prefix(
        self, prefix: str, *, removeprefix=False, exclude=None
    ) -> dict:
        assert prefix, f'prefix not set: "{prefix}"'

        if exclude is None:
            exclude = ()

        def removeprefix_(k: str) -> str:
            if removeprefix:
                return k.removeprefix(prefix)
            return k

        fields = (
            (removeprefix_(k), v)
            for k, v in self.dict().items()
            if k.startswith(prefix)
        )

        return dict(
            (k, v) for k, v in fields
            if k not in exclude
        )


class CommandHandler(Protocol):

    """Обработчик команды.

    .. code-block:: python

       def register_student(command: RegisterStudent, uow: UnitOfWork) -> None::
           assert isinstance(command, Command)
           student = factory.create(last_name=command.last_name, first_name=command.first_name)
           repository.add(student)
    """

    def __call__(self, command: Command, **kwargs) -> Any:
        """Обработка запроса на обновление данных."""


class CommandBusMixin(ABC):

    """Примесь к шине сообщений, реализует обработку команд на обновление данных."""

    _command_handlers_value: Dict[Type[Command], CommandHandler]

    @property
    def _command_handlers(self) -> Dict[Type[Command], CommandHandler]:
        if not hasattr(self, '_command_handlers_value'):
            self._command_handlers_value = {}
        return self._command_handlers_value

    def add_command_handler(self, command: Type[Command], handler: CommandHandler) -> None:
        """Регистрация обработчика команды."""

        assert issubclass(command, Command)
        assert callable(handler)
        self._command_handlers[command] = handler

    def add_command_handlers(
        self,
        *handlers: Tuple[Type[Command], CommandHandler]
    ) -> None:
        """Регистрация обработчиков команд."""

        for command, handler in handlers:
            self.add_command_handler(command, handler)

    def handle_command(self, command: Command):
        """Передача запроса обработчику типа данной команды."""

        assert isinstance(command, Command)
        handler = self._command_handlers.get(type(command))
        if handler is None:
            raise NoHandlerError(type(command))

        return handler(command)
