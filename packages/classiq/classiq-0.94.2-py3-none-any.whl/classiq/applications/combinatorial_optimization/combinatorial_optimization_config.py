import dataclasses
from dataclasses import dataclass

from classiq.interface.executor.optimizer_preferences import CostType, OptimizerType


@dataclass
class QAOAConfig:
    num_layers: int = 2
    penalty_energy: float = 2.0


@dataclass
class OptimizerConfig:
    opt_type: OptimizerType = OptimizerType.COBYLA
    max_iteration: int | None = None
    tolerance: float = 0.0
    step_size: float = 0.0
    skip_compute_variance: bool = False
    cost_type: CostType = CostType.CVAR
    alpha_cvar: float = 1.0
    initial_point: list[float] | None = dataclasses.field(default=None)
