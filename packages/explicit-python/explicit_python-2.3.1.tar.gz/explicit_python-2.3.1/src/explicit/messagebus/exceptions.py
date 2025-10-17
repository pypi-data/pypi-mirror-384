from typing import Any


class NoHandlerError(ValueError):
    """Обработчик для данного сообщения не зарегистрирован."""

    def __init__(self, message_cls: type[Any], *args, **kwargs):
        super().__init__(f'No handler for {message_cls}', *args, **kwargs)
