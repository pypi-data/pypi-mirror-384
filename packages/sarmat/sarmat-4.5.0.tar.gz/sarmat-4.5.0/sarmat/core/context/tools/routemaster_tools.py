"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Вспомогательные инструменты.
Инструменты для маршрутной сети.
"""
from datetime import (
    UTC,
    date,
    datetime,
    time,
    timedelta,
)
from typing import Generator

from sarmat.core.constants.exception_constants import (
    ErrorClass,
    SarmatWrongValueError,
)
from sarmat.core.constants.sarmat_constants import (
    DurationMonthCalcStrategy,
    JourneyType,
    RouteType,
)
from sarmat.core.context.models import (
    DurationModel,
    JourneyItemModel,
    JourneyModel,
    RouteItemModel,
    RouteModel,
)
from sarmat.core.context.tools.calculators import get_timedelta_from_duration

# Последовательность, возвращаемая генератором для определения последнего пункта в составе маршрута
RouteSeq = tuple[list[RouteItemModel], bool]


def make_journeys_from_route(
    route: RouteModel,
    departure_time: time,
    pauses: list[DurationModel],
    departure_date: date,
    duration_calc_strategy: DurationMonthCalcStrategy,
) -> list[JourneyModel]:
    """Создание рейсов на основе шаблона (маршрута).

    Args:
        route: RouteModel - маршрут
        departure_time: time (UTC) - время отправления для первого рейса
        pauses: list[DurationModel] - список пауз между рейсами
        departure_date: date - расчётная дата отправления (для расчёта продолжительности в месяцы или годы)
        duration_calc_strategy: DurationMonthCalcStrategy - стратегия переноса дней в конце месяца

    Returns: list[JourneyModel] - список построенных маршрутов

    Если маршрут задан как "кольцевой", то точки перелома в составе маршрута не учитываются.
    Будет создан один рейс.
    Выполняется проверка того, что последний пункт в составе маршрута совпадает с пунктом отправления.

    Для оборотных маршрутов:
     - если точка перелома не задана, то будет создан один рейс. Актуально для заказных перевозок.
     - если одна точка перелома указана для последнего пункта в составе маршрута,
       то будут построены два рейса с противоположным составом маршрута.
     - если переломных точек несколько, то будет создано несколько рейсов: от точки до точки.
     - если последний пункт не является переломной точкой, то обратные рейсы не строятся

     Список пауз используется для обозначения перерывов между рейсами.
     Ко времени завершения предыдущего рейса будет добавлена указанная продолжительность,
       чтобы вычислить время отправления следующего рейса.
     Если продолжительность не указана, то время отправления следующего рейса
       будет совпадать со временем завершения предыдущего рейса.

    """
    datetime_counter = datetime.combine(
        departure_date,
        departure_time,
        tzinfo=UTC,
    )
    journey_comment = f"Создан на основе маршрута {route.id} ({route.name})"
    pauses_gen = (i for i in pauses)
    journeys_list = []

    # Создание рейса на основе кольцевого маршрута
    if route.route_type == RouteType.CIRCLE:
        if route.start_point.id != route.structure[-1].point.id:
            raise SarmatWrongValueError(
                err_class=ErrorClass.DATA,
                title="Ошибка создания рейса",
                description="Последний пункт кольцевого маршрута должен соответствовать начальному пункту",
            )
        # Создание рейсов по количеству оборотов маршрута
        first_item = RouteItemModel(
            length_from_last_km=0,
            travel_time_min=0,
            point=route.start_point,
            position=0,
            station=route.departure_station,
        )
        route_items = [first_item] + route.structure
        for _ in range(route.turnovers):
            journey, datetime_counter = create_journey_from_route(
                route,
                datetime_counter,
                route_items,
                journey_comment,
            )
            journeys_list.append(journey)
            datetime_counter = apply_time_delta_to_start_date(
                datetime_counter,
                pauses_gen,
                duration_calc_strategy,
            )
    else:
        need_to_build_turnovers = False
        # общее количество рейсов в прямом и обратном направлении
        # будет равно количеству рейсов в одном круге, помноженному на количество оборотов
        for _ in range(route.turnovers):
            turnover_items = []
            first_item = RouteItemModel(
                length_from_last_km=0,
                travel_time_min=0,
                point=route.start_point,
                position=0,
                station=route.departure_station,
            )
            # обход состава маршрута в прямом направлении
            for sub_structure, is_final in route_structure_gen(route.structure):
                route_items = [first_item] + sub_structure
                journey, datetime_counter = create_journey_from_route(
                    route,
                    datetime_counter,
                    route_items,
                    journey_comment,
                )
                journeys_list.append(journey)
                turnover_items.append(route_items[::-1])
                datetime_counter = apply_time_delta_to_start_date(
                    datetime_counter,
                    pauses_gen,
                    duration_calc_strategy,
                )
                first_item = RouteItemModel(
                    length_from_last_km=0,
                    travel_time_min=0,
                    point=sub_structure[-1].point,
                    position=0,
                    station=sub_structure[-1].station,
                )
                if is_final:
                    need_to_build_turnovers = sub_structure[-1].is_breaking_point

            if need_to_build_turnovers:
                # обход состава маршрута в обратном направлении
                for sub_structure in turnover_items[::-1]:
                    journey, datetime_counter = create_journey_from_route(
                        route,
                        datetime_counter,
                        sub_structure,
                        journey_comment,
                    )
                    journeys_list.append(journey)
                    datetime_counter = apply_time_delta_to_start_date(
                        datetime_counter,
                        pauses_gen,
                        duration_calc_strategy,
                    )

    return journeys_list


def create_journey_from_route(
    route: RouteModel,
    start_time: datetime,
    items: list[RouteItemModel],
    comment: str = "",
) -> tuple[JourneyModel, datetime]:
    """Вспомогательная функция по созданию рейса из маршрута.

    Args:
        route: RouteModel - маршрут
        start_time: datetime - дата и время отправления рейса
        items: list[RouteItemModel] - состав маршрута
        comment: str - комментарий к рейсу

    Returns: JourneyModel, datetime - модель рейса и дата с приращением времени выполнения рейса

    """

    if not items:
        raise SarmatWrongValueError(
            err_class=ErrorClass.DATA,
            title="Ошибка построения рейса",
            description="Пункт отправления и состав маршрута должны быть определены",
        )
    start_point, *structure = items
    if not structure:
        raise SarmatWrongValueError(
            err_class=ErrorClass.DATA,
            title="Ошибка построения рейса",
            description="Состав маршрута должны быть определён",
        )

    current_time = start_time
    new_journey = JourneyModel(
        route_type=route.route_type,
        name=f"{start_point.point.name} - {structure[-1].point.name}",
        start_point=start_point.point,
        departure_station=start_point.station,
        direction=route.direction,
        comments=comment,
        journey_type=JourneyType.LONG_DISTANCE,
        departure_time=current_time.time(),
        structure=[],
    )

    for idx, item in enumerate(structure):
        current_time += timedelta(minutes=item.travel_time_min)
        stop_time = item.stop_time_min or 0

        new_journey.structure.append(
            JourneyItemModel(
                departure_time=(current_time + timedelta(minutes=stop_time)).time(),
                arrive_time=current_time.time(),
                length_from_last_km=item.length_from_last_km,
                travel_time_min=item.travel_time_min,
                point=item.point,
                position=idx,
                station=item.station,
                stop_time_min=item.stop_time_min,
            )
        )
        current_time += timedelta(minutes=stop_time)

    # В последнем пункте время отправления не нужно
    new_journey.structure[-1].departure_time = None
    return new_journey, current_time


def route_structure_gen(route_structure: list[RouteItemModel]) -> Generator[RouteSeq, None, None]:
    """Генератор для разбиения состава маршрута по точкам перелома.

    Args:
        route_structure: list[RouteItemModel] - элементы из состава маршрута

    Returns: генератор, разбирающий состав маршрута по точкам перелома.

    """
    sub_route = []
    item_last_idx = len(route_structure) - 1

    for idx, item in enumerate(route_structure):
        sub_route.append(item)
        if item.is_breaking_point:
            yield sub_route, idx == item_last_idx
            sub_route = []

    if sub_route:
        yield sub_route, True


def apply_time_delta_to_start_date(
    departure_datetime: datetime,
    pauses_gen: Generator[DurationModel, None, None],
    duration_calc_strategy: DurationMonthCalcStrategy,
) -> datetime:
    """Приращение по времени для определения времени отправления для следующего рейса.

    Args:
        departure_datetime: datetime - дата и время отправления
        pauses_gen: Generator - генератор продолжительностей
        duration_calc_strategy: DurationMonthCalcStrategy - стратегия расчёта переноса дней

    Returns: datetime - дата и время с приращением времени из очередного элемента продолжительности

    """
    try:
        pause = next(pauses_gen)
    except StopIteration:
        return departure_datetime

    return departure_datetime + get_timedelta_from_duration(
        duration=pause,
        calculation_date=departure_datetime.date(),
        calc_strategy=duration_calc_strategy,
        only_active=False,
    )
