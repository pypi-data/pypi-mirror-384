"""
Sarmat.
Ядро пакета.
Константы.
Константы бизнес логики.
"""
from collections import namedtuple
from enum import Enum
from typing import Any


month_len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
SarmatConstant = namedtuple("SarmatConstant", "id cypher name")


class SarmatAttribute(SarmatConstant, Enum):
    """Встроенные значения атрибутов в Sarmat."""

    @property
    def as_text(self) -> str:
        """Описание значения."""
        val: SarmatConstant = self.value
        return val.name

    @property
    def as_cypher(self) -> str:
        """Получение строковой константы."""
        val: SarmatConstant = self.value
        return val.cypher

    @property
    def id(self) -> Any:
        val: SarmatConstant = self.value
        return val.id


class RoadType(SarmatAttribute):
    """Тип дорожного покрытия."""
    PAVED = 1, "", "Дорога с твердым покрытием"
    DIRT = 2, "", "Грунтовая дорога"
    HIGHWAY = 3, "", "Магистраль"
    TOLL_ROAD = 4, "", "Платная дорога"


class DurationType(SarmatAttribute):
    """Тип продолжительности."""
    MINUTE = 1, "minutes", "Минуты"
    HOUR = 2, "hours", "Часы"
    DAY = 3, "days", "Дни"
    WEEK = 4, "weeks", "Недели"
    MONTH = 5, "months", "Месяцы"
    YEAR = 6, "years", "Годы"


class IntervalType(SarmatAttribute):
    """Тип интервала."""
    MINUTE = 1, "minute", "По минутам"
    HOUR = 2, "hour", "По часам"
    DAY = 3, "day", "По дням"
    WEEK = 4, "week", "По неделям"
    MONTH = 5, "month", "По месяцам"
    YEAR = 6, "year", "По годам"
    EVEN = 7, "even", "По четным дням месяца"
    ODD = 8, "odd", "По нечетным дням месяца"
    DAYS = 9, "days", "По числам месяца"
    DAYS_OF_WEEK = 10, "dow", "По дням недели"


class LocationType(SarmatAttribute):
    """Тип территориального образования."""
    COUNTRY = 1, "", "Страна"
    DISTRICT = 2, "респ.", "Республика"
    REGION = 3, "кр.", "Край"
    PROVINCE = 4, "обл.", "Область"
    AREA = 5, "р-н", "Район"


class SettlementType(SarmatAttribute):
    """Тип населенного пункта."""
    CITY = 1, "г.", "Город"
    SETTLEMENT = 2, "пос.", "Поселок"
    TOWNSHIP = 3, "с.", "Село"
    HAMLET = 4, "дер.", "Деревня"
    COUNTRYSIDE = 5, "ст.", "Станица"
    FARM = 6, "х.", "Хутор"
    VILLAGE = 7, "сл.", "Слобода"
    TURN = 8, "пов.", "Поворот"
    POINT = 9, "м.", "Место"


class StationType(SarmatAttribute):
    """Типы станций."""
    STATION = 1, "АВ", "Автовокзал"
    TERMINAL = 2, "АС", "Автостанция"
    TICKET_OFFICE = 3, "АК", "Автокасса"
    PLATFORM = 4, "ОП", "Остановочная платформа"


class RouteType(SarmatAttribute):
    """Типы маршрутов."""
    TURNOVER = 1, "turn", "Оборотный"
    CIRCLE = 2, "circle", "Кольцевой"


class JourneyType(SarmatAttribute):
    """Типы рейсов."""
    SUBURBAN = 1, "", "Пригородный"
    LONG_DISTANCE = 2, "", "Междугородный"
    INTER_REGIONAL = 3, "", "Межрегиональный"
    INTERNATIONAL = 4, "", "Международный"


class DurationMonthCalcStrategy(SarmatAttribute):
    """Стратегия расчёта месячной продолжительности."""
    DOWN = 1, "down", "Откат к наименьшему дню месяца"
    MOVE = 2, "move", "Смещение по количеству дней в конце месяца"
    FULL = 3, "max", "Считаем, что во всех месяцах 31 день"


class CalculationType(SarmatAttribute):
    """Виды расчёта стоимости."""
    CONST = 1, "const", "Константное значение"
    RATE = 2, "rate", "Тариф за пройденный километраж"
    STEP = 3, "step", "Зональный тип расчёта стоимости"
    # NOTE: not needed yet MIXED = 4, "mixed", "Смешанный тип расчёта"


class JourneyClass(SarmatAttribute):
    """Классификация рейсов."""
    BASE = 1, "", "Формирующийся"
    TRANSIT = 2, "", "Транзитный"
    ARRIVING = 3, "", "Прибывающий"


class JourneyState(SarmatAttribute):
    """Состояния рейсов."""
    READY = 0, "", "Активен"
    ARRIVED = 1, "", "Прибыл"
    ON_REGISTRATION = 2, "", "На регистрации"
    DEPARTED = 3, "", "Отправлен"
    CANCELLED = 4, "", "Отменен"
    CLOSED = 5, "", "Закрыт"
    DISRUPTED = 6, "", "Сорван"


class VehicleType(SarmatAttribute):
    """Тип транспортного средства."""
    BUS = 1, "", "Автобус"
    SMALL_BUS = 2, "", "Автобус малой вместимости"
    CAR = 3, "", "Легковой автомобиль"
    TRUCK = 4, "", "Грузовой автомобиль"
    TRAILER = 5, "", "Прицеп"
    SPECIAL = 6, "", "Спецтехника"


class CrewType(SarmatAttribute):
    """Тип участника экипажа."""
    DRIVER = 1, "", "Водитель"
    TRAINEE = 2, "", "Стажер"


class PermitType(SarmatAttribute):
    """Тип путевого листа."""
    BUS_PERMIT = 1, "", "Путевой лист автобуса"
    CAR_PERMIT = 2, "", "Путевой лист легкового автомобиля"
    TRUCK_PERMIT = 3, "", "Путевой лист грузового автомобиля"
    CUSTOM_PERMIT = 4, "", "Заказной путевой лист"


class PlaceKind(SarmatAttribute):
    """Тип места."""
    PASSENGERS_SEAT = 1, "P", "Пассажирское место"
    BAGGAGE = 2, "B", "Багажное место"


class PlaceType(SarmatAttribute):
    """Вид пассажирского места."""
    STANDING = 1, "", "Место для стоящих пассажиров"
    SITTING = 2, "", "Место для сидящих пассажиров"


class PlaceState(SarmatAttribute):
    """Состояние места."""
    FREE = 1, "", "Свободно"
    BOOKED = 2, "", "Забронировано"
    CLOSED = 3, "", "Закрыто"
    SOLD = 4, "", "Продано"
    LOCKED = 5, "", "Заблокировано"
    TRANSFERRED = 6, "", "Произведена пересадка"


MAX_SUBURBAN_ROUTE_LENGTH = 50      # Максимальная длина пригородных маршрутов (в километрах)
