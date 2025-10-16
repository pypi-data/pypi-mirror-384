from typing import Any

from bigeye_cli.enums import VersionControlReportType
from bigeye_cli.exceptions import InvalidConfigurationException
from bigeye_sdk.model.delta_facade import SimpleDeltaConfiguration
from bigeye_sdk.serializable import File


class DeltaCicdConf(SimpleDeltaConfiguration):
    vendor: str = None
    report_type: VersionControlReportType = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.vendor is None:
            raise InvalidConfigurationException("Version control vendor must be specified for CICD configuration.")
        self.report_type = VersionControlReportType[self.vendor.upper()]


class SimpleDeltaCicdConfigFile(File, type='DELTA_CICD_CONFIG_FILE'):
    cicd_conf: DeltaCicdConf
