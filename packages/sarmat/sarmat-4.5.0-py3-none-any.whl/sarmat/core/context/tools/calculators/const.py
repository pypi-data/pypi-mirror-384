"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Вспомогательные инструменты.
Вычисления с участием Sarmat объектов.
Константы общего назначения.
"""
from typing import Union

from sarmat.core.context.models import (
    JourneyModel,
    RouteModel,
)

max_month_len = 31
months_in_year = 12

MetricsSource = Union[JourneyModel, RouteModel]
