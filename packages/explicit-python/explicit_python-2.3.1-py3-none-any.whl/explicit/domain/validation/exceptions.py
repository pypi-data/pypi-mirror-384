"""Исключения предметной области."""
from collections import defaultdict
from functools import wraps
from typing import List
from typing import Mapping

from pydantic import ValidationError as PydanticValidationError


NON_FIELD_ERRORS = '__all__'


def init_messages_dict() -> Mapping[str, List[str]]:
    return defaultdict(list)


class DomainValidationError(Exception):

    """Ошибка валидации данных модели предметной области.

    .. code-block:: python

       def handler(...):
            errors = init_messages_dict()
            if not password:
                errors['Пароль'].append('Обязательное поле')
            if password != confirm:
                errors['Пароль'].append('Пароль и подтверждение не совпадают')
            if errors:
                raise DomainValidationError(errors)

    """

    def __init__(self, message, code=None, params=None):
        """
        The `message` argument can be a single error, a list of errors, or a
        dictionary that maps field names to lists of errors.

        What we define as an "error" can be either a simple string or an
        instance of DomainValidationError with its message attribute set, and
        what we define as list or dictionary can be an actual `list` or `dict`
        or an instance of DomainValidationError with its `error_list` or
        `error_dict` attribute set.
        """
        super().__init__(message, code, params)

        if isinstance(message, DomainValidationError):
            if hasattr(message, 'error_dict'):
                message = message.error_dict
            elif not hasattr(message, 'message'):
                message = message.error_list
            else:
                message, code, params = (
                    message.message, message.code, message.params
                )

        if isinstance(message, dict):
            self.error_dict = {}
            for field, messages in message.items():
                if not isinstance(messages, DomainValidationError):
                    messages = DomainValidationError(messages)
                self.error_dict[field] = messages.error_list

        elif isinstance(message, list):
            self.error_list = []
            for sub_message in message:
                # Normalize plain strings to instances of
                # DomainValidationError.
                if not isinstance(sub_message, DomainValidationError):
                    sub_message = DomainValidationError(sub_message)
                if hasattr(sub_message, 'error_dict'):
                    self.error_list.extend(
                        sum(sub_message.error_dict.values(), []))
                else:
                    self.error_list.extend(sub_message.error_list)

        else:
            self.message = message
            self.code = code
            self.params = params
            self.error_list = [self]

    @property
    def message_dict(self):
        # Trigger an AttributeError if this DomainValidationError
        # doesn't have an error_dict.
        getattr(self, 'error_dict')

        return dict(self)

    @property
    def messages(self):
        if hasattr(self, 'error_dict'):
            return sum(dict(self).values(), [])
        return list(self)

    def update_error_dict(self, error_dict):
        if hasattr(self, 'error_dict'):
            for field, error_list in self.error_dict.items():
                error_dict.setdefault(field, []).extend(error_list)
        else:
            error_dict.setdefault(NON_FIELD_ERRORS, []).extend(self.error_list)
        return error_dict

    def __iter__(self):
        if hasattr(self, 'error_dict'):
            for field, errors in self.error_dict.items():
                yield field, list(DomainValidationError(errors))
        else:
            for error in self.error_list:
                message = error.message
                if error.params:
                    message %= error.params
                yield str(message)

    def __str__(self):
        if hasattr(self, 'error_dict'):
            return repr(dict(self))
        return repr(list(self))

    def __repr__(self):
        return f'DomainValidationError({self})'


def handle_pydantic_validation_error(fn):

    """Конвертирует PydanticValidationError в DomainValidationError.

    .. code-block:: python

    @handle_domain_validation_error
    def create_object(uow: 'UnitOfWork', data: 'SessionOrderDTO',):
        ...
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PydanticValidationError as error:
            errors_dict = defaultdict(list)
            for i in error.errors():
                for field in i['loc']:
                    errors_dict[field].append(i['msg'])
            if errors_dict:
                raise DomainValidationError(errors_dict) from error
        return fn
    return wrapper
