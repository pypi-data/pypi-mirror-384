"""Шина сообщений: обработка запросов на чтение данных."""
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Type


@dataclass
class Query(ABC):
    """Объект запроса на чтение данных."""


class QueryHandler(ABC):

    @abstractmethod
    def handle(self, query: Query) -> Any:
        """Обработка запроса на чтение данных."""
        assert isinstance(query, Query)


class QueryBusMixin(ABC):

    """Примесь к шине сообщений, реализует обработку запросов на чтение данных."""

    _query_handlers_value: Dict[Type[Query], QueryHandler]

    @property
    def _query_handlers(self) -> Dict[Type[Query], QueryHandler]:
        if not hasattr(self, "_query_handlers_value"):
            self._query_handlers_value = {}
        return self._query_handlers_value

    def add_query_handler(
        self, query: Type[Query], handler: QueryHandler
    ) -> None:
        """Регистрация обработчика запроса."""

        assert issubclass(query, Query)
        assert isinstance(handler, QueryHandler)
        self._query_handlers[query] = handler

    def handle_query(
        self,
        query: Query,
    ):
        """Передача запроса обработчику типа данного запроса."""

        assert isinstance(query, Query)
        return self._query_handlers[type(query)].handle(query)
