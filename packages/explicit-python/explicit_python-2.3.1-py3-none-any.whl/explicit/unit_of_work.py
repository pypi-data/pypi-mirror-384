"""Абстракции "Единицы работы"."""
from abc import ABC
from abc import abstractmethod
from queue import Queue
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Type
import threading

from explicit.adapters.db import AbstractRepository


class RepositoryRegistry:

    """Реестр репозиториев."""

    __repositories: Dict[str, AbstractRepository]  # pylint: disable=invalid-name

    def __init__(self, uow: 'AbstractUnitOfWork'):
        self.__repositories = {}
        self.__uow = uow

    def register(
        self, *repositories: Tuple[str, AbstractRepository]
    ):
        for name, repository in repositories:
            self.__repositories[name] = repository
            setattr(self.__uow, name, repository)

    def get(self, name: str) -> AbstractRepository:
        return self.__repositories[name]

    def __iter__(self):
        yield from self.__repositories.values()


# данные уровня модуля, локальные для текущего потока
_thread_local = threading.local()


class AbstractUnitOfWork(ABC):

    """Единица работы, логическая бизнес-транзакция.

    Обеспечивает атомарность выполняемых операций.

    .. code-block:: python

       class UnitOfWork(AbstractUnitOfWork):

           units: UnitsRepository
           users: UsersRepository
           persons: PersonsRepository
           students: StudentsRepository

       def handler(...):
            with UnitOfWork().wraps():
                ...

    """

    _registry: RepositoryRegistry

    strategy: 'AbstractTransactionStrategy'

    def __init__(self, *args, **kwargs) -> None:  # pylint: disable=unused-argument
        self._registry = RepositoryRegistry(self)
        # данные уровня экземпляра, локальные для текущего потока
        self._thread_local = threading.local()

    def register_repositories(
        self, *repositories: Tuple[str, AbstractRepository]
    ):
        """Регистрация репозиториев.

        Пример:

            .. code-block::python

            class AppConfig(AppConfigBase):
              def ready(self):
                  self._register_repositories()

              def _register_repositories(self):
                  from app.core import bus
                  from .adapters.db import repository

                  bus.get_uow().register_repositories(('persons', repository))

        """
        self._registry.register(*repositories)

    @property
    def _wrapping(self) -> bool:
        self._init_per_thread_state()
        return self._thread_local.uow_wrapping

    @_wrapping.setter
    def _wrapping(self, value):
        self._init_per_thread_state()
        self._thread_local.uow_wrapping = value

    @property
    def _event_queue(self):
        if not hasattr(_thread_local, 'event_queue'):
            _thread_local.event_queue = Queue()
        return _thread_local.event_queue

    def _init_per_thread_state(self):
        """Инициализирует локальные для потока атрибуты значениями по-умолчанию."""
        if not hasattr(self._thread_local, 'uow_init'):
            self._thread_local.uow_init = True
            self._thread_local.uow_wrapping = False

    @abstractmethod
    def _get_new_self(self) -> 'AbstractUnitOfWork':
        """Возвращает экземпляр UnitOfWork для вложенных транзакций."""

    def commit(self):
        """Зафиксировать транзакцию."""
        self.strategy.commit()

    def rollback(self):
        """Откатить транзакцию."""
        self.strategy.rollback()

    def wrap(self) -> 'AbstractUnitOfWork':
        """Обернуть логику в бизнес-транзакцию."""
        if not self._wrapping:
            self._wrapping = True
            return self

        return self._get_new_self()

    def add_event(self, event):
        self._event_queue.put(event)

    def collect_events(self):
        while not self._event_queue.empty():
            yield self._event_queue.get_nowait()

    def __enter__(self) -> 'AbstractUnitOfWork':
        """Начало транзакции."""

        self.strategy.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[Exception]],
        *args: Tuple
    ) -> None:
        """Окончание транзакции."""

        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
        except Exception as e:
            raise e
        finally:
            self._wrapping = False
            self.strategy.__exit__()


class AbstractTransactionStrategy(ABC):

    """Абстрактная транзакционная стратегия."""

    def __enter__(self):
        """Действия при входе в транзакцию."""

    def __exit__(self, *_):
        """Действия при выходе из транзакции."""

    @abstractmethod
    def commit(self):
        """Зафиксировать транзакцию."""

    @abstractmethod
    def rollback(self):
        """Откатить транзакцию."""
