"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Модели.
Модели для построения маршрутной сети.
"""
from dataclasses import dataclass
from datetime import time, date

from sarmat.core.constants import JourneyType, RoadType, RouteType, StationType

from .geo_models import DirectionModel, DestinationPointModel, RoadNameModel
from .sarmat_models import BaseIdModel, BaseModel, CustomAttributesModel, DurationModel


@dataclass
class BaseStationModel(BaseModel):
    """Станции (пункты посадки-высадки пассажиров) (основные атрибуты)."""

    station_type: StationType           # тип станции
    name: str                           # наименование
    point: DestinationPointModel        # ближайший населенный пункт
    address: str = ''                   # почтовый адрес


@dataclass
class StationModel(BaseIdModel, CustomAttributesModel, BaseStationModel):
    """Станции (пункты посадки-высадки пассажиров)."""


@dataclass
class BaseRoadModel(BaseModel):
    """Дороги (основные атрибуты)."""

    start_point: DestinationPointModel          # начало дороги
    end_point: DestinationPointModel            # конец дороги
    direct_travel_time_min: int                 # время прохождения в прямом направлении
    reverse_travel_time_min: int                # время прохождения в обратном направлении
    direct_len_km: float                        # расстояние в прямом направлении
    reverse_len_km: float                       # расстояние в обратном направлении
    road_type: RoadType                         # тип дорожного покрытия
    road_name: RoadNameModel | None = None      # классификация дороги


@dataclass
class RoadModel(BaseIdModel, CustomAttributesModel, BaseRoadModel):
    """Дороги."""


@dataclass
class BaseRouteItemModel(BaseModel):
    """Состав маршрута (основные атрибуты)."""

    length_from_last_km: float              # расстояние от предыдущего пункта
    travel_time_min: int                    # время движения от предыдущего пункта в минутах
    point: DestinationPointModel            # точка прохождения маршрута
    position: int = 1                       # порядок следования
    station: StationModel | None = None     # станция
    stop_time_min: int | None = None        # время стоянки в минутах
    road: RoadModel | None = None           # дорога


@dataclass
class RouteItemModel(BaseIdModel, CustomAttributesModel, BaseRouteItemModel):
    """Состав маршрута."""

    is_breaking_point: bool = False     # точка перелома маршрута (начало следующего рейса)


@dataclass
class CommonRouteModel(BaseModel):
    """Общие атрибуты для маршрута и рейса."""

    route_type: RouteType                           # тип маршрута
    name: str                                       # наименование
    start_point: DestinationPointModel              # точка отправления
    departure_station: StationModel | None = None   # станция отправления
    direction: list[DirectionModel] | None = None   # направления
    comments: str | None = None                     # комментарий к маршруту
    number: int | None = None                       # номер маршрута
    literal: str = ''                               # литера
    is_active: bool = True                          # признак активности маршрута


@dataclass
class BaseRouteModel(BaseModel):
    """Описание маршрута (основные атрибуты)."""

    structure: list[RouteItemModel]     # состав маршрута


@dataclass
class RouteModel(BaseIdModel, CustomAttributesModel, CommonRouteModel, BaseRouteModel):
    """Описание маршрута."""

    turnovers: int = 1      # количество оборотов по маршруту


@dataclass
class JourneyItemModel(BaseIdModel, CustomAttributesModel, BaseRouteItemModel):
    """Состав рейса."""

    departure_time: time | None = None      # время отправления из пункта
    arrive_time: time | None = None         # время прибытия в пункт


@dataclass
class BaseJourneyModel(BaseModel):
    """Атрибуты рейса (основные атрибуты)."""

    journey_type: JourneyType           # тип рейса
    departure_time: time                # время отправления
    structure: list[JourneyItemModel]   # структура рейса


@dataclass
class JourneyModel(BaseIdModel, CustomAttributesModel, CommonRouteModel, BaseJourneyModel):
    """Атрибуты рейса"""

    is_chartered: bool = False          # признак заказного рейса
    need_control: bool = False          # признак именной продажи и мониторинга
    season_begin: date | None = None    # начало сезона
    season_end: date | None = None      # окончание сезона


@dataclass
class RouteMetrics:
    """Описание метрики маршрута или рейса."""

    fact_route_name: str    # фактическое название маршрута
    points_count: int       # количество пунктов в составе
    total_length: float     # общая протяжённость маршрута
    spent_time: int         # затраченное время в минутах
    move_time: int          # время в движении
    stop_time: int          # время стоянки на промежуточных пунктах


@dataclass
class BaseJourneyBunchItemModel(BaseModel):
    """Атрибуты элемента из связки рейсов (основные атрибуты)"""

    journey: JourneyModel           # рейс
    stop_duration: DurationModel    # время простоя
    position: int                   # номер в последовательности


@dataclass
class JourneyBunchItemModel(BaseIdModel, CustomAttributesModel, BaseJourneyBunchItemModel):
    """Атрибуты элемента из связки рейсов"""


@dataclass
class BaseJourneyBunchModel(BaseModel):
    """Атрибуты связки рейсов (основные атрибуты)"""

    journeys: list[JourneyBunchItemModel]   # элементы связки


@dataclass
class JourneyBunchModel(BaseIdModel, CustomAttributesModel, BaseJourneyBunchModel):
    """Атрибуты связки рейсов"""

    name: str | None = None                 # наименование связки
