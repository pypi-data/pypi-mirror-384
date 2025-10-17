"""
Sarmat.
Описание сущностей.
Базовый класс для описания моделей.
"""
from dataclasses import asdict, dataclass, fields
from typing import Any

from sarmat.core.constants import DurationType, IntervalType


@dataclass
class BaseModel:

    @property
    def sarmat_fields(self):
        return [fld.name for fld in fields(self)]

    @property
    def as_dict(self):
        return asdict(self)


@dataclass
class BaseIdModel:

    id: int = 0


@dataclass
class BaseUidModel:

    uid: str = ""


@dataclass
class BaseCatalogModel:
    """Базовая модель для описания справочников."""

    cypher: str     # шифр (константа)
    name: str       # название


@dataclass
class CustomAttributesModel:

    custom_attributes: dict[str, Any] | None = None

    @property
    def custom_fields(self) -> list[str]:
        return list(self.custom_attributes.keys()) if self.custom_attributes else []


@dataclass
class PersonModel(BaseModel):
    """Данные человека."""

    last_name: str      # фамилия
    first_name: str     # имя
    middle_name: str    # отчество
    male: bool          # пол: М


@dataclass
class BaseOrganizationModel(BaseModel):
    """Описание организации. Базовый класс."""

    name: str   # наименование организации


@dataclass
class OrganizationModel(BaseIdModel, CustomAttributesModel, BaseOrganizationModel):
    """Описание организации."""


@dataclass
class DurationItemModel(BaseModel):
    """Базовый элемент для описания продолжительности."""

    duration_type: DurationType     # тип продолжительности
    value: int                      # значение
    in_activity: bool               # признак активной фазы
    position: int = 0               # номер в последовательности
    id: int = 0                     # идентификатор записи


@dataclass
class DurationModel(BaseIdModel, CustomAttributesModel, BaseCatalogModel):
    """Составная модель с описанием продолжительности."""

    values: list[DurationItemModel] | None = None    # последовательность из отрезков времени


@dataclass
class IntervalItemModel(BaseModel):
    """Базовая модель для описания интервала."""

    interval_type: IntervalType     # тип интервала
    values: list[int]               # список значений
    in_activity: bool               # признак активной фазы
    position: int = 0               # номер в последовательности
    id: int = 0                     # идентификатор записи


@dataclass
class IntervalModel(BaseIdModel, CustomAttributesModel, BaseCatalogModel):
    """Составная модель с описанием интервала."""

    values: list[IntervalItemModel] | None = None     # описание сложного интервала
