"""Шина сообщений: внедрение зависимостей."""
from functools import partial
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
import inspect
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UnknownDependencyError(Exception):
    """Ожидаемая обработчиком зависимость не зарегистрирована."""


class AlreadyRegisteredDependencyError(Exception):
    """Зависимость с таким именем уже зарегистрирована."""


class DependencyInjectionMixin:

    """Примесь к шине сообщений, реализует управление зависимостями и их внедрение."""

    _dependencies: Dict[str, Callable]

    def register_dependency(self, alias: str, dependency: Callable):
        """Зарегистрировать зависимость."""
        if alias in self._dependencies:
            raise AlreadyRegisteredDependencyError(f'Зависимость с именем {alias} именем уже зарегистрирована')

        self._dependencies[alias] = dependency
        logger.debug('Зарегистрирована зависимость %s', alias)

    def _set_dependencies(self, **dependencies: Any):
        """Заменяет внутреннее сопоставление зависимостей."""
        self._dependencies = dependencies

    def _get_dependency(self, alias: str) -> Callable:
        """Определяет и возвращает зависимость по имени."""
        try:
            return self._dependencies[alias]
        except KeyError as e:
            raise UnknownDependencyError(f'Зависимость для аргумента "{alias}" не найдена') from e

    def _inject_dependencies(self, target: Callable, exclude: Optional[set[str]] = None) -> Callable:
        """Внедряет зависимости в target."""
        exclude = exclude or set()

        target_signature = inspect.signature(target)
        # определяем зависимости, которые ожидает обработчик
        deps = {
            name: self._get_dependency(name)
            for name in target_signature.parameters.keys()
            if name not in exclude
        }
        logger.debug('В обработчик %s внедрены зависимости %s', target, deps)
        return partial(target, **deps)
