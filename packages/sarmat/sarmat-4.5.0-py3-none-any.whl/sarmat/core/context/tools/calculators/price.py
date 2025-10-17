"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Вспомогательные инструменты.
Вычисления с участием Sarmat объектов.
Вычисление стоимости проезда.
"""
from abc import ABC, abstractmethod
from typing import Any, Union

from dataclasses import asdict, dataclass

from sarmat.core.constants import SarmatWrongValueError, ErrorClass
from sarmat.core.constants.sarmat_constants import CalculationType
from sarmat.core.context.models import (JourneyModel, RouteModel)

RouteSimilarity = Union[JourneyModel, RouteModel]


@dataclass
class PriceCalculation:
    """Структура для расчёта стоимости."""

    @property
    def as_dict(self):
        return asdict(self)


@dataclass
class PriceCalculationConstant(PriceCalculation):
    """Структура для простого расчёта стоимости."""

    values_map: list[list[float]]    # значения
    calc_type: CalculationType = CalculationType.CONST


@dataclass
class PriceCalculationRate(PriceCalculation):
    """Структура для расчёта стоимости за пройденный километраж."""

    rate: float     # значение тарифа
    calc_type: CalculationType = CalculationType.RATE


@dataclass
class PriceCalculationStep(PriceCalculation):
    """Структура для расчёта стоимости по зонам прохождения."""

    steps: dict[int, float]     # маппинг стоимости на расстояние
    calc_type: CalculationType = CalculationType.STEP

    def __post_init__(self):
        self.steps = {int(key): round(val, 2) for key, val in self.steps.items()}


class PriceCalculator(ABC):
    """Калькулятор стоимости проезда."""

    def __init__(self):
        self._calc_data = None

    @abstractmethod
    def get_price_calculation_structure(self, args: dict[str, Any]) -> PriceCalculation:
        """Получение структуры для расчёта стоимости проезда.

        Args:
            args: сериализованные данные

        Returns: структура со значениями для расчёта стоимости
        """

    @abstractmethod
    def calculate_price(
        self,
        route: RouteSimilarity,
        departure_index: int,
        destination_index: int,
    ) -> float:
        """Базовый метод вычисления стоимости проезда.

        Args:
            route: рейс или маршрут
            departure_index: индекс пункта отправления
            destination_index: индекс пункта назначения

        Returns: высчитанная стоимость
        """
        if departure_index >= destination_index:
            raise SarmatWrongValueError(
                err_class=ErrorClass.DATA,
                title="Ошибка расчёта стоимости",
                description="Пункт отправления должен быть раньше пункта назначения",
            )

        route_len = len(route.structure)
        # NOTE: учитывается начальный пункт, который не присутствует в списке
        if max(departure_index, destination_index) > route_len:
            raise SarmatWrongValueError(
                err_class=ErrorClass.DATA,
                title="Ошибка расчёта стоимости",
                description="Указанный индекс превышает длительность маршрута",
            )

        if self._calc_data is None:
            raise SarmatWrongValueError(
                err_class=ErrorClass.DATA,
                title="Ошибка расчёта стоимости",
                description="Не указаны параметры расчёта стоимости",
            )
        return 0.0


class PriceCalculatorForConstant(PriceCalculator):
    """Калькулятор для расчёта стоимости по обычному способу."""

    def get_price_calculation_structure(self, args: dict[str, Any]) -> PriceCalculation:
        """Получение структуры для расчёта стоимости проезда.

        Args:
            args: сериализованные данные

        Returns: структура со значениями для расчёта стоимости
        """
        return PriceCalculationConstant(**args)

    def set_calculation_data(self, calc_data: PriceCalculationConstant) -> None:
        """Указание расчётных данных."""
        self._calc_data = calc_data

    def calculate_price(
        self,
        route: RouteSimilarity,
        departure_index: int,
        destination_index: int,
    ) -> float:
        """Базовый метод вычисления стоимости проезда.

        Args:
            route: рейс или маршрут
            departure_index: индекс пункта отправления
            destination_index: индекс пункта назначения

        Returns: высчитанная стоимость
        """
        super().calculate_price(route, departure_index, destination_index)
        return self._calc_data.values_map[departure_index][destination_index]


class PriceCalculatorForRate(PriceCalculator):
    """Калькулятор для расчёта стоимости по тарифу за пройденное расстояние."""

    def get_price_calculation_structure(self, args: dict[str, Any]) -> PriceCalculation:
        """Получение структуры для расчёта стоимости проезда.

        Args:
            args: сериализованные данные

        Returns: структура со значениями для расчёта стоимости
        """
        return PriceCalculationRate(**args)

    def set_calculation_data(self, calc_data: PriceCalculationRate) -> None:
        """Указание расчётных данных."""
        self._calc_data = calc_data

    def calculate_price(
        self,
        route: RouteSimilarity,
        departure_index: int,
        destination_index: int,
    ) -> float:
        """Базовый метод вычисления стоимости проезда.

        Args:
            route: рейс или маршрут
            departure_index: индекс пункта отправления
            destination_index: индекс пункта назначения

        Returns: высчитанная стоимость
        """
        super().calculate_price(route, departure_index, destination_index)
        sub_route = slice(departure_index, destination_index)
        amount = 0.0
        for item in route.structure[sub_route]:
            amount += self._calc_data.rate * item.length_from_last_km

        return amount


class PriceCalculatorForStep(PriceCalculator):
    """Калькулятор для расчёта стоимости по зонному тарифу."""

    def get_price_calculation_structure(self, args: dict[str, Any]) -> PriceCalculation:
        """Получение структуры для расчёта стоимости проезда.

        Args:
            args: сериализованные данные

        Returns: структура со значениями для расчёта стоимости
        """
        return PriceCalculationStep(**args)

    def set_calculation_data(self, calc_data: PriceCalculationStep) -> None:
        """Указание расчётных данных."""
        self._calc_data = calc_data

    def calculate_price(
            self,
            route: RouteSimilarity,
            departure_index: int,
            destination_index: int,
    ) -> float:
        """Базовый метод вычисления стоимости проезда.

        Args:
            route: рейс или маршрут
            departure_index: индекс пункта отправления
            destination_index: индекс пункта назначения

        Returns: высчитанная стоимость
        """
        super().calculate_price(route, departure_index, destination_index)
        sub_route = slice(departure_index, destination_index)
        traveled_distance = sum(
            [item.length_from_last_km for item in route.structure[sub_route]]
        )
        steps = [(traveled_distance, 0)] + [
            (distance, value) for distance, value in self._calc_data.steps.items()
        ]
        # NOTE: сортировка по обратным величинам стоимости
        #       позволяет при совпадении пройденного расстояния с табличным
        #       отодвинуть вставленный элемент вправо
        #       и не получить нулевую стоимость проезда
        length, values = zip(*sorted(steps, key=lambda x: (x[0], -x[1])))
        idx = length.index(traveled_distance)

        delta = 0
        if not idx:
            delta += 1
        elif idx == len(length) - 1:
            delta = -1
        corner_case = bool(delta)

        return values[idx+delta] if corner_case else max(values[idx], values[idx+1])
