"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Модели.
Диспетчерские объекты.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from sarmat.core.constants import JourneyClass, JourneyState

from .sarmat_models import BaseIdModel, BaseModel, BaseUidModel, CustomAttributesModel, IntervalModel
from .traffic_management_models import DestinationPointModel, JourneyModel, StationModel
from .vehicle_models import PermitModel


@dataclass
class BaseJourneyIntervalModel(BaseModel):
    """График выполнения рейсов (основные атрибуты)"""

    journey: JourneyModel       # рейс
    start_date: date            # дата начала
    interval: IntervalModel     # интервал движения


@dataclass
class JourneyIntervalModel(BaseIdModel, CustomAttributesModel, BaseJourneyIntervalModel):
    """График выполнения рейсов"""


@dataclass
class BaseJourneyProgressModel(BaseModel):
    """Атрибуты рейсовой ведомости (основные атрибуты класса)"""

    depart_date: date           # дата отправления в рейс
    journey: JourneyModel       # рейс
    permit: PermitModel         # номер путевого листа


@dataclass
class JourneyProgressModel(BaseUidModel, CustomAttributesModel, BaseJourneyProgressModel):
    """Атрибуты рейсовой ведомости"""


@dataclass
class BaseJourneyScheduleModel(BaseModel):
    """Процесс прохождения рейса по автоматизированным точкам (основные атрибуты)"""

    journey_progress: JourneyProgressModel                       # рейсовая ведомость
    journey_class: JourneyClass                                  # классификация рейса в данном пункте
    station: Optional[StationModel]                              # станция
    point: Optional[DestinationPointModel]                       # точка прохождения маршрута
    state: JourneyState                                          # состояние рейса
    plan_arrive: Optional[datetime] = None                       # плановое время прибытия
    fact_arrive: Optional[datetime] = None                       # фактическое время прибытия
    plan_depart: Optional[datetime] = None                       # плановое время отправления
    fact_depart: Optional[datetime] = None                       # фактическое время отправления
    platform: str = ''                                           # платформа
    comment: str = ''                                            # комментарий к текущему пункту
    last_items: Optional[List['JourneyScheduleModel']] = None    # оставшиеся активные пункты прохождения рейса


@dataclass
class JourneyScheduleModel(BaseUidModel, CustomAttributesModel, BaseJourneyScheduleModel):
    """Процесс прохождения рейса по автоматизированным точкам"""
