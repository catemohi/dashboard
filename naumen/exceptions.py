
class ConnectionsFailed(Exception):

    """Исключение возвращяемой при невозможности создать соединение CRM.

        Attributes:

    """


class CantGetData(Exception):

    """Исключение возвращяемой при невозможности получить данные из CRM.

        Attributes:

    """


class InvalidDate(Exception):

    """Исключение возвращяемой при невозможности получить данные из CRM.

        Attributes:
            message: объяснение ошибки.
    """

    def __init__(self,
                 message="Формат даты неверный. Необходимый формат %d.%m.%Y"):
        self.message = message
        super().__init__(self.message)
