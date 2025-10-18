# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union
from typing_extensions import TypeAlias

from .usage_data_export_schedule_response import UsageDataExportScheduleResponse
from .operational_data_export_schedule_response import OperationalDataExportScheduleResponse

__all__ = ["ScheduleUpdateResponse"]

ScheduleUpdateResponse: TypeAlias = Union[OperationalDataExportScheduleResponse, UsageDataExportScheduleResponse]
