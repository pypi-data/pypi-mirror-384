"""Абстракции адаптера СУБД."""
from abc import ABCMeta
from abc import abstractmethod
from typing import Any


class AbstractSpecification(metaclass=ABCMeta):

    """Набор условий для проверки соответствия объекта этим условиям."""

    @abstractmethod
    def as_filter(self):
        """Представление в виде фильтра."""

    @abstractmethod
    def is_satisfied_by(self, instance) -> bool:
        """Соответствует ли объект условиям."""


class AbstractRepository(metaclass=ABCMeta):

    """Репозиторий - абстракция над хранилищем данных (БД).

    Должен содержать методы получения объектов со всеми вариантами выборки:
       * Все записи
       * По идентификатору
       * По условию (фильтрация)
       * Стандартные наборы (администраторы, министерства,
         виды занятий для очного обучения и т.п.)

    .. note::
       Репозиторий должен возвращать объекты модели модели предметной области,
       но не хранилища.

    """

    def _to_domain(self, dbinstance: Any) -> Any:
        """Преобразование из объекта БД в объект модели."""
        raise NotImplementedError()

    def _to_db(self, modelinstance):
        """Преобразование из объекта модели в объект БД."""
        raise NotImplementedError()

    def add(self, obj):
        """Добавление объекта."""
        raise NotImplementedError()

    def update(self, obj):
        """Обновление объекта."""
        raise NotImplementedError()

    def delete(self, obj):
        """Удаление объекта."""
        raise NotImplementedError()

    def get_all_objects(self):
        """Возвращает все объекты."""
        raise NotImplementedError()

    def get_object_by_id(self, identifier):
        """Возвращает объект по его идентификатору."""
        raise NotImplementedError()
