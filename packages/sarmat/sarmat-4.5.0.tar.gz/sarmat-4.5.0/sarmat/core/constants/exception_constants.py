"""
Sarmat.
Ядро пакета.
Описание ошибок.
Типы ошибок, коды, описание.
"""
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum


SarmatErrorType = namedtuple("SarmatErrorType", "code title")
SarmatErrorClass = namedtuple("SarmatErrorClass", "cypher description")


class MessageType(SarmatErrorType, Enum):
    """Типы сообщений."""
    INFORMATION = 0, "Информация"
    QUESTION = 1, "Вопрос"
    WARNING = 2, "Внимание"
    ERROR = 3, "Ошибка"
    CRITICAL = 4, "Критическая ошибка"


class ErrorClass(SarmatErrorClass, Enum):
    """Классификация ошибки."""

    UNKNOWN = "", ""
    SYSTEM = "S", "Системная ошибка"
    DATA = "D", "Ошибка данных"
    OPERATION = "O", "Ошибка выполнения операции"


@dataclass
class SarmatException(Exception):
    """Класс ошибки в формате Sarmat."""
    err_class: ErrorClass = ErrorClass.UNKNOWN
    err_type: MessageType = MessageType.ERROR
    title: str = ""
    description: str = ""


class SarmatExpectedAttributeError(SarmatException):
    """Ошибка возникает при отсутствии атрибута в объекте."""
    err_class = ErrorClass.DATA
    title = "Отсутствует атрибут"


class SarmatNotFilledAttribute(SarmatException):
    """Ошибка возникает при обнаружении незаполненного атрибута."""
    err_class = ErrorClass.DATA
    title = "Не указано значение"


class SarmatWrongTypeAttribute(SarmatException):
    """Атрибут содержит значение неверного типа."""
    err_class = ErrorClass.DATA
    title = "Невертный тип данных"


class SarmatWrongValueError(SarmatException):
    """Атрибут содержит неверное значение."""
    err_class = ErrorClass.DATA
    title = "Неверное значение данных"


class SarmatWrongOperationError(SarmatException):
    """Невозможно выполнить операцию."""
    err_class = ErrorClass.OPERATION
    title = "Невозможная операция"
