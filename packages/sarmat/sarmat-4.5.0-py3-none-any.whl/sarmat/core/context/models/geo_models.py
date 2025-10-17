"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Модели.
Модели для описания географических объектов.
"""
from dataclasses import dataclass
from typing import Self

from sarmat.core.constants import LocationType, SettlementType

from .sarmat_models import BaseIdModel, BaseModel, CustomAttributesModel


@dataclass
class BaseGeoModel(BaseModel):
    """Модель географического справочника (основные атрибуты)"""

    name: str                           # наименование
    location_type: LocationType         # тип образования
    latin_name: str = ""                # латинское название
    mapping_data: dict | None = None    # данные геолокации
    tags: str = ''                      # теги
    parent: Self | None = None          # родительский объект


@dataclass
class GeoModel(BaseIdModel, CustomAttributesModel, BaseGeoModel):
    """Модель географического справочника"""


@dataclass
class BaseDestinationPointModel(BaseModel):
    """Модель для описания пунктов назначения (основные атрибуты)"""

    name: str                       # наименование
    state: GeoModel                 # территориальное образование
    point_type: SettlementType      # тип поселения


@dataclass
class DestinationPointModel(BaseIdModel, CustomAttributesModel, BaseDestinationPointModel):
    """Модель для описания пунктов назначения"""


@dataclass
class BaseDirectionModel(BaseModel):
    """Модель для описания направления (основные атрибуты)"""

    name: str           # наименование
    cypher: str = ""    # шифр (системное имя)


@dataclass
class DirectionModel(BaseIdModel, CustomAttributesModel, BaseDirectionModel):
    """Модель для описания направления"""


@dataclass
class BaseRoadNameModel(BaseModel):
    """Модель для описания дороги (основные атрибуты)"""

    cypher: str
    name: str = ''


@dataclass
class RoadNameModel(BaseIdModel, CustomAttributesModel, BaseRoadNameModel):
    """Модель для описания дороги"""
