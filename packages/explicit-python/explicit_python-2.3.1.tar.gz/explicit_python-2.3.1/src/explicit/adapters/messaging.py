"""Абстракции адаптера обмена сообщениями."""
from abc import ABC
from abc import abstractmethod


class AbstractAdapter(ABC):

    @abstractmethod
    def publish(self, message, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def subscribe(self, *args, **kwargs):
        raise NotImplementedError()
