"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Модели.
Подвижной состав.
"""
from dataclasses import dataclass
from datetime import date
from typing import List

from sarmat.core.constants import CrewType, PermitType, VehicleType

from .sarmat_models import PersonModel, BaseIdModel, BaseUidModel, BaseModel, CustomAttributesModel


@dataclass
class BaseSeatRow:
    """Базовый класс для описания рядов."""

    sequence: int


@dataclass
class SeatsRow(BaseIdModel, BaseSeatRow):
    """Ряд сидений в транспортном средстве."""

    a: int = 0
    b: int = 0
    c: int = 0
    d: int = 0
    e: int = 0


@dataclass
class BaseVehicleTemplateModel(BaseModel):
    """Модель транспортного средства (основные атрибуты)."""

    vehicle_type: VehicleType  # тип транспортного средства
    vehicle_name: str  # марка транспортного средства
    seats: int  # количество мест для посадки


@dataclass
class VehicleCommonModels:
    """Общие атрибуты для подпижного состава и шаблона."""

    stand: int = 0  # количество мест стоя
    capacity: int = 0   # вместимость багажного отделения
    seats_map: list[SeatsRow] | None = None     # схема расположения мест


@dataclass
class VehicleTemplateModel(BaseIdModel, CustomAttributesModel, VehicleCommonModels, BaseVehicleTemplateModel):
    """Модель транспортного средства (шаблон для создания подвижного состава)."""


@dataclass
class BaseVehicleModel(BaseVehicleTemplateModel):
    """Подвижной состав (основные атрибуты)."""

    state_number: str           # регистрационный номер


@dataclass
class VehicleModel(BaseIdModel, CustomAttributesModel, VehicleCommonModels, BaseVehicleModel):
    """Подвижной состав."""


@dataclass
class BaseCrewModel(BaseModel):
    """Экипаж (основные атрибуты)."""

    crew_type: CrewType     # тип члена экипажа
    is_main: bool = True    # признак главного члена экипажа


@dataclass
class CrewModel(BaseIdModel, CustomAttributesModel, BaseCrewModel, PersonModel):
    """Экипаж."""


@dataclass
class BasePermitModel(BaseModel):
    """Путевой лист (основные атрибуты)"""

    number: str                     # номер путевого листа
    permit_type: PermitType         # тип путевого листа
    depart_date: date               # дата выезда
    crew: List[CrewModel]           # экипаж
    vehicle: List[VehicleModel]     # подвижной состав


@dataclass
class PermitModel(BaseUidModel, CustomAttributesModel, BasePermitModel):
    """Путевой лист"""
