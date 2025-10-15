from datetime import datetime
from typing import Annotated, Literal, Union

import pydantic
from pydantic import BaseModel, Field

from classiq.interface.executor.estimation import OperatorsEstimation
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.executor.quantum_code import QuantumCode
from classiq.interface.generator.quantum_program import QuantumProgram
from classiq.interface.helpers.custom_encoders import CUSTOM_ENCODERS
from classiq.interface.helpers.versioned_model import VersionedModel
from classiq.interface.jobs import JobStatus


class QuantumProgramExecution(QuantumProgram):
    execution_type: Literal["quantum_program2"] = "quantum_program2"


class QuantumCodeExecution(QuantumCode):
    execution_type: Literal["quantum_code"] = "quantum_code"


class EstimateOperatorsExecution(OperatorsEstimation):
    execution_type: Literal["estimate_operators"] = "estimate_operators"


ExecutionPayloads = Annotated[
    Union[QuantumProgramExecution, QuantumCodeExecution, EstimateOperatorsExecution],
    Field(discriminator="execution_type"),
]


class ExecutionRequest(BaseModel, json_encoders=CUSTOM_ENCODERS):
    execution_payload: ExecutionPayloads
    preferences: ExecutionPreferences = pydantic.Field(
        default_factory=ExecutionPreferences,
        description="preferences for the execution",
    )


class QuantumProgramExecutionRequest(ExecutionRequest):
    execution_payload: QuantumCodeExecution


class ProviderJobs(BaseModel):
    provider_job_id: str = Field(default="DUMMY")
    cost: float = Field(default=0)


class JobCost(BaseModel):
    total_cost: float = Field(default=0)
    currency_code: str = Field(default="USD")
    organization: str | None = Field(default=None)
    jobs: list[ProviderJobs] = Field(default=[])


class ExecutionJobDetails(VersionedModel):
    id: str

    name: str | None = Field(default=None)
    start_time: datetime
    end_time: datetime | None = Field(default=None)

    provider: str | None = Field(default=None)
    backend_name: str | None = Field(default=None)

    status: JobStatus

    num_shots: int | None = Field(default=None)
    program_id: str | None = Field(default=None)

    error: str | None = Field(default=None)

    cost: JobCost | None = Field(default=None)


class ExecutionJobsQueryResults(VersionedModel):
    results: list[ExecutionJobDetails]
