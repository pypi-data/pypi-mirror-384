import enum
from typing import List

from bigeye_cli.model.github_report import GitHubReport
from bigeye_sdk.generated.com.bigeye.models.generated import PredefinedMetric, PredefinedMetricName

OPS_METRICS: List[PredefinedMetric] = [
    PredefinedMetric(metric_name=PredefinedMetricName.PERCENT_NULL),
    PredefinedMetric(metric_name=PredefinedMetricName.COUNT_NULL),
    PredefinedMetric(metric_name=PredefinedMetricName.PERCENT_EMPTY_STRING),
    PredefinedMetric(metric_name=PredefinedMetricName.PERCENT_DATE_NOT_IN_FUTURE),
    PredefinedMetric(metric_name=PredefinedMetricName.MAX),
    PredefinedMetric(metric_name=PredefinedMetricName.MIN),
    PredefinedMetric(metric_name=PredefinedMetricName.AVERAGE),
    PredefinedMetric(metric_name=PredefinedMetricName.COUNT_DUPLICATES),
    PredefinedMetric(metric_name=PredefinedMetricName.COUNT_DISTINCT),
    # PredefinedMetric(metric_name=PredefinedMetricName.HOURS_SINCE_MAX_TIMESTAMP) TODO Must have function that checks if this is the metric time.
]


class MetricFileType(enum.Enum):
    SIMPLE = 'SIMPLE'
    FULL = 'FULL'


class VersionControlReportType(enum.Enum):
    GITHUB = GitHubReport
