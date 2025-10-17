"""Абстракции адаптера к хранилищу файлов."""
from abc import ABC


class AbstractAdapter(ABC):

    """Абстрактный адаптер к хранилищу файлов.

    .. code-block:: python

       from ..adapters.fs import adapter as fs

       content = request.FILES['file_photo']
       path = fs.save(content.name, content)

    """

    def open(self, name, mode='rb'):
        raise NotImplementedError()

    def save(self, name, content, max_length=None):
        raise NotImplementedError()

    def delete(self, name):
        raise NotImplementedError()

    def exists(self, name):
        raise NotImplementedError()

    def size(self, name):
        raise NotImplementedError()

    def generate_filename(self, filename):
        raise NotImplementedError()

    def path(self, name):
        raise NotImplementedError()

    def url(self, name):
        raise NotImplementedError()
