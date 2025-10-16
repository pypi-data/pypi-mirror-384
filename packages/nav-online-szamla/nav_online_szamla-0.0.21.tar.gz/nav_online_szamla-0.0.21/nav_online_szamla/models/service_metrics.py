from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from nav_online_szamla.models.common import BasicResultType

__NAMESPACE__ = "http://schemas.nav.gov.hu/OSA/3.0/metrics"


class LanguageType(Enum):
    """
    Nyelv megnevezés típus Language naming type.

    :cvar HU: Magyar nyelv Hungarian language
    :cvar EN: Angol nyelv English language
    :cvar DE: Német nyelv German language
    """

    HU = "HU"
    EN = "EN"
    DE = "DE"


class MetricTypeType(Enum):
    """
    Metrika típusának leírója Metric's descriptor type.

    :cvar COUNTER: Növekmény típusú metrika Incremental type metric
    :cvar GAUGE: Pillanatkép típusú metrika Snapshot type metric
    :cvar HISTOGRAM: Kvantilis típusú, eloszlást mérő metrika Quantile
        type, dispersion sampler metric
    :cvar SUMMARY: Összegző érték típusú metrika Sum value type metric
    """

    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    SUMMARY = "SUMMARY"


@dataclass
class MetricValueType:
    """
    Metrika érték típus Metric value type.

    :ivar value: Metrika értéke Metric's value
    :ivar timestamp: Metrika értékének időpontja UTC időben Time of
        metric value in UTC time
    """

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
        },
    )
    timestamp: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )


@dataclass
class MetricDescriptionType:
    """
    Metrika leírás típus Metric description type.

    :ivar language: Nyelv megnevezés Language naming
    :ivar localized_description: Lokalizált leírás Localized description
    """

    language: Optional[LanguageType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
        },
    )
    localized_description: Optional[str] = field(
        default=None,
        metadata={
            "name": "localizedDescription",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class MetricDefinitionType:
    """
    Metrika definíció típus Metric definition type.

    :ivar metric_name: Metrika neve Metric's name
    :ivar metric_type: Metrika típusa Metric's type
    :ivar metric_description: Metrika leírása Metric's description
    """

    metric_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "metricName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
            "min_length": 1,
            "max_length": 200,
            "pattern": r".*[^\s].*",
        },
    )
    metric_type: Optional[MetricTypeType] = field(
        default=None,
        metadata={
            "name": "metricType",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
        },
    )
    metric_description: list[MetricDescriptionType] = field(
        default_factory=list,
        metadata={
            "name": "metricDescription",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "min_occurs": 3,
            "max_occurs": 3,
        },
    )


@dataclass
class MetricType:
    """
    Metrika típus Metric data type.

    :ivar metric_definition: Metrika definíció Metric definition
    :ivar metric_values: Metrika értékek Metric values
    """

    metric_definition: Optional[MetricDefinitionType] = field(
        default=None,
        metadata={
            "name": "metricDefinition",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
        },
    )
    metric_values: list[MetricValueType] = field(
        default_factory=list,
        metadata={
            "name": "metricValues",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "max_occurs": 60,
        },
    )


@dataclass
class QueryServiceMetricsListResponseType:
    """
    A GET /queryServiceMetrics/list REST operáció válasz típusa Response type of
    the GET /queryServiceMetrics/list REST operation.

    :ivar metric_definition: Metrika definíciói Metric definitions
    """

    metric_definition: list[MetricDefinitionType] = field(
        default_factory=list,
        metadata={
            "name": "metricDefinition",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
        },
    )


@dataclass
class QueryServiceMetricsListResponse(QueryServiceMetricsListResponseType):
    """
    A GET /queryServiceMetrics/list REST operáció válaszának root elementje
    Response root element of the GET /queryServiceMetrics/list REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/metrics"


@dataclass
class QueryServiceMetricsResponseType:
    """
    A GET /queryServiceMetrics REST operáció válasz típusa Response type of the GET
    /queryServiceMetrics REST operation.

    :ivar result: Alap válaszeredmény adatok Basic result data
    :ivar metrics_last_update_time: A metrikák utolsó frissítésének
        időpontja UTC időben Last update time of metrics in UTC time
    :ivar metric: Metrika adatai Metric data
    """

    result: Optional[BasicResultType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "required": True,
        },
    )
    metrics_last_update_time: Optional[str] = field(
        default=None,
        metadata={
            "name": "metricsLastUpdateTime",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    metric: list[MetricType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/metrics",
        },
    )


@dataclass
class QueryServiceMetricsResponse(QueryServiceMetricsResponseType):
    """
    A GET /queryServiceMetrics REST operáció válaszának root elementje Response
    root element of the GET /queryServiceMetrics REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/metrics"
