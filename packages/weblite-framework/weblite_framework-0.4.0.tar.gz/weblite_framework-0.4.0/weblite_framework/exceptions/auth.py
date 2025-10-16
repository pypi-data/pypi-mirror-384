"""Модуль исключений, связанных с авторизацией и правами доступа."""

__all__ = [
    'BaseAppException',
    'UnauthorizedException',
    'ForbiddenException',
]


class BaseAppException(Exception):
    """Базовое исключение для всех кастомных исключений."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Инициализирует базовое исключение.

        Args:
            status_code: Код передаваемой ошибки
            detail: Сообщение с передаваемой информацией
        """
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)


class UnauthorizedException(BaseAppException):
    """Класс исключения, связанного с авторизацией."""

    def __init__(self, detail: str = 'Необходима авторизация') -> None:
        """Инициализирует исключение при отсутствии авторизации.

        Args:
            detail: Сообщение с передаваемой информацией
        """
        super().__init__(
            status_code=401,
            detail=detail,
        )


class ForbiddenException(BaseAppException):
    """Класс исключения, вызываемого при отсутствии прав доступа к ресурсу."""

    def __init__(
        self,
        detail: str = 'Доступ запрещён. У вас нет прав на выполнение данного '
        'действия.',
    ) -> None:
        """Инициализирует исключение при отсутствии прав доступа.

        Args:
            detail: Сообщение с передаваемой информацией
        """
        super().__init__(
            status_code=403,
            detail=detail,
        )
