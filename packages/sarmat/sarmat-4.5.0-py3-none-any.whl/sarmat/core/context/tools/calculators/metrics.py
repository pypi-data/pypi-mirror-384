"""
Sarmat.
Ядро пакета.
Описание бизнес логики.
Вспомогательные инструменты.
Вычисления с участием Sarmat объектов.
Вычисление метрик.
"""
from sarmat.core.constants import RouteType
from sarmat.core.context.models import RouteMetrics

from .const import MetricsSource


def calculate_route_metrics(source: MetricsSource) -> RouteMetrics:
    """Вычисление метрики для маршрута или рейса.

    Args:
        source: JourneyModel | RouteModel - маршрут или рейс

    Returns: метрика
    """
    last_item = source.structure[-1]

    # Для кольцевых маршрутов последний пункт совпадает с начальным,
    #    поэтому вычислять фактическое имя маршрута не имеет смысла
    if source.route_type == RouteType.CIRCLE:
        route_name = source.name
    else:
        route_name = f"{source.start_point.name} - {last_item.point.name}"

    metrics = RouteMetrics(
        fact_route_name=route_name,
        points_count=len(source.structure),
        total_length=last_item.length_from_last_km,
        spent_time=last_item.travel_time_min,
        move_time=last_item.travel_time_min,
        stop_time=0,
    )

    for item in source.structure[:-1]:
        metrics.total_length += item.length_from_last_km
        metrics.spent_time += (item.travel_time_min + (item.stop_time_min or 0))
        metrics.move_time += item.travel_time_min
        metrics.stop_time += item.stop_time_min or 0

    return metrics
