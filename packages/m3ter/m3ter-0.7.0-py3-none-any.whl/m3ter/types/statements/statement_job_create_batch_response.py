# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .statement_job_response import StatementJobResponse

__all__ = ["StatementJobCreateBatchResponse"]

StatementJobCreateBatchResponse: TypeAlias = List[StatementJobResponse]
