
class AppNotAvailableException(Exception):
    """Исключение недоступности приложения."""


class BehaveTestRecorderException(Exception):
    """
    Исключительная ситуация уровня инструмента записи тестов.
    """

    def __init__(self, message):
        Exception.__init__(self, message)
        self.exception_message = message

    def __str__(self):
        return self.exception_message
