"""
Bacterial Foraging Optimization (BFO) Optimizer for PyTorch
===========================================================

A production-grade, GPU-accelerated implementation of Bacterial Foraging
Optimization (BFO) with modern enhancements for deep learning and scientific
computing.

Based on Passino (2002) "Biomimicry of Bacterial Foraging for Distributed
Optimization and Control" with state-of-the-art improvements from recent
literature (2010-2024).

Key Enhancements Over Canonical BFO:
-----------------------------------
1. **Lévy Flight Exploration**: Mantegna (1994) algorithm for heavy-tailed
   exploration with adaptive linear-decreasing schedule (Chen et al. 2020)

2. **Normalized Chemotaxis**: Direction vectors normalized to unit length
   ensuring step_size parameter controls actual movement magnitude across
   all dimensions

3. **Vectorized Swimming**: GPU-optimized parallel swimming for all bacteria
   with per-bacterium termination for efficiency

4. **Adaptive Step Sizing**: Cosine annealing schedule with performance-based
   adjustments (improvement → increase, stagnation → decrease)

5. **Diversity-Based Elimination**: Adaptive elimination probability based on
   population diversity and convergence state (Chen et al. 2020)

6. **Smart Reinitialization**: Eliminated bacteria respawn near best solution
   with exploration noise (prevents loss of progress)

7. **Production Features**: Mixed precision support, device handling, early
   stopping, function evaluation budgets, state checkpointing

Mathematical Formulations:
-------------------------
Chemotaxis: θ(i,j+1) = θ(i,j) + C(i) × Δ(i)/||Δ(i)||
Lévy Flight: L ~ u/|v|^(1/α) where u~N(0,σ_u²), v~N(0,1), α∈[1,2]
Swarming: J_cc = -d×exp(-w_a×||Δ||²) + h×exp(-w_r×||Δ||²)
Reproduction: Keep top 50% by fitness, duplicate to replace bottom 50%
Elimination: P_ed adaptive based on diversity and stagnation

References:
----------
- Passino (2002): Original BFO algorithm
- Mantegna (1994): Lévy stable distributions
- Chen et al. (2020): Adaptive mechanisms and Lévy flight scheduling
- Multiple 2010-2024 papers: Diversity-based adaptations
"""

import logging
import math
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import torch
from torch.autograd.profiler import record_function
from torch.optim import Optimizer

try:  # torch.distributed may be optional in some environments
    import torch.distributed as dist  # type: ignore
except Exception:  # pragma: no cover - distributed backend unavailable
    dist = None  # type: ignore

try:  # PyTorch DTensor (PyTorch 2.7+)
    from torch.distributed.tensor import (  # type: ignore[attr-defined]
        DTensor,
        DeviceMesh,
        Replicate,
        Shard,
    )
    try:
        from torch.distributed.tensor import ops as dt_ops  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - ops module missing
        dt_ops = None  # type: ignore
except Exception:  # pragma: no cover - DTensor not available
    DTensor = None  # type: ignore
    DeviceMesh = None  # type: ignore
    Replicate = None  # type: ignore
    Shard = None  # type: ignore
    dt_ops = None  # type: ignore

try:  # Avoid circular import during typing / sphinx builds
    from .utils import make_generator_for_rank, resolve_distributed_context
except Exception:  # pragma: no cover - fallback if utils unavailable
    resolve_distributed_context = None  # type: ignore
    make_generator_for_rank = None  # type: ignore

try:  # Optional torch dynamo configuration helpers
    import torch._dynamo as _torch_dynamo  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - older PyTorch
    _torch_dynamo = None  # type: ignore

# Future: vectorized closure evaluation
# try:
#     from torch.func import functional_call, vmap
#     HAS_FUNCTORCH = True
# except ImportError:
#     HAS_FUNCTORCH = False
HAS_FUNCTORCH = False

logger = logging.getLogger(__name__)


@dataclass
class ShardMeta:
    """Describe shard placement for a DTensor-backed population."""

    global_start: int = 0
    global_end: int = 0
    global_count: int = 0
    global_size: int = 0
    world_size: int = 1
    rank: int = 0
    local_rank: int = 0
    devices_per_node: Optional[int] = None
    placements: Optional[Tuple[Any, ...]] = None
    mesh: Optional["DeviceMesh"] = None

    @property
    def slice(self) -> slice:
        return slice(self.global_start, self.global_end)


@dataclass
class BFOGroupState:
    """Structured container for the per-group optimizer state."""

    param_vector: torch.Tensor
    param_shapes: List[torch.Size]
    population: torch.Tensor
    best_params: torch.Tensor
    best_fitness: torch.Tensor
    prev_best_fitness: torch.Tensor
    current_step_size: torch.Tensor
    stagnation_count: torch.Tensor
    iteration: torch.Tensor
    dtype: torch.dtype
    fitness_history_buffer: torch.Tensor
    fitness_history_length: torch.Tensor
    function_evaluations: torch.Tensor
    population_dtensor: Optional["DTensor"] = None
    population_local: Optional[torch.Tensor] = None
    population_shard: Optional[ShardMeta] = None
    population_shape: torch.Size = torch.Size()
    clone_on_write: bool = True
    per_bacterium_step_size: Optional[torch.Tensor] = None
    batch_eval_rng: Optional[torch.Generator] = None
    distributed_context: Optional[Any] = None
    momentum_buffer: Optional[torch.Tensor] = None
    replicated_tensors: Dict[str, "DTensor"] = field(default_factory=dict)
    group_id: int = 0

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return hasattr(self, key)

    def update(self, mapping: Dict[str, Any]) -> None:
        for key, value in mapping.items():
            setattr(self, key, value)

class BFO(Optimizer):
    """
    Production-Grade Bacterial Foraging Optimization (BFO) for PyTorch.

    GPU-accelerated BFO with modern enhancements including Lévy flights,
    adaptive mechanisms, and diversity-based population management.

    Arguments:
        params (iterable): Parameters to optimize or dicts defining parameter groups
        lr (float): Base learning rate for parameter updates (default: 0.01)
        population_size (int): Number of bacteria in population. Larger = better
            exploration but more function evaluations (default: 50)
        chemotaxis_steps (int): Chemotactic steps per reproduction cycle. More steps
            = finer local search (default: 10)
        swim_length (int): Maximum consecutive swims in beneficial direction.
            Exploits good gradients (default: 4)
        reproduction_steps (int): Reproduction cycles per elimination step. Balances
            exploration vs exploitation (default: 4)
        elimination_steps (int): Full BFO cycles. More = longer optimization (default: 2)
        elimination_prob (float): Base elimination probability. Adapts based on
            diversity and stagnation (default: 0.25)
        step_size_min (float): Minimum chemotaxis step size (default: 1e-4)
        step_size_max (float): Maximum chemotaxis step size. Controls exploration
            radius (default: 0.1)
        levy_alpha (float): Lévy flight stability parameter. α∈[1,2] where 1=Cauchy,
            2=Gaussian. Default 1.5 balances exploration (default: 1.5)
        levy_schedule (str): Lévy step size schedule: 'constant', 'linear-decrease',
            'cosine'. Linear-decrease recommended (default: 'linear-decrease')
        step_schedule (str): Adaptive step size schedule: 'adaptive', 'cosine',
            'linear'. Adaptive adjusts based on improvement (default: 'adaptive')
        enable_swarming (bool): Enable cell-to-cell communication via attraction/
            repulsion forces (default: True)
        swarming_params (tuple): (d_attract, w_attract, h_repel, w_repel). Standard
            values: (0.1, 0.2, 0.1, 10.0) per Passino (2002) (default: (0.1, 0.2, 0.1, 10.0))
        normalize_directions (bool): Normalize chemotaxis directions to unit vectors.
            Essential for high-dimensional problems (default: True)
        global_respawn_ratio (float): Fraction of eliminated bacteria respawned globally
            (uniform across domain_bounds) vs locally (near best solution). Range [0.0, 1.0].
            Higher values improve escape from local minima on multimodal functions.
            Recommended: 0.5 for Rastrigin/Ackley, 0.25 for unimodal functions (default: 0.5)
        adaptive_global_respawn (bool): Dynamically adjust global_respawn_ratio based on
            population diversity. Low diversity triggers higher global respawn to escape
            local minima. Recommended: True for unknown problem landscapes (default: True)
        device (torch.device): Computation device. Auto-detected if None (default: None)
        compile_mode (str): torch.compile mode for JIT compilation: 'default',
            'reduce-overhead', 'max-autotune' (default: None)
        early_stopping (bool): Stop if converged (default: True)
        convergence_tolerance (float): Convergence threshold (default: 1e-6)
        convergence_patience (int): Steps without improvement before stopping (default: 10)
        seed (int): Random seed for reproducibility (default: None)
        domain_bounds (tuple): (min, max) parameter bounds for constraint handling (default: None)
        batch_eval_fn (callable): Optional callable for evaluating a population of
            candidates in a single vectorized/batched operation. Receives the
            tensor of shape (population_size, param_dim) and may accept keyword
            arguments `rng` (torch.Generator) and `shard` (metadata dict). Must
            return fitness values as a 1D tensor aligned with the population.
        history_window (int): Number of recent best-fitness values to retain on-device
            for adaptive schedules and diagnostics (default: 5).

    Example:
        >>> # Basic usage
        >>> optimizer = BFO(model.parameters(), lr=0.01, population_size=30)
        >>> def closure():
        >>>     optimizer.zero_grad()
        >>>     output = model(data)
        >>>     loss = criterion(output, target)
        >>>     return loss.item()
        >>> optimizer.step(closure)
        >>>
        >>> # Advanced: constrained optimization with budget
        >>> optimizer = BFO(
        >>>     model.parameters(),
        >>>     population_size=100,
        >>>     levy_schedule='linear-decrease',
        >>>     step_schedule='cosine',
        >>>     domain_bounds=(-1.0, 1.0),
        >>> )
        >>> optimizer.step(closure, max_fe=10000)
    """

    _EPS = 1e-12

    def __init__(
        self,
        params: Iterable[Union[torch.Tensor, Dict[str, Any]]],
        lr: float = 0.01,
        population_size: int = 50,
        chemotaxis_steps: int = 10,
        swim_length: int = 4,
        reproduction_steps: int = 4,
        elimination_steps: int = 2,
        elimination_prob: float = 0.25,
        step_size_min: float = 1e-4,
        step_size_max: float = 0.1,
        levy_alpha: float = 1.5,
        levy_schedule: str = "linear-decrease",
        step_schedule: str = "adaptive",
        enable_swarming: bool = True,
        swarming_params: Tuple[float, float, float, float] = (0.1, 0.2, 0.1, 10.0),
        normalize_directions: bool = True,
        global_respawn_ratio: float = 0.5,
        adaptive_global_respawn: bool = True,
        device: Optional[torch.device] = None,
        compile_mode: Optional[str] = None,
        early_stopping: bool = True,
        convergence_tolerance: float = 1e-6,
        convergence_patience: int = 10,
        seed: Optional[int] = None,
        domain_bounds: Optional[Tuple[float, float]] = None,
        batch_eval_fn: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
        history_window: int = 5,
        mesh_spec: Optional[Any] = None,
        checkpoint_strategy: str = "rank0_full",
        clone_on_write: bool = True,
        debug_sharding: bool = False,
        **kwargs,
    ):
        # Validation with helpful error messages
        if lr < 0.0:
            raise ValueError(
                f"Invalid learning rate: {lr}. Must be positive. "
                f"Try lr=0.01 as a starting point."
            )
        if population_size < 1:
            raise ValueError(
                f"Invalid population size: {population_size}. Must be >= 1. "
                f"Recommended: 20-100 for most problems."
            )
        if population_size < 10:
            logger.warning(
                f"Small population_size={population_size} may struggle with exploration. "
                f"Consider population_size >= 20 for problems with >5 dimensions."
            )
        if not (0.0 < elimination_prob <= 1.0):
            raise ValueError(
                f"Invalid elimination probability: {elimination_prob}. "
                f"Must be in range (0.0, 1.0]. Try elimination_prob=0.25."
            )
        if step_size_max <= step_size_min:
            raise ValueError(
                f"step_size_max ({step_size_max}) must be greater than step_size_min ({step_size_min}). "
                f"Typical values: step_size_min=1e-4, step_size_max=0.1."
            )
        if not (1.0 <= levy_alpha <= 2.0):
            raise ValueError(
                f"levy_alpha must be between 1.0 and 2.0, got {levy_alpha}. "
                f"Use 1.5 for balanced exploration (default) or 2.0 for Gaussian-like behavior."
            )
        if levy_schedule not in ["constant", "linear-decrease", "cosine"]:
            raise ValueError(
                f"levy_schedule must be 'constant', 'linear-decrease', or 'cosine', got '{levy_schedule}'. "
                f"Recommended: 'linear-decrease' for automatic exploration-exploitation balance."
            )
        if step_schedule not in ["adaptive", "cosine", "linear"]:
            raise ValueError(
                f"step_schedule must be 'adaptive', 'cosine', or 'linear', got '{step_schedule}'. "
                f"Recommended: 'adaptive' for automatic step size tuning."
            )
        if not (0.0 <= global_respawn_ratio <= 1.0):
            raise ValueError(
                f"global_respawn_ratio must be in [0.0, 1.0], got {global_respawn_ratio}. "
                f"0.0 = all local respawn, 1.0 = all global respawn. Recommended: 0.5 for multimodal problems."
            )

        # Default parameter group settings
        defaults = dict(
            lr=lr,
            population_size=population_size,
            chemotaxis_steps=chemotaxis_steps,
            swim_length=swim_length,
            reproduction_steps=reproduction_steps,
            elimination_steps=elimination_steps,
            elimination_prob=elimination_prob,
            step_size_min=step_size_min,
            step_size_max=step_size_max,
            levy_alpha=levy_alpha,
            levy_schedule=levy_schedule,
            step_schedule=step_schedule,
            enable_swarming=enable_swarming,
            swarming_params=swarming_params,
            normalize_directions=normalize_directions,
            global_respawn_ratio=global_respawn_ratio,
            adaptive_global_respawn=adaptive_global_respawn,
            **kwargs,
        )

        super().__init__(params, defaults)

        # BFO-specific state (separate from PyTorch's self.state)
        # Use parameter group index as key for stable serialization
        self.bfo_state = {}

        # Cache for Lévy flight constants (keyed by alpha, device, dtype)
        self._levy_cache = {}

        # Configuration & distributed metadata
        self.domain_bounds = domain_bounds
        self.early_stopping = early_stopping
        self.convergence_tolerance = convergence_tolerance
        self.convergence_patience = convergence_patience
        self._batch_eval_fn = batch_eval_fn
        self._batch_eval_failed = False
        self._seed = seed
        self._mesh_spec = mesh_spec
        self.checkpoint_strategy = checkpoint_strategy
        self._clone_on_write_default = bool(clone_on_write)
        self.debug_sharding = debug_sharding
        self._dist_debug = str(os.getenv("BFO_DIST_DEBUG", "0")).lower() in (
            "1",
            "true",
            "yes",
        )

        if history_window <= 0:
            raise ValueError(
                f"history_window must be a positive integer, got {history_window}."
            )
        self.history_window = int(history_window)

        self._distributed_context = self._safe_resolve_distributed_context()
        self.device = self._select_device(device)
        ctx = self._distributed_context
        if ctx:
            world_size = int(getattr(ctx, "world_size", 1) or 1)
            rank = int(getattr(ctx, "rank", 0) or 0)
            local_rank = int(getattr(ctx, "local_rank", rank) or rank)
        else:
            world_size = 1
            rank = 0
            local_rank = 0
        self.world_size = world_size
        self.rank = rank
        self.local_rank = local_rank
        self.devices_per_node = (
            torch.cuda.device_count() if torch.cuda.is_available() else None
        )
        self._device_mesh = self._maybe_create_device_mesh()
        self._dtensor_enabled = self._device_mesh is not None
        self._population_placements = (
            (Shard(0),) if self._dtensor_enabled and Shard is not None else None
        )
        self._replicate_placements = (
            (Replicate(),) if self._dtensor_enabled and Replicate is not None else None
        )

        self._compile_mode = (
            compile_mode if compile_mode and hasattr(torch, "compile") else None
        )
        if self._compile_mode and _torch_dynamo is not None:
            # Enable capture of scalar outputs and dynamic shape ops for torch.compile.
            _torch_dynamo.config.capture_scalar_outputs = True
            _torch_dynamo.config.capture_dynamic_output_shape_ops = True

        # Random seed
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)

        # Initialize optimizer state
        self._initialize_state()

        # Log initialization
        logger.info(
            f"BFO initialized: population_size={population_size}, device={self.device}, "
            f"levy_alpha={levy_alpha}, step_schedule={step_schedule}"
        )

        # Compile optimization if requested
        if self._compile_mode:
            try:
                self._compiled_step = torch.compile(
                    self._optimization_step, mode=self._compile_mode
                )
                logger.info(f"BFO compiled with mode: {self._compile_mode}")
            except Exception as exc:
                logger.warning(
                    "torch.compile failed at init (%s); falling back to eager", exc
                )
                self._compiled_step = self._optimization_step
        else:
            self._compiled_step = self._optimization_step

    def _safe_resolve_distributed_context(self) -> Optional[Any]:
        if resolve_distributed_context is None:
            return None
        try:
            return resolve_distributed_context()
        except Exception:  # pragma: no cover - defensive fallback
            logger.debug("resolve_distributed_context failed", exc_info=True)
            return None

    def _select_device(self, requested: Optional[torch.device]) -> torch.device:
        if requested is None:
            first_param = next(iter(self.param_groups[0]["params"]))
            requested = first_param.device
        ctx = self._distributed_context
        if (
            ctx is not None
            and getattr(ctx, "is_distributed", False)
            and requested is not None
            and requested.type == "cuda"
        ):
            local_rank = getattr(ctx, "local_rank", None)
            if local_rank is not None:
                try:
                    return torch.device("cuda", int(local_rank))
                except Exception:  # pragma: no cover - fall back to requested
                    pass
        return requested

    def _maybe_create_device_mesh(self) -> Optional["DeviceMesh"]:
        if DeviceMesh is None or Shard is None or Replicate is None:
            return None
        ctx = self._distributed_context
        if ctx is None or not getattr(ctx, "is_distributed", False):
            return None
        world_size = int(getattr(ctx, "world_size", 1) or 1)
        if world_size <= 1:
            return None

        spec = self._mesh_spec
        if spec is not None:
            if isinstance(spec, DeviceMesh):
                return spec
            devices = None
            if isinstance(spec, (list, tuple)):
                devices = [int(d) for d in spec]
            elif isinstance(spec, torch.Tensor):
                devices = [int(d.item()) for d in spec.view(-1)]
            elif isinstance(spec, str):
                tokens = [tok.strip() for tok in spec.split(",")]
                if tokens:
                    try:
                        devices = [int(tok) for tok in tokens if tok]
                    except ValueError:
                        logger.warning("Invalid mesh_spec string: %s", spec)
            if devices is not None:
                try:
                    return DeviceMesh("cuda", devices)
                except Exception:
                    logger.warning(
                        "Failed to construct DeviceMesh from mesh_spec=%s", spec
                    )

        try:
            mesh = DeviceMesh.create("cuda")
            if mesh is not None and mesh.ndim > 0:
                return mesh
        except Exception:
            pass

        try:
            devices = torch.arange(world_size, device="cpu", dtype=torch.int64).tolist()
            return DeviceMesh("cuda", devices)
        except Exception:
            logger.warning("Falling back to eager tensors; DeviceMesh unavailable.")
            return None

    def _compute_shard_meta(self, size: int) -> ShardMeta:
        ctx = self._distributed_context
        if ctx is None or not getattr(ctx, "is_distributed", False):
            return ShardMeta(
                global_start=0,
                global_end=size,
                global_count=size,
                global_size=size,
                world_size=1,
                rank=0,
                local_rank=0,
                devices_per_node=self.devices_per_node,
                placements=self._population_placements,
                mesh=self._device_mesh,
            )
        world_size = int(getattr(ctx, "world_size", 1) or 1)
        rank = int(getattr(ctx, "rank", 0) or 0)
        local_rank = int(getattr(ctx, "local_rank", rank) or rank)
        base = size // world_size
        remainder = size % world_size
        start = rank * base + min(rank, remainder)
        end = start + base + (1 if rank < remainder else 0)
        return ShardMeta(
            global_start=start,
            global_end=end,
            global_count=end - start,
            global_size=size,
            world_size=world_size,
            rank=rank,
            local_rank=local_rank,
            devices_per_node=self.devices_per_node,
            placements=self._population_placements,
            mesh=self._device_mesh,
        )

    def _wrap_population_tensor(
        self, tensor: torch.Tensor, meta: ShardMeta
    ) -> Tuple[torch.Tensor, Optional["DTensor"]]:
        if tensor is None:
            raise ValueError("Population tensor must be provided.")
        if not self._dtensor_enabled or DTensor is None or meta.mesh is None:
            return tensor, None
        try:
            dtensor = DTensor.from_local(
                tensor,
                meta.mesh,
                meta.placements or (Shard(0),),
                shape=torch.Size((meta.global_size,) + tensor.shape[1:]),
                stride=tensor.stride(),
            )
            return tensor, dtensor
        except Exception:
            logger.warning(
                "Failed to wrap population tensor in DTensor; using eager.",
                exc_info=True,
            )
        return tensor, None

    def _wrap_replicated_tensor(
        self, tensor: torch.Tensor, name: str
    ) -> Tuple[torch.Tensor, Optional["DTensor"]]:
        if not self._dtensor_enabled or DTensor is None:
            return tensor, None
        if self._device_mesh is None or self._replicate_placements is None:
            return tensor, None
        try:
            dtensor = DTensor.from_local(
                tensor,
                self._device_mesh,
                self._replicate_placements,
                shape=torch.Size(tensor.shape),
                stride=tensor.stride(),
            )
            if self.debug_sharding:
                logger.debug("Replicated tensor '%s' wrapped as DTensor", name)
            return tensor, dtensor
        except Exception:
            logger.debug(
                "Failed to wrap replicated tensor '%s' as DTensor; continuing eager.",
                name,
                exc_info=True,
            )
            return tensor, None

    def _wrap_local_like_dtensor(
        self, local_tensor: torch.Tensor, reference: "DTensor"
    ) -> "DTensor":
        """Recreate a DTensor from a local shard using reference metadata."""
        return DTensor.from_local(
            local_tensor,
            reference.device_mesh,
            reference.placements,
            shape=torch.Size(reference.size()),
            stride=local_tensor.stride(),
        )

    def _wrap_replicated_from_local(self, tensor: torch.Tensor) -> Optional["DTensor"]:
        """Wrap a local tensor as a replicated DTensor if possible."""
        if (
            not self._dtensor_enabled
            or DTensor is None
            or self._device_mesh is None
            or self._replicate_placements is None
        ):
            return None
        try:
            return DTensor.from_local(
                tensor,
                self._device_mesh,
                self._replicate_placements,
                shape=torch.Size(tensor.shape),
                stride=tensor.stride(),
            )
        except Exception:
            logger.debug("Failed to wrap tensor as replicated DTensor.", exc_info=True)
            return None

    def _dist_enabled(self) -> bool:
        return bool(dist is not None and self.world_size > 1)

    def _normalize_reduce_op(self, reduce_op: Any) -> Tuple[Optional[Any], str]:
        """Map user-friendly reduce ops to torch.distributed equivalents."""
        key = "sum"
        if isinstance(reduce_op, str):
            key = reduce_op.lower()
        elif dist is not None and isinstance(reduce_op, dist.ReduceOp):
            reverse = {
                dist.ReduceOp.SUM: "sum",
                dist.ReduceOp.PRODUCT: "prod",
                dist.ReduceOp.MAX: "max",
                dist.ReduceOp.MIN: "min",
                getattr(dist.ReduceOp, "AVG", dist.ReduceOp.SUM): "mean",
            }
            key = reverse.get(reduce_op, "sum")
        elif reduce_op is not None:
            key = str(reduce_op).lower()

        if dist is None:
            return None, key

        alias = {
            "sum": dist.ReduceOp.SUM,
            "add": dist.ReduceOp.SUM,
            "prod": dist.ReduceOp.PRODUCT,
            "product": dist.ReduceOp.PRODUCT,
            "max": dist.ReduceOp.MAX,
            "min": dist.ReduceOp.MIN,
            "mean": getattr(dist.ReduceOp, "AVG", dist.ReduceOp.SUM),
            "avg": getattr(dist.ReduceOp, "AVG", dist.ReduceOp.SUM),
        }
        return alias.get(key, dist.ReduceOp.SUM), key

    def _describe_tensor_for_log(
        self, tensor: Union[torch.Tensor, "DTensor"]
    ) -> str:
        try:
            if isinstance(tensor, DTensor):
                global_shape = tuple(int(dim) for dim in tensor.size())
                placements = getattr(tensor, "placements", None)
                mesh = getattr(tensor, "device_mesh", None)
                local = tensor.to_local()
                mesh_size = None
                if mesh is not None:
                    try:
                        mesh_size = mesh.size()
                    except Exception:  # pragma: no cover - defensive
                        mesh_size = None
                return (
                    f"DTensor(global_shape={global_shape}, "
                    f"local_shape={tuple(local.shape)}, "
                    f"dtype={tensor.dtype}, "
                    f"device={local.device}, "
                    f"placements={placements}, "
                    f"mesh_size={mesh_size})"
                )
            if isinstance(tensor, torch.Tensor):
                return (
                    f"Tensor(shape={tuple(tensor.shape)}, "
                    f"dtype={tensor.dtype}, device={tensor.device}, "
                    f"contiguous={tensor.is_contiguous()})"
                )
        except Exception as exc:  # pragma: no cover - defensive logging helper
            return f"{type(tensor).__name__}(describe_failed={exc})"
        return f"{type(tensor).__name__}"

    def _log_collective_event(
        self,
        name: str,
        stage: str,
        *,
        tag: str = "",
        tensor: Optional[Union[torch.Tensor, "DTensor"]] = None,
        extra: Optional[str] = None,
    ) -> None:
        if not self._dist_debug:
            return
        parts = [
            f"{name} {stage}",
            f"rank={self.rank}",
            f"world={self.world_size}",
        ]
        if tag:
            parts.append(f"tag={tag}")
        if tensor is not None:
            parts.append(self._describe_tensor_for_log(tensor))
        if extra:
            parts.append(extra)
        logger.warning(" | ".join(parts))

    def _gather_local_shards(
        self,
        local_tensor: torch.Tensor,
        expected_total: Optional[int] = None,
        tag: str = "",
    ) -> List[torch.Tensor]:
        """Gather local shards from all ranks as a list using padded all_gather."""
        if not self._dist_enabled():
            return [local_tensor]
        assert dist is not None  # for type-checkers

        device = local_tensor.device
        shard_dim = 0
        local_count = local_tensor.size(shard_dim)

        if self._dist_debug:
            logger.warning(
                "gather_local_shards start rank=%s world=%s tag=%s local_count=%s shape=%s dtype=%s expected_total=%s",
                self.rank,
                self.world_size,
                tag,
                local_count,
                tuple(local_tensor.shape),
                local_tensor.dtype,
                expected_total,
            )

        counts: Optional[List[int]] = None
        if expected_total is not None and self.world_size > 0:
            base = expected_total // self.world_size
            remainder = expected_total % self.world_size
            candidate = [
                base + (1 if rank < remainder else 0)
                for rank in range(self.world_size)
            ]
            if candidate[self.rank] == int(local_count):
                counts = candidate
            elif self._dist_debug:
                logger.warning(
                    "gather_local_shards deterministic counts mismatch "
                    "rank=%s local=%s candidate=%s expected_total=%s",
                    self.rank,
                    local_count,
                    candidate,
                    expected_total,
                )

        if counts is None:
            count_tensor = torch.tensor(
                [int(local_count)], device=device, dtype=torch.int64
            )
            gathered_counts_tensors = [
                torch.zeros_like(count_tensor) for _ in range(self.world_size)
            ]
            dist.all_gather(gathered_counts_tensors, count_tensor)
            counts = [int(t.item()) for t in gathered_counts_tensors]
        max_count = max(counts) if counts else 0
        counts_sum = sum(counts)

        if self._dist_debug:
            logger.warning(
                "gather_local_shards counts rank=%s tag=%s counts=%s sum=%s max=%s",
                self.rank,
                tag,
                counts,
                counts_sum,
                max_count,
            )

        if expected_total is not None and counts_sum != expected_total and self.rank == 0:
            logger.warning(
                "gather_local_shards mismatch tag=%s expected_total=%s got=%s counts=%s",
                tag,
                expected_total,
                counts_sum,
                counts,
            )

        if any(c < 0 for c in counts):
            raise RuntimeError(
                f"gather_local_shards received negative shard counts: {counts}"
            )

        if max_count == 0:
            return [torch.empty_like(local_tensor) for _ in counts]

        padded_shape = list(local_tensor.shape)
        padded_shape[shard_dim] = max_count
        padded = torch.zeros(padded_shape, device=device, dtype=local_tensor.dtype)
        if local_count > 0:
            padded.narrow(shard_dim, 0, local_count).copy_(local_tensor)

        gathered_buffer = torch.zeros(
            (self.world_size,) + tuple(padded.shape),
            device=device,
            dtype=local_tensor.dtype,
        )
        dist.all_gather_into_tensor(gathered_buffer, padded.unsqueeze(0))

        result: List[torch.Tensor] = []
        for idx, count in enumerate(counts):
            shard = gathered_buffer[idx]
            result.append(shard.narrow(shard_dim, 0, count).clone())

        if self._dist_debug:
            logger.warning(
                "gather_local_shards end rank=%s tag=%s reconstructed_shapes=%s",
                self.rank,
                tag,
                [tuple(t.shape) for t in result],
            )
        return result

    def _distributed_all_reduce(
        self,
        tensor: Union[torch.Tensor, "DTensor"],
        reduce_op: Any = "sum",
        tag: str = "",
    ) -> Union[torch.Tensor, "DTensor"]:
        """All-reduce helper that prefers DTensor ops when available."""
        if not self._dist_enabled():
            return tensor
        dist_op, reducer = self._normalize_reduce_op(reduce_op)
        if self._dist_debug:
            self._log_collective_event(
                "all_reduce",
                "start",
                tag=tag,
                tensor=tensor,
                extra=f"reduce_op={reducer}",
            )

        if isinstance(tensor, DTensor):
            if dt_ops is not None and hasattr(dt_ops, "all_reduce"):
                result = dt_ops.all_reduce(tensor, reduce_op=dist_op or reduce_op)
                if self._dist_debug:
                    self._log_collective_event(
                        "all_reduce",
                        "end",
                        tag=tag,
                        tensor=result,
                        extra=f"reduce_op={reducer} (dtensor)",
                    )
                return result
            local = tensor.to_local().clone()
            if dist is not None and dist_op is not None:
                dist.all_reduce(local, op=dist_op)
            elif dist is not None:
                dist.all_reduce(local)
            wrapped = self._wrap_local_like_dtensor(local, tensor)
            if self._dist_debug:
                self._log_collective_event(
                    "all_reduce",
                    "end",
                    tag=tag,
                    tensor=wrapped if wrapped is not None else local,
                    extra=f"reduce_op={reducer} (dtensor_fallback)",
                )
            return wrapped

        if not isinstance(tensor, torch.Tensor):
            raise TypeError("all_reduce expects a torch.Tensor or DTensor.")
        work = tensor if tensor.is_contiguous() else tensor.contiguous()
        if dist is not None and dist_op is not None:
            dist.all_reduce(work, op=dist_op)
        elif dist is not None:
            dist.all_reduce(work)
        if work is not tensor:
            tensor.copy_(work)
            result = tensor
        else:
            result = work
        if self._dist_debug:
            self._log_collective_event(
                "all_reduce",
                "end",
                tag=tag,
                tensor=result,
                extra=f"reduce_op={reducer}",
            )
        return result

    def _distributed_all_gather(
        self,
        tensor: Union[torch.Tensor, "DTensor"],
        dim: int = 0,
        tag: str = "",
    ) -> Union[torch.Tensor, "DTensor"]:
        """All-gather helper that tolerates uneven shards via object collectives."""
        gather_tag = tag or (
            "dtensor_all_gather" if isinstance(tensor, DTensor) else "tensor_all_gather"
        )

        if self._dist_debug:
            self._log_collective_event(
                "all_gather",
                "start",
                tag=gather_tag,
                tensor=tensor,
            )

        if isinstance(tensor, DTensor):
            if self._dist_enabled() and dt_ops is not None and hasattr(
                dt_ops, "all_gather"
            ):
                result = dt_ops.all_gather(tensor, dim=dim)
            else:
                local = tensor.to_local()
                expected = int(tensor.size(dim))
                shards = self._gather_local_shards(
                    local,
                    expected_total=expected,
                    tag=gather_tag,
                )
                gathered = torch.cat(shards, dim=dim)
                replicated = self._wrap_replicated_from_local(gathered)
                result = replicated if replicated is not None else gathered

            if self._dist_debug:
                result_is_dt = DTensor is not None and isinstance(result, DTensor)  # type: ignore[arg-type]
                self._log_collective_event(
                    "all_gather",
                    "end",
                    tag=gather_tag,
                    tensor=result,
                    extra="dtensor" if result_is_dt else None,
                )
            return result

        if not isinstance(tensor, torch.Tensor):
            raise TypeError("all_gather expects a torch.Tensor or DTensor.")
        shards = self._gather_local_shards(tensor, tag=gather_tag)
        result_tensor = torch.cat(shards, dim=dim)
        if self._dist_debug:
            self._log_collective_event(
                "all_gather",
                "end",
                tag=gather_tag,
                tensor=result_tensor,
            )
        return result_tensor

    def _distributed_reduce_scatter(
        self,
        tensor: Union[torch.Tensor, "DTensor"],
        shard_meta: Optional[ShardMeta],
        reduce_op: Any = "sum",
        tag: str = "",
        dim: int = 0,
    ) -> Union[torch.Tensor, "DTensor"]:
        """
        Reduce-scatter helper.

        When native DTensor ops are unavailable, this falls back to a gather +
        slice strategy, which assumes non-overlapping shards. For overlapping
        shards, a true reduce is required; callers should ensure inputs respect
        that contract.
        """
        if not self._dist_enabled():
            return tensor

        dist_op, reducer = self._normalize_reduce_op(reduce_op)
        if self._dist_debug:
            self._log_collective_event(
                "reduce_scatter",
                "start",
                tag=tag,
                tensor=tensor,
                extra=f"reduce_op={reducer}",
            )

        if isinstance(tensor, DTensor):
            if dt_ops is not None and hasattr(dt_ops, "reduce_scatter"):
                result = dt_ops.reduce_scatter(tensor, reduce_op=dist_op or reduce_op)
                if self._dist_debug:
                    self._log_collective_event(
                        "reduce_scatter",
                        "end",
                        tag=tag,
                        tensor=result,
                        extra=f"reduce_op={reducer} (dtensor)",
                    )
                return result
            local = tensor.to_local()
        elif isinstance(tensor, torch.Tensor):
            local = tensor
        else:
            raise TypeError("reduce_scatter expects a torch.Tensor or DTensor.")

        if shard_meta is None:
            raise ValueError(
                "ShardMeta is required when reduce_scatter falls back to gather."
            )

        expected = (
            shard_meta.global_size if shard_meta is not None else None
        )
        shards = self._gather_local_shards(
            local, expected_total=expected, tag="reduce_scatter"
        )
        if reducer not in ("sum", "add"):
            # TODO: implement true reduction for max/min/prod in fallback path.
            logger.debug(
                "Fallback reduce_scatter currently treats reducer '%s' as concat.",
                reducer,
            )
        gathered = torch.cat(shards, dim=dim)
        local_result = gathered[shard_meta.slice].clone()

        if isinstance(tensor, DTensor):
            wrapped = self._wrap_local_like_dtensor(local_result, tensor)
            if self._dist_debug:
                self._log_collective_event(
                    "reduce_scatter",
                    "end",
                    tag=tag,
                    tensor=wrapped if wrapped is not None else local_result,
                    extra=f"reduce_op={reducer} (fallback_dtensor)",
                )
            return wrapped
        if self._dist_debug:
            self._log_collective_event(
                "reduce_scatter",
                "end",
                tag=tag,
                tensor=local_result,
                extra=f"reduce_op={reducer} (fallback_tensor)",
            )
        return local_result

    def _gather_population_full(
        self,
        population: Union[torch.Tensor, "DTensor"],
        shard_meta: ShardMeta,
        tag: str = "population",
    ) -> Tuple[torch.Tensor, Optional["DTensor"]]:
        gather_tag = tag or "population"
        if isinstance(population, DTensor):
            gathered = self._distributed_all_gather(
                population,
                dim=0,
                tag=f"{gather_tag}_dt",
            )
            if isinstance(gathered, DTensor):
                gathered_local = gathered.to_local()
            else:
                gathered_local = gathered
            return gathered_local.clone(), population
        if isinstance(population, torch.Tensor):
            if self._dist_debug and shard_meta.world_size > 1:
                self._log_collective_event(
                    "all_gather",
                    "skip",
                    tag=f"{gather_tag}_tensor_local",
                    tensor=population,
                    extra="already_full",
                )
            return population.clone(), None
        raise TypeError("Unsupported population tensor type.")

    def _scatter_population_from_full(
        self,
        population_full: torch.Tensor,
        population_spec: Optional["DTensor"],
        shard_meta: ShardMeta,
    ) -> Union[torch.Tensor, "DTensor"]:
        if population_spec is not None:
            local_updated = population_full[shard_meta.slice].clone()
            return self._wrap_local_like_dtensor(local_updated, population_spec)
        return population_full

    def _ensure_population_meta(
        self,
        group_state: BFOGroupState,
        population: Union[torch.Tensor, "DTensor"],
        shard_meta: ShardMeta,
    ) -> None:
        if isinstance(population, DTensor):
            group_state.population_dtensor = population
            group_state.population_local = population.to_local()
            group_state.population = population
            group_state.population_shape = torch.Size(population.size())
            group_state.population_shard = shard_meta
        else:
            group_state.population_dtensor = None
            group_state.population_local = population
            group_state.population = population
            group_state.population_shape = population.shape
            group_state.population_shard = shard_meta if shard_meta.world_size > 1 else None

    def _resolve_population_shard_meta(
        self,
        group_state: BFOGroupState,
        population: Union[torch.Tensor, "DTensor"],
    ) -> ShardMeta:
        pop_size = (
            int(population.size(0))
            if isinstance(population, DTensor)
            else int(population.shape[0])
        )
        shard_meta = group_state.population_shard
        if (
            shard_meta is not None
            and shard_meta.global_size == pop_size
            and shard_meta.world_size == self.world_size
        ):
            return shard_meta
        return self._compute_shard_meta(pop_size)

    def _population_full_view(
        self, group_state: BFOGroupState
    ) -> Tuple[torch.Tensor, Optional["DTensor"], ShardMeta]:
        population = group_state.population
        shard_meta = self._resolve_population_shard_meta(group_state, population)
        population_full, population_spec = self._gather_population_full(
            population,
            shard_meta,
            tag=f"population_view.group{group_state.group_id}",
        )
        return population_full, population_spec, shard_meta

    def _update_population_from_full(
        self, group_state: BFOGroupState, population_full: torch.Tensor
    ) -> None:
        new_size = int(population_full.shape[0])
        shard_meta = self._compute_shard_meta(new_size)

        materialized_full = (
            population_full.clone() if group_state.clone_on_write else population_full
        )

        local_slice = materialized_full[shard_meta.slice]
        if group_state.clone_on_write:
            local_slice = local_slice.clone()

        population_local, population_dtensor = self._wrap_population_tensor(
            local_slice, shard_meta
        )

        if population_dtensor is not None:
            population_view: Union[torch.Tensor, "DTensor"] = population_dtensor
        else:
            population_view = materialized_full

        group_state.population = population_view
        group_state.population_local = population_local
        group_state.population_dtensor = population_dtensor
        group_state.population_shard = (
            shard_meta if shard_meta.world_size > 1 else None
        )
        group_state.population_shape = torch.Size(materialized_full.shape)

    def _initialize_state(self) -> None:
        """Initialize optimizer state for all parameter groups."""
        for group in self.param_groups:
            self._initialize_group_state(group)

    def _get_group_id(self, group: Dict[str, Any]) -> int:
        """Get stable group ID based on index in param_groups."""
        for i, g in enumerate(self.param_groups):
            if g is group:
                return i
        raise ValueError("Group not found in param_groups")

    def _initialize_group_state(self, group: Dict[str, Any]) -> None:
        """Initialize state for a specific parameter group."""
        # Flatten parameters for this group
        param_vector, param_shapes = self._flatten_group_params(group)
        population_size = group["population_size"]

        # Detect dtype from parameters
        first_param = group["params"][0]
        dtype = first_param.dtype

        shard_meta = self._compute_shard_meta(population_size)
        local_count = shard_meta.global_count
        population_shape = torch.Size((population_size, param_vector.numel()))

        population_local = torch.empty(
            (local_count, param_vector.numel()),
            device=self.device,
            dtype=dtype,
        )
        if local_count > 0:
            population_local.copy_(
                param_vector.unsqueeze(0)
                + torch.randn_like(population_local) * group["step_size_max"]
            )
        if shard_meta.global_start <= 0 < shard_meta.global_end:
            local_idx = 0 - shard_meta.global_start
            population_local[local_idx] = param_vector.clone()
        if self.domain_bounds is not None and population_local.numel() > 0:
            population_local.clamp_(self.domain_bounds[0], self.domain_bounds[1])

        # Store state
        if self.domain_bounds is not None:
            param_vector = param_vector.clamp(
                self.domain_bounds[0], self.domain_bounds[1]
            )

        population_local, population_dtensor = self._wrap_population_tensor(
            population_local, shard_meta
        )

        fitness_dtype = torch.float32 if dtype in (torch.float16, torch.bfloat16) else dtype
        history_buffer = self._init_history_buffer(fitness_dtype)
        replicated_tensors: Dict[str, "DTensor"] = {}

        def register_replicated(name: str, tensor: torch.Tensor) -> torch.Tensor:
            local, dtensor = self._wrap_replicated_tensor(tensor, name)
            if dtensor is not None:
                replicated_tensors[name] = dtensor
            return local

        group_id = self._get_group_id(group)
        best_params = register_replicated("best_params", param_vector.clone())
        best_fitness = register_replicated(
            "best_fitness",
            torch.full((), float("inf"), device=self.device, dtype=fitness_dtype),
        )
        prev_best_fitness = register_replicated(
            "prev_best_fitness",
            torch.full((), float("inf"), device=self.device, dtype=fitness_dtype),
        )
        current_step_size = register_replicated(
            "current_step_size",
            torch.tensor(group["step_size_max"], device=self.device, dtype=dtype),
        )
        stagnation_count = register_replicated(
            "stagnation_count",
            torch.zeros((), device=self.device, dtype=torch.int64),
        )
        iteration = register_replicated(
            "iteration",
            torch.zeros((), device=self.device, dtype=torch.int64),
        )
        history_buffer = register_replicated("fitness_history_buffer", history_buffer)
        history_length = register_replicated(
            "fitness_history_length",
            torch.zeros((), device=self.device, dtype=torch.int64),
        )
        function_evals = register_replicated(
            "function_evaluations",
            torch.zeros((), device=self.device, dtype=torch.int64),
        )

        population_view = (
            population_dtensor if population_dtensor is not None else population_local
        )

        group_state = BFOGroupState(
            param_vector=param_vector,
            param_shapes=param_shapes,
            population=population_view,
            best_params=best_params,
            best_fitness=best_fitness,
            prev_best_fitness=prev_best_fitness,
            current_step_size=current_step_size,
            stagnation_count=stagnation_count,
            iteration=iteration,
            dtype=dtype,
            fitness_history_buffer=history_buffer,
            fitness_history_length=history_length,
            function_evaluations=function_evals,
            population_dtensor=population_dtensor,
            population_local=population_local,
            population_shard=shard_meta,
            population_shape=population_shape,
            clone_on_write=self._clone_on_write_default,
            distributed_context=self._distributed_context,
            replicated_tensors=replicated_tensors,
            group_id=group_id,
        )
        group_state.batch_eval_rng = self._make_generator(group_id)
        self.bfo_state[group_id] = group_state

    def _init_history_buffer(self, dtype: torch.dtype) -> torch.Tensor:
        """Create an on-device rolling buffer for best-fitness history."""
        return torch.full(
            (self.history_window,),
            float("inf"),
            device=self.device,
            dtype=dtype,
        )

    def _history_push(self, group_state: BFOGroupState, value: torch.Tensor) -> None:
        """Append a new scalar to the rolling history buffer."""
        history = group_state.fitness_history_buffer
        if group_state.clone_on_write:
            rolled = torch.roll(history, shifts=-1, dims=0)
            new_history = rolled.clone()
            new_history[-1] = value
            group_state.fitness_history_buffer = new_history
        else:
            history.copy_(torch.roll(history, shifts=-1, dims=0))
            history[-1] = value
        max_window = torch.tensor(
            self.history_window,
            device=self.device,
            dtype=group_state.fitness_history_length.dtype,
        )
        new_length = torch.minimum(
            group_state.fitness_history_length + 1, max_window
        )
        group_state.fitness_history_length = (
            new_length.clone() if group_state.clone_on_write else new_length
        )

    def _history_has(self, group_state: BFOGroupState, count: int) -> bool:
        """Return True if the rolling history has at least `count` valid entries."""
        length = int(group_state.fitness_history_length.item())
        return length >= count

    def _history_get(self, group_state: BFOGroupState, lag: int) -> torch.Tensor:
        """Fetch the value `lag` steps from the end of the history buffer."""
        return group_state.fitness_history_buffer[-lag]

    def _make_generator(self, group_id: Optional[int]) -> torch.Generator:
        """Create a torch.Generator seeded deterministically when possible."""
        ctx = getattr(self, "_distributed_context", None)
        rank = getattr(ctx, "rank", 0) if ctx is not None else 0
        world_size = getattr(ctx, "world_size", 1) if ctx is not None else 1
        batch_id = int(group_id or 0)

        if (
            self._seed is not None
            and make_generator_for_rank is not None
            and world_size is not None
            and world_size > 0
        ):
            try:
                return make_generator_for_rank(
                    int(self._seed),
                    rank=rank,
                    world_size=int(world_size),
                    batch_id=batch_id,
                    device=self.device,
                )
            except Exception:  # pragma: no cover - defensive fallback
                pass

        gen = torch.Generator(device=self.device)
        if self._seed is not None:
            gen.manual_seed(int(self._seed) + batch_id)
        else:
            gen.seed()
        return gen

    def _step_scale(
        self, group_state: BFOGroupState, population: torch.Tensor
    ) -> torch.Tensor:
        """
        Retrieve the current step multiplier for each bacterium.

        Returns either a scalar (shared step) or a broadcast-ready per-bacterium
        tensor with shape compatible with `population`.
        """
        base = group_state.current_step_size
        per_bacterium = getattr(group_state, "per_bacterium_step_size", None)
        if per_bacterium is None:
            return base
        view_shape = (per_bacterium.shape[0],) + (1,) * (population.dim() - 1)
        return per_bacterium.view(view_shape)

    def _flatten_group_params(
        self, group: Dict[str, Any]
    ) -> Tuple[torch.Tensor, List[torch.Size]]:
        """Flatten all parameters in a group into a single tensor."""
        param_list = []
        param_shapes = []

        for p in group["params"]:
            param_list.append(p.data.view(-1))
            param_shapes.append(p.shape)

        param_vector = torch.cat(param_list).to(self.device)
        return param_vector, param_shapes

    def _unflatten_group_params(
        self, vector: torch.Tensor, shapes: List[torch.Size]
    ) -> List[torch.Tensor]:
        """Unflatten parameter vector back to original shapes."""
        params = []
        offset = 0

        for shape in shapes:
            numel = torch.prod(torch.tensor(shape)).item()
            params.append(vector[offset : offset + numel].view(shape))
            offset += numel

        return params

    def _apply_domain_bounds(self, tensor: torch.Tensor) -> torch.Tensor:
        """Clamp tensor in-place to domain bounds if provided."""
        if self.domain_bounds is not None:
            tensor.clamp_(self.domain_bounds[0], self.domain_bounds[1])
        return tensor

    def _levy_flight(
        self,
        size: Tuple[int, ...],
        alpha: float,
        device: torch.device,
        dtype: torch.dtype,
    ) -> torch.Tensor:
        """Generate Lévy flight steps for exploration."""
        # Check cache for pre-computed constants
        cache_key = (alpha, device, dtype)
        if cache_key not in self._levy_cache:
            # Compute Lévy distribution parameters (only once per alpha/device/dtype combo)
            gamma_1_alpha = torch.exp(
                torch.lgamma(torch.tensor(1 + alpha, device=device, dtype=dtype))
            )
            gamma_1_alpha_2 = torch.exp(
                torch.lgamma(torch.tensor((1 + alpha) / 2, device=device, dtype=dtype))
            )
            sin_term = torch.sin(
                torch.tensor(np.pi * alpha / 2, device=device, dtype=dtype)
            )

            sigma_u = (
                gamma_1_alpha
                * sin_term
                / (
                    gamma_1_alpha_2
                    * alpha
                    * torch.pow(
                        torch.tensor(2.0, device=device, dtype=dtype), (alpha - 1) / 2
                    )
                )
            ).pow(1 / alpha)

            self._levy_cache[cache_key] = sigma_u
        else:
            sigma_u = self._levy_cache[cache_key]

        # Generate random samples with numerical stability
        u = torch.randn(size, device=device, dtype=dtype) * sigma_u
        v = torch.randn(size, device=device, dtype=dtype)
        v_abs = torch.abs(v) + 1e-10
        step = u / v_abs.pow(1 / alpha)
        step = torch.nan_to_num(step, nan=0.0, posinf=0.0, neginf=0.0)
        step = 10 * torch.tanh(step / 10)
        return step

    def _compute_swarming(
        self,
        positions: torch.Tensor,
        swarming_params: Tuple[float, float, float, float],
    ) -> torch.Tensor:
        """Compute bacterial swarming forces."""
        d_attract, w_attract, h_repel, w_repel = swarming_params
        pop_size = positions.shape[0]

        if pop_size == 1:
            return torch.zeros(
                1, positions.shape[1], device=positions.device, dtype=positions.dtype
            )

        # Handle mixed precision for torch.cdist compatibility
        original_dtype = positions.dtype
        needs_conversion = original_dtype in (torch.float16, torch.bfloat16)
        positions_compute = positions.float() if needs_conversion else positions

        # Compute pairwise distances (with small epsilon for numerical stability)
        distances = torch.cdist(positions_compute, positions_compute, p=2)
        distances = distances + 1e-10

        # Compute direction vectors (reuse diff for normalized_diff to save memory)
        diff = positions_compute.unsqueeze(0) - positions_compute.unsqueeze(1)
        diff = diff / distances.unsqueeze(-1)  # Now diff is normalized_diff

        # Compute attraction and repulsion forces (Passino 2002)
        # Both use squared distances for proper force profiles
        dist_sq = distances * distances  # Reuse for both
        attract_factor = -d_attract * torch.exp(-w_attract * dist_sq)
        repel_factor = h_repel * torch.exp(-w_repel * dist_sq)

        # Combine factors and exclude self-interactions in one step
        mask = ~torch.eye(pop_size, dtype=torch.bool, device=positions_compute.device)
        combined_factor = (attract_factor + repel_factor) * mask.float()

        # Compute swarming forces (in-place operations where possible)
        swarming = (combined_factor.unsqueeze(-1) * diff).sum(dim=1)

        # Convert back to original dtype
        if original_dtype != swarming.dtype:
            swarming = swarming.to(original_dtype)

        return swarming

    def _get_levy_scale(
        self, group: Dict[str, Any], group_state: BFOGroupState
    ) -> torch.Tensor:
        """
        Compute Lévy flight scale factor based on schedule (Chen et al. 2020).

        Linear-decreasing schedule balances exploration (early) and exploitation (late):
        C'(t) = C_min + ((iter_max - iter) / iter_max) × (C_max - C_min)
        """
        schedule = group["levy_schedule"]
        dtype = group_state.current_step_size.dtype
        base = torch.tensor(1.0, device=self.device, dtype=dtype)

        if schedule == "constant":
            return base

        iteration = group_state.iteration.to(dtype)
        max_iterations = (
            group["elimination_steps"]
            * group["reproduction_steps"]
            * group["chemotaxis_steps"]
        )
        max_tensor = torch.tensor(max(max_iterations, 1), device=self.device, dtype=dtype)
        progress = torch.clamp(iteration / max_tensor, 0.0, 1.0)

        if schedule == "linear-decrease":
            return base - 0.7 * progress
        if schedule == "cosine":
            return torch.tensor(0.3, device=self.device, dtype=dtype) + 0.7 * (
                1 + torch.cos(progress * math.pi)
            ) / 2

        return base

    def _update_step_size(
        self,
        group: Dict[str, Any],
        group_state: BFOGroupState,
        recent_improvement: torch.Tensor,
    ) -> None:
        """
        Update adaptive step size based on schedule and performance.

        Combines scheduled decay with performance-based adaptation for
        robust convergence across different problem types.
        """
        schedule = group["step_schedule"]
        current = group_state.current_step_size
        dtype = current.dtype
        step_min = torch.tensor(
            group["step_size_min"], device=self.device, dtype=dtype
        )
        step_max = torch.tensor(
            group["step_size_max"], device=self.device, dtype=dtype
        )

        if schedule == "adaptive":
            tolerance = torch.tensor(
                self.convergence_tolerance,
                device=self.device,
                dtype=recent_improvement.dtype,
            )
            shrink_mask = recent_improvement < tolerance
            grow_factor = torch.tensor(1.05, device=self.device, dtype=dtype)
            shrink_factor = torch.tensor(0.95, device=self.device, dtype=dtype)
            current = torch.where(
                shrink_mask, current * shrink_factor, current * grow_factor
            )

        elif schedule == "linear":
            iteration = group_state.iteration.to(dtype)
            max_iterations = (
                group["elimination_steps"]
                * group["reproduction_steps"]
                * group["chemotaxis_steps"]
            )
            max_tensor = torch.tensor(
                max(max_iterations, 1), device=self.device, dtype=dtype
            )
            progress = torch.clamp(iteration / max_tensor, 0.0, 1.0)
            current = step_max - (step_max - step_min) * progress

        elif schedule == "cosine":
            iteration = group_state.iteration.to(dtype)
            max_iterations = (
                group["elimination_steps"]
                * group["reproduction_steps"]
                * group["chemotaxis_steps"]
            )
            max_tensor = torch.tensor(
                max(max_iterations, 1), device=self.device, dtype=dtype
            )
            progress = torch.clamp(iteration / max_tensor, 0.0, 1.0)
            current = step_min + (step_max - step_min) * (
                1 + torch.cos(progress * math.pi)
            ) / 2

        current = torch.minimum(step_max, torch.maximum(step_min, current))
        group_state.current_step_size = current

    def _evaluate_closure(
        self, closure: Callable, group: Dict[str, Any], individual: torch.Tensor
    ) -> float:
        """Safely evaluate closure for a given parameter configuration."""
        # Store references to original data tensors (no clone needed)
        params = group["params"]
        original_data = [p.data for p in params]

        try:
            # Unflatten individual into parameter shapes
            group_id = self._get_group_id(group)
            param_list = self._unflatten_group_params(
                individual, self.bfo_state[group_id]["param_shapes"]
            )

            # Swap in new parameters (in-place, no copy)
            with torch.no_grad():
                for p, new_p in zip(params, param_list):
                    p.data = new_p

            # Evaluate closure
            result = closure()

            # Convert result to float
            if isinstance(result, torch.Tensor):
                result = result.item()

            return float(result)

        except Exception as e:
            logger.debug(f"Closure evaluation failed: {e}")
            return float("inf")

        finally:
            # Restore original parameters (just reassign references)
            with torch.no_grad():
                for p, orig_data in zip(params, original_data):
                    p.data = orig_data

    def _evaluate_batch_closure(
        self, closure: Callable, group: Dict[str, Any], population: torch.Tensor
    ) -> torch.Tensor:
        """Evaluate closure for multiple parameter configurations in batch."""
        group_id = self._get_group_id(group)
        group_state = self.bfo_state.get(group_id)
        population_is_dtensor = isinstance(population, DTensor)

        pop_size = (
            int(population.size(0)) if population_is_dtensor else population.shape[0]
        )

        if group_state is not None:
            best_fitness_tensor = getattr(group_state, "best_fitness", None)
            fitness_dtype = (
                best_fitness_tensor.dtype
                if isinstance(best_fitness_tensor, torch.Tensor)
                else torch.float32
            )
            shard_meta = getattr(group_state, "population_shard", None)
        else:
            fitness_dtype = torch.float32
            shard_meta = None

        if shard_meta is None:
            shard_meta = self._compute_shard_meta(pop_size)

        if population_is_dtensor:
            local_population = population.to_local()
        else:
            if shard_meta.global_count == pop_size:
                local_population = population
            else:
                local_population = population[shard_meta.slice]

        local_count = local_population.shape[0]

        max_fe = getattr(self, "_max_fe", None)
        fe_tensor: Optional[torch.Tensor] = None
        fe_dtype = torch.int64
        if group_state is not None:
            fe_state = getattr(group_state, "function_evaluations", None)
            if isinstance(fe_state, torch.Tensor):
                fe_tensor = fe_state.to(device=self.device)
                fe_dtype = fe_tensor.dtype
            elif fe_state is not None:
                fe_tensor = torch.tensor(
                    int(fe_state), device=self.device, dtype=fe_dtype
                )

        pop_limit = torch.tensor(pop_size, device=self.device, dtype=fe_dtype)
        if max_fe is not None and fe_tensor is not None:
            remaining = torch.clamp(
                torch.tensor(max_fe, device=self.device, dtype=fe_dtype) - fe_tensor,
                min=0,
            )
            to_eval_tensor = torch.minimum(pop_limit, remaining)
        else:
            to_eval_tensor = pop_limit

        global_eval_limit = int(to_eval_tensor.item())

        local_indices = (
            torch.arange(local_count, device=self.device, dtype=torch.long)
            if local_count > 0
            else torch.empty(0, device=self.device, dtype=torch.long)
        )
        global_indices = local_indices + shard_meta.global_start
        local_eval_mask = global_indices < global_eval_limit
        local_eval_positions = torch.nonzero(local_eval_mask, as_tuple=False).view(-1)
        local_eval_count = int(local_eval_positions.numel())
        has_eval = local_eval_count > 0

        if _torch_dynamo is not None and has_eval:
            _torch_dynamo.graph_break()

        if population_is_dtensor:
            fitness_local = torch.full(
                (local_count,), float("inf"), device=self.device, dtype=fitness_dtype
            )
        else:
            fitness = torch.full(
                (pop_size,), float("inf"), device=self.device, dtype=fitness_dtype
            )

        # Batched closure evaluation
        if has_eval and self._batch_eval_fn is not None and not self._batch_eval_failed:
            try:
                batch_population = local_population.index_select(0, local_eval_positions)
                rng = None
                shard_info = None
                if group_state is not None:
                    rng = getattr(group_state, "batch_eval_rng", None)
                    if rng is None:
                        rng = self._make_generator(group_id)
                        group_state.batch_eval_rng = rng
                    dist_ctx = getattr(group_state, "distributed_context", None)
                    if dist_ctx is None and resolve_distributed_context is not None:
                        dist_ctx = resolve_distributed_context()
                        group_state.distributed_context = dist_ctx
                    shard_info = {
                        "group": group_id,
                        "count": int(batch_population.shape[0]),
                        "population_size": pop_size,
                        "start": shard_meta.global_start,
                        "end": shard_meta.global_end,
                    }
                    if dist_ctx is not None:
                        shard_info.update(
                            {
                                "rank": getattr(dist_ctx, "rank", 0),
                                "local_rank": getattr(dist_ctx, "local_rank", 0),
                                "world_size": getattr(dist_ctx, "world_size", 1),
                                "is_distributed": getattr(
                                    dist_ctx, "is_distributed", False
                                ),
                            }
                        )
                try:
                    batch_fitness = self._batch_eval_fn(
                        batch_population, rng=rng, shard=shard_info
                    )
                except TypeError:
                    batch_fitness = self._batch_eval_fn(batch_population)

                if not isinstance(batch_fitness, torch.Tensor):
                    batch_fitness = torch.as_tensor(
                        batch_fitness, device=self.device, dtype=fitness_dtype
                    )
                else:
                    batch_fitness = batch_fitness.to(self.device, dtype=fitness_dtype)

                batch_fitness = batch_fitness.view(-1)
                if batch_fitness.numel() != batch_population.size(0):
                    raise ValueError(
                        f"batch_eval_fn returned {batch_fitness.numel()} values for "
                        f"{batch_population.size(0)} inputs."
                    )

                if population_is_dtensor:
                    fitness_local.index_copy_(0, local_eval_positions, batch_fitness)
                else:
                    target_indices = global_indices.index_select(0, local_eval_positions)
                    fitness.index_copy_(0, target_indices.to(torch.long), batch_fitness)
            except Exception as exc:
                if not self._batch_eval_failed:
                    logger.debug(
                        "Batch evaluation failed (%s); falling back to sequential evaluation.",
                        exc,
                    )
                self._batch_eval_failed = True
                local_eval_positions = torch.nonzero(local_eval_mask, as_tuple=False).view(-1)
                local_eval_count = int(local_eval_positions.numel())

        # Sequential fallback
        if has_eval and (
            self._batch_eval_failed or self._batch_eval_fn is None
        ):
            for local_idx in local_eval_positions.tolist():
                value = self._evaluate_closure(
                    closure, group, local_population[local_idx]
                )
                if population_is_dtensor:
                    fitness_local[local_idx] = torch.tensor(
                        value, device=self.device, dtype=fitness_dtype
                    )
                else:
                    global_idx = int(global_indices[local_idx].item())
                    fitness[global_idx] = torch.tensor(
                        value, device=self.device, dtype=fitness_dtype
                    )

        # Function evaluation accounting
        local_increment = torch.tensor(
            local_eval_count, device=self.device, dtype=fe_dtype
        )
        if self._dist_debug:
            logger.warning(
                "fe_increment local | rank=%s | world=%s | local_count=%s | has_eval=%s",
                self.rank,
                self.world_size,
                local_eval_count,
                has_eval,
            )
        global_increment = self._distributed_all_reduce(
            local_increment, "sum", tag="fe_increment"
        )
        if self._dist_debug:
            try:
                global_value = int(global_increment.item())
            except Exception:
                global_value = global_increment
            logger.warning(
                "fe_increment global | rank=%s | world=%s | total=%s",
                self.rank,
                self.world_size,
                global_value,
            )

        if group_state is not None:
            increment_cast = global_increment.to(
                group_state.function_evaluations.dtype
            )
            updated_fe = group_state.function_evaluations + increment_cast
            group_state.function_evaluations = (
                updated_fe.clone()
                if group_state.clone_on_write
                else updated_fe
            )

        if population_is_dtensor:
            gather_tag = f"fitness_dtensor.group{group_id}"
            gathered = self._distributed_all_gather(
                fitness_local,
                dim=0,
                tag=gather_tag,
            )
            if isinstance(gathered, DTensor):
                return gathered.to_local()
            return gathered

        return fitness

    def _perform_chemotaxis_phase(
        self,
        closure: Callable,
        group: Dict[str, Any],
        group_state: BFOGroupState,
        population: torch.Tensor,
        fe_budget: Optional[torch.Tensor],
        estimated_fe_tensor: Optional[torch.Tensor],
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], bool]:
        """
        Execute the chemotaxis/swim stage and update population and fitness.

        Returns the updated population, the latest fitness tensor (if available),
        and a boolean flag indicating whether the function-evaluation budget was
        exhausted.
        """
        group_id = self._get_group_id(group)
        shard_meta = (
            group_state.population_shard
            if group_state.population_shard is not None
            else self._compute_shard_meta(
                population.shape[0]
                if not isinstance(population, DTensor)
                else int(population.size(0))
            )
        )
        population_full, population_spec = self._gather_population_full(
            population,
            shard_meta,
            tag=f"chemotaxis.group{group_id}",
        )

        def _as_eval_tensor(full_tensor: torch.Tensor) -> Union[torch.Tensor, "DTensor"]:
            if population_spec is None:
                return full_tensor
            return self._wrap_local_like_dtensor(
                full_tensor[shard_meta.slice].clone(), population_spec
            )

        fitness: Optional[torch.Tensor] = None
        dtype = group_state.dtype

        for _ in range(group["chemotaxis_steps"]):
            if (
                fe_budget is not None
                and estimated_fe_tensor is not None
                and bool(
                    (
                        group_state.function_evaluations + estimated_fe_tensor
                        > fe_budget
                    ).item()
                )
            ):
                if logger.isEnabledFor(logging.INFO):
                    logger.info(
                        "Stopping optimization: FE budget exceeded (%s + %s > %s)",
                        group_state.function_evaluations,
                        estimated_fe_tensor,
                        fe_budget,
                    )
                return population, fitness, True

            with record_function("bfo/evaluate_population"):
                population_eval = _as_eval_tensor(population_full)
                fitness = self._evaluate_batch_closure(closure, group, population_eval)

            best_fitness, best_idx = torch.min(fitness, dim=0)
            improvement = best_fitness < group_state.best_fitness

            group_state.best_fitness = torch.minimum(
                group_state.best_fitness, best_fitness
            )
            best_params_candidate = torch.index_select(
                population_full, 0, best_idx.unsqueeze(0)
            ).squeeze(0)
            group_state.best_params = torch.where(
                improvement.unsqueeze(0).expand_as(best_params_candidate),
                best_params_candidate,
                group_state.best_params,
            )
            group_state.stagnation_count = torch.where(
                improvement,
                torch.zeros_like(group_state.stagnation_count),
                group_state.stagnation_count + 1,
            )

            prev_best = group_state.prev_best_fitness
            recent_improvement = torch.where(
                torch.isfinite(prev_best),
                torch.abs(prev_best - best_fitness),
                torch.zeros_like(best_fitness),
            )
            group_state.prev_best_fitness = best_fitness

            self._update_step_size(group, group_state, recent_improvement)

            levy_steps = self._levy_flight(
                population_full.shape,
                group["levy_alpha"],
                self.device,
                dtype,
            )

            if group["normalize_directions"]:
                norms = torch.norm(levy_steps, dim=1, keepdim=True)
                levy_directions = levy_steps / (norms + self._EPS)
            else:
                levy_directions = levy_steps

            levy_scale = self._get_levy_scale(group, group_state)
            step_factor = self._step_scale(group_state, population_full) * levy_scale
            movement = levy_directions * step_factor

            with record_function("bfo/chemotaxis_move"):
                candidate_positions = population_full + movement
                self._apply_domain_bounds(candidate_positions)
                candidate_fitness = self._evaluate_batch_closure(
                    closure, group, candidate_positions
                )

            improved = candidate_fitness < fitness
            population_full = torch.where(
                improved.unsqueeze(1), candidate_positions, population_full
            )
            fitness = torch.where(improved, candidate_fitness, fitness)

            active_mask = improved
            movement_step = movement
            with record_function("bfo/swim"):
                for _ in range(group["swim_length"]):
                    candidate_positions = population_full + movement_step
                    self._apply_domain_bounds(candidate_positions)
                    swim_population = torch.where(
                        active_mask.unsqueeze(1), candidate_positions, population_full
                    )
                    swim_eval = _as_eval_tensor(swim_population)
                    swim_fitness = self._evaluate_batch_closure(closure, group, swim_eval)
                    swim_improved = swim_fitness < fitness
                    population_full = torch.where(
                        swim_improved.unsqueeze(1),
                        swim_population,
                        population_full,
                    )
                    fitness = torch.where(swim_improved, swim_fitness, fitness)
                    active_mask = swim_improved

        population_out = self._scatter_population_from_full(
            population_full, population_spec, shard_meta
        )
        return population_out, fitness, False

    def _apply_reproduction_phase(
        self,
        group_state: BFOGroupState,
        population: torch.Tensor,
        fitness: Optional[torch.Tensor],
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Replicate the best half of the population to replace the worst half."""
        if fitness is None:
            return population, fitness

        shard_meta = (
            group_state.population_shard
            if group_state.population_shard is not None
            else self._compute_shard_meta(
                population.shape[0]
                if not isinstance(population, DTensor)
                else int(population.size(0))
            )
        )
        population_full, population_spec = self._gather_population_full(
            population,
            shard_meta,
            tag=f"reproduction.group{group_state.group_id}",
        )

        if population_full.shape[0] <= 1:
            return population, fitness

        with record_function("bfo/reproduction"):
            pop_size = int(population_full.shape[0])
            sorted_indices = torch.argsort(fitness)
            split_point = pop_size // 2

            best_indices = sorted_indices[:split_point]
            worst_indices = sorted_indices[split_point:]

            if best_indices.numel() > 0 and worst_indices.numel() > 0:
                # Repeat best indices if population is odd so every worst slot is replaced
                repeat_factor = (
                    worst_indices.numel() + best_indices.numel() - 1
                ) // best_indices.numel()
                clone_indices = best_indices.repeat(repeat_factor)[
                    : worst_indices.numel()
                ]

                replacements = population_full.index_select(0, clone_indices)
                population_full.index_copy_(0, worst_indices, replacements)

                fitness_replacements = fitness.index_select(0, clone_indices)
                fitness.index_copy_(0, worst_indices, fitness_replacements)

        population_out = self._scatter_population_from_full(
            population_full, population_spec, shard_meta
        )
        return population_out, fitness

    def _apply_elimination_phase(
        self,
        closure: Callable,
        group: Dict[str, Any],
        group_state: BFOGroupState,
        population: torch.Tensor,
        fitness: Optional[torch.Tensor],
        param_dim: int,
        max_iters_tensor: torch.Tensor,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Perform elimination-dispersal with adaptive respawn policies."""
        fitness_dtype = group_state.best_fitness.dtype
        group_id = self._get_group_id(group)
        shard_meta = (
            group_state.population_shard
            if group_state.population_shard is not None
            else self._compute_shard_meta(
                population.shape[0]
                if not isinstance(population, DTensor)
                else int(population.size(0))
            )
        )
        population_full, population_spec = self._gather_population_full(
            population,
            shard_meta,
            tag=f"elimination.group{group_id}",
        )
        pop_size = population_full.shape[0]

        if fitness is None:
            with record_function("bfo/evaluate_population"):
                population_eval = (
                    population_full
                    if population_spec is None
                    else self._wrap_local_like_dtensor(
                        population_full[shard_meta.slice].clone(), population_spec
                    )
                )
                fitness = self._evaluate_batch_closure(closure, group, population_eval)

        mean_position = population_full.mean(dim=0)
        diversity = torch.norm(population_full - mean_position, dim=1).mean()
        iteration = group_state.iteration.to(fitness_dtype)
        progress = torch.clamp(iteration / max_iters_tensor, 0.0, 1.0)
        decay = torch.maximum(
            torch.tensor(0.1, device=self.device, dtype=fitness_dtype),
            1.0 - progress,
        )
        diversity_threshold = torch.maximum(
            torch.tensor(1e-3, device=self.device, dtype=fitness_dtype),
            torch.tensor(0.01 * param_dim, device=self.device, dtype=fitness_dtype)
            * decay,
        )

        elim_prob = torch.tensor(
            group["elimination_prob"], device=self.device, dtype=fitness_dtype
        )
        stagnation = group_state.stagnation_count.to(fitness_dtype)
        elim_prob = torch.where(
            stagnation > torch.tensor(5.0, device=self.device, dtype=fitness_dtype),
            torch.minimum(
                torch.tensor(0.5, device=self.device, dtype=fitness_dtype),
                elim_prob * 1.5,
            ),
            elim_prob,
        )

        low_diversity = diversity < diversity_threshold
        elim_prob = torch.where(
            low_diversity,
            torch.minimum(
                torch.tensor(0.8, device=self.device, dtype=fitness_dtype),
                elim_prob * 3.0,
            ),
            elim_prob,
        )

        base_ratio = torch.tensor(
            group["global_respawn_ratio"],
            device=self.device,
            dtype=fitness_dtype,
        )
        if group["adaptive_global_respawn"]:
            diversity_ratio = torch.where(
                diversity_threshold
                > torch.tensor(self._EPS, device=self.device, dtype=fitness_dtype),
                diversity / torch.clamp(diversity_threshold, min=self._EPS),
                torch.ones_like(diversity),
            )
            adaptive_ratio = torch.where(
                diversity_ratio < 0.5,
                torch.minimum(
                    torch.tensor(0.9, device=self.device, dtype=fitness_dtype),
                    base_ratio * 2.0,
                ),
                torch.where(
                    diversity_ratio < 1.0,
                    torch.minimum(
                        torch.tensor(0.75, device=self.device, dtype=fitness_dtype),
                        base_ratio * 1.5,
                    ),
                    base_ratio,
                ),
            )
        else:
            adaptive_ratio = base_ratio

        eliminate_mask = (
            torch.rand(pop_size, device=self.device, dtype=fitness_dtype) < elim_prob
        )
        with record_function("bfo/elimination"):
            global_mask = (
                torch.rand(pop_size, device=self.device, dtype=fitness_dtype)
                < adaptive_ratio
            ) & eliminate_mask

            if self.domain_bounds is not None:
                lb, ub = self.domain_bounds
                respawn_global = torch.rand_like(population_full) * (ub - lb) + lb
            else:
                respawn_global = torch.randn_like(population_full) * 5.0

            respawn_local = (
                group_state.best_params.unsqueeze(0)
                + torch.randn_like(population_full) * group_state.current_step_size
            )

            self._apply_domain_bounds(respawn_global)
            self._apply_domain_bounds(respawn_local)

            respawn_candidates = torch.where(
                global_mask.unsqueeze(1), respawn_global, respawn_local
            )
            population_full = torch.where(
                eliminate_mask.unsqueeze(1), respawn_candidates, population_full
            )
            fitness = torch.where(
                eliminate_mask,
                torch.full_like(fitness, float("inf")),
                fitness,
            )

        population_out = self._scatter_population_from_full(
            population_full, population_spec, shard_meta
        )
        return population_out, fitness

    def _optimization_step(
        self, closure: Callable, group: Dict[str, Any], group_state: BFOGroupState
    ) -> BFOGroupState:
        """Core optimization step for a parameter group."""
        population = group_state.population
        pop_size, param_dim = population.shape
        fitness_dtype = group_state.best_fitness.dtype
        fitness: Optional[torch.Tensor] = None

        max_iters = (
            group["elimination_steps"]
            * group["reproduction_steps"]
            * group["chemotaxis_steps"]
        )
        max_iters_tensor = torch.tensor(
            max(max_iters, 1), device=self.device, dtype=fitness_dtype
        )

        fe_budget: Optional[torch.Tensor] = None
        estimated_fe_tensor: Optional[torch.Tensor] = None
        if hasattr(self, "_max_fe") and self._max_fe is not None:
            fe_budget = torch.tensor(
                self._max_fe,
                device=self.device,
                dtype=group_state.function_evaluations.dtype,
            )
            estimated_fe_tensor = torch.tensor(
                pop_size * (1 + group["swim_length"]),
                device=self.device,
                dtype=group_state.function_evaluations.dtype,
            )

        for _ in range(group["elimination_steps"]):
            for _ in range(group["reproduction_steps"]):
                population, fitness, budget_hit = self._perform_chemotaxis_phase(
                    closure,
                    group,
                    group_state,
                    population,
                    fe_budget,
                    estimated_fe_tensor,
                )
                if budget_hit:
                    shard_meta = (
                        group_state.population_shard
                        if group_state.population_shard is not None
                        else self._compute_shard_meta(
                            population.shape[0]
                            if not isinstance(population, DTensor)
                            else int(population.size(0))
                        )
                    )
                    self._ensure_population_meta(group_state, population, shard_meta)
                    return group_state

                population, fitness = self._apply_reproduction_phase(
                    group_state, population, fitness
                )
                shard_meta = (
                    group_state.population_shard
                    if group_state.population_shard is not None
                    else self._compute_shard_meta(
                        population.shape[0]
                        if not isinstance(population, DTensor)
                        else int(population.size(0))
                    )
                )
                self._ensure_population_meta(group_state, population, shard_meta)

            population, fitness = self._apply_elimination_phase(
                closure,
                group,
                group_state,
                population,
                fitness,
                param_dim,
                max_iters_tensor,
            )
            shard_meta = (
                group_state.population_shard
                if group_state.population_shard is not None
                else self._compute_shard_meta(
                    population.shape[0]
                    if not isinstance(population, DTensor)
                    else int(population.size(0))
                )
            )
            self._ensure_population_meta(group_state, population, shard_meta)

        shard_meta = (
            group_state.population_shard
            if group_state.population_shard is not None
            else self._compute_shard_meta(
                population.shape[0]
                if not isinstance(population, DTensor)
                else int(population.size(0))
            )
        )
        self._ensure_population_meta(group_state, population, shard_meta)
        self._history_push(group_state, group_state.best_fitness)
        group_state.iteration = group_state.iteration + 1
        return group_state

    def get_function_evaluations(self) -> int:
        """Get the total number of function evaluations performed."""
        total_evals = 0
        for group in self.param_groups:
            group_id = self._get_group_id(group)
            if group_id in self.bfo_state:
                fe_value = getattr(
                    self.bfo_state[group_id], "function_evaluations", 0
                )
                if isinstance(fe_value, torch.Tensor):
                    total_evals += int(fe_value.item())
                else:
                    total_evals += int(fe_value)
        return total_evals

    def step(
        self,
        closure: Optional[Callable] = None,
        max_fe: Optional[int] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> float:
        """
        Perform a single optimization step.

        Arguments:
            closure (callable, optional): A closure that reevaluates the model
                and returns the loss. Required for BFO.
            max_fe (int, optional): Maximum function evaluations allowed.
            callback (callable, optional): Progress callback function that receives
                a dict with keys: 'iteration', 'best_fitness', 'population_diversity',
                'function_evaluations', 'stagnation_count'.

        Returns:
            float: Best fitness value found across all parameter groups
        """
        if closure is None:
            raise ValueError(
                "BFO requires a closure that returns the loss. "
                "Example: def closure(): return model(data).pow(2).sum().item()"
            )

        # Set max_fe for budget checking in optimization step
        self._max_fe = max_fe

        best_fitness = float("inf")

        for group in self.param_groups:
            group_id = self._get_group_id(group)

            # Initialize group state if not present
            if group_id not in self.bfo_state:
                self._initialize_group_state(group)

            group_state = self.bfo_state[group_id]

            # Run optimization step
            group_state = self._compiled_step(closure, group, group_state)
            self.bfo_state[group_id] = group_state

            # Update parameters with best solution
            param_list = self._unflatten_group_params(
                group_state.best_params, group_state.param_shapes
            )
            for p, new_p in zip(group["params"], param_list):
                p.data.copy_(new_p)

            # Track best fitness across all groups
            best_value = float(group_state.best_fitness.item())
            best_fitness = min(best_fitness, best_value)

            # Calculate diversity for logging/callback
            population_full, _, _ = self._population_full_view(group_state)
            pop_mean = population_full.mean(dim=0)
            diversity = torch.norm(
                population_full - pop_mean, dim=1
            ).mean().item()
            iteration = int(group_state.iteration.item())
            stagnation = int(group_state.stagnation_count.item())
            step_scale = float(group_state.current_step_size.item())
            fe_count = int(group_state.function_evaluations.item())

            # Log progress
            logger.debug(
                f"Step {iteration}: best_fitness={best_value:.6e}, "
                f"diversity={diversity:.4f}, step_size={step_scale:.4e}, "
                f"fe={fe_count}"
            )

            # Invoke callback if provided
            if callback is not None:
                callback(
                    {
                        "iteration": iteration,
                        "best_fitness": best_value,
                        "population_diversity": diversity,
                        "function_evaluations": fe_count,
                        "stagnation_count": stagnation,
                        "current_step_size": step_scale,
                    }
                )

            # Early stopping check
            if (
                self.early_stopping
                and stagnation >= self.convergence_patience
            ):
                logger.warning(
                    f"Early stopping triggered for group {group_id}: "
                    f"{stagnation} steps without improvement"
                )

        return best_fitness

    def state_dict(self) -> Dict[str, Any]:
        """Return the optimizer's state as a dictionary."""
        state_dict = super().state_dict()

        # Add BFO-specific state
        bfo_state = {}
        for group_id, group_state in self.bfo_state.items():
            population_full, _, _ = self._population_full_view(group_state)
            bfo_state[group_id] = {
                "population": population_full.clone(),
                "population_size": int(population_full.shape[0]),
                "best_params": group_state.best_params.clone(),
                "best_fitness": group_state.best_fitness.clone(),
                "prev_best_fitness": group_state.prev_best_fitness.clone(),
                "current_step_size": group_state.current_step_size.clone(),
                "stagnation_count": group_state.stagnation_count.clone(),
                "iteration": group_state.iteration.clone(),
                "function_evaluations": group_state.function_evaluations.clone(),
                "param_shapes": group_state.param_shapes,
                "dtype": group_state.dtype,
                "fitness_history_buffer": group_state.fitness_history_buffer.clone(),
                "fitness_history_length": group_state.fitness_history_length.clone(),
            }
            if group_state.per_bacterium_step_size is not None:
                bfo_state[group_id]["per_bacterium_step_size"] = (
                    group_state.per_bacterium_step_size.clone()
                )
            if group_state.momentum_buffer is not None:
                bfo_state[group_id]["momentum_buffer"] = group_state.momentum_buffer.clone()
            bfo_state[group_id]["param_vector"] = group_state.param_vector.clone()

        state_dict["bfo_state"] = bfo_state

        # Add RNG state for reproducibility
        state_dict["rng_state"] = {
            "torch_rng": torch.get_rng_state(),
            "numpy_rng": np.random.get_state(),
        }

        if torch.cuda.is_available():
            state_dict["rng_state"]["cuda_rng"] = torch.cuda.get_rng_state()

        return state_dict

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load the optimizer's state."""
        # Restore RNG states
        if "rng_state" in state_dict:
            torch.set_rng_state(state_dict["rng_state"]["torch_rng"])
            np.random.set_state(state_dict["rng_state"]["numpy_rng"])
            if "cuda_rng" in state_dict["rng_state"] and torch.cuda.is_available():
                torch.cuda.set_rng_state(state_dict["rng_state"]["cuda_rng"])

        # Restore BFO-specific state
        if "bfo_state" in state_dict:
            for group_id, group_state_dict in state_dict["bfo_state"].items():
                group_id_int = int(group_id) if isinstance(group_id, str) else group_id
                if group_id_int not in self.bfo_state:
                    self.bfo_state[group_id_int] = {}

                param_group = self.param_groups[group_id_int]
                population_full = group_state_dict["population"].to(self.device)
                best_params = group_state_dict["best_params"].to(self.device)
                dtype = group_state_dict.get("dtype", param_group["params"][0].dtype)

                def _to_tensor(value, dtype, default):
                    if value is None:
                        value = default
                    if isinstance(value, torch.Tensor):
                        return value.to(self.device, dtype=dtype)
                    return torch.tensor(value, device=self.device, dtype=dtype)

                best_fitness_tensor = _to_tensor(
                    group_state_dict.get("best_fitness"),
                    torch.float32,
                    float("inf"),
                )
                prev_best_tensor = _to_tensor(
                    group_state_dict.get("prev_best_fitness"),
                    best_fitness_tensor.dtype,
                    best_fitness_tensor,
                )
                current_step_tensor = _to_tensor(
                    group_state_dict.get("current_step_size"),
                    dtype,
                    param_group.get("step_size_max", 0.1),
                )
                stagnation_tensor = _to_tensor(
                    group_state_dict.get("stagnation_count"),
                    torch.int64,
                    0,
                )
                iteration_tensor = _to_tensor(
                    group_state_dict.get("iteration"),
                    torch.int64,
                    0,
                )
                function_eval_tensor = _to_tensor(
                    group_state_dict.get("function_evaluations"),
                    torch.int64,
                    0,
                )

                if "fitness_history_buffer" in group_state_dict:
                    history_buffer = group_state_dict["fitness_history_buffer"].to(self.device)
                    history_length = _to_tensor(
                        group_state_dict.get("fitness_history_length"),
                        torch.int64,
                        min(history_buffer.numel(), self.history_window),
                    )
                else:
                    history_buffer = self._init_history_buffer(best_fitness_tensor.dtype)
                    history_list = group_state_dict.get("fitness_history", [])
                    tail = history_list[-self.history_window :]
                    if tail:
                        tail_tensor = torch.tensor(
                            tail,
                            device=self.device,
                            dtype=history_buffer.dtype,
                        )
                        history_buffer[-len(tail_tensor) :] = tail_tensor
                    history_length = torch.tensor(
                        min(len(tail), self.history_window),
                        device=self.device,
                        dtype=torch.int64,
                    )

                param_shapes_raw = group_state_dict.get("param_shapes")
                if param_shapes_raw:
                    param_shapes = [torch.Size(s) for s in param_shapes_raw]
                else:
                    _, param_shapes = self._flatten_group_params(param_group)

                param_vector_src = group_state_dict.get("param_vector")
                if isinstance(param_vector_src, torch.Tensor):
                    param_vector = param_vector_src.to(self.device, dtype=dtype)
                else:
                    param_vector = best_params.clone()

                per_bacterium = group_state_dict.get("per_bacterium_step_size")
                if isinstance(per_bacterium, torch.Tensor):
                    per_bacterium = per_bacterium.to(self.device, dtype=dtype)
                else:
                    per_bacterium = None

                new_state = BFOGroupState(
                    param_vector=param_vector,
                    param_shapes=param_shapes,
                    population=population_full,
                    best_params=best_params,
                    best_fitness=best_fitness_tensor,
                    prev_best_fitness=prev_best_tensor,
                    current_step_size=current_step_tensor,
                    stagnation_count=stagnation_tensor,
                    iteration=iteration_tensor,
                    dtype=dtype,
                    fitness_history_buffer=history_buffer,
                    fitness_history_length=history_length,
                    function_evaluations=function_eval_tensor,
                    per_bacterium_step_size=per_bacterium,
                )
                new_state.group_id = group_id_int

                if "momentum_buffer" in group_state_dict:
                    new_state.momentum_buffer = group_state_dict["momentum_buffer"].to(
                        self.device
                    )

                self._update_population_from_full(new_state, population_full)
                new_state.batch_eval_rng = self._make_generator(group_id_int)
                self.bfo_state[group_id_int] = new_state
        # Restore parent state
        parent_state_dict = {
            k: v for k, v in state_dict.items() if k not in ["bfo_state", "rng_state"]
        }
        super().load_state_dict(parent_state_dict)


class AdaptiveBFO(BFO):
    """
    Adaptive Bacterial Foraging Optimization (BFO) optimizer.

    Extends BFO with adaptive parameter adjustment based on performance.
    Automatically tunes population size, step sizes, and elimination probability.

    Additional Arguments:
        adaptation_rate (float, optional): Rate of parameter adaptation (default: 0.1)
        min_population_size (int, optional): Minimum population size (default: 10)
        max_population_size (int, optional): Maximum population size (default: 100)
        diversity_threshold (float, optional): Minimum population diversity (default: 1e-3)
    """

    def __init__(
        self,
        params,
        adaptation_rate: float = 0.1,
        min_population_size: int = 10,
        max_population_size: int = 100,
        diversity_threshold: float = 1e-3,
        **kwargs,
    ):
        super().__init__(params, **kwargs)

        self.adaptation_rate = adaptation_rate
        self.min_population_size = min_population_size
        self.max_population_size = max_population_size
        self.diversity_threshold = diversity_threshold

    def _compute_population_diversity(
        self,
        population: Union[torch.Tensor, "DTensor"],
        shard_meta: Optional[ShardMeta] = None,
    ) -> float:
        """Compute population diversity metric."""
        if DTensor is not None and isinstance(population, DTensor):
            meta = (
                shard_meta
                if shard_meta is not None
                else self._compute_shard_meta(int(population.size(0)))
            )
            population_full, _ = self._gather_population_full(
                population,
                meta,
                tag="adaptive_diversity",
            )
        else:
            population_full = population

        if population_full.shape[0] <= 1:
            return 0.0

        mean_pos = population_full.mean(dim=0)
        diversity = torch.norm(population_full - mean_pos, dim=1).mean()
        return float(diversity.item())

    def _adapt_parameters(
        self, group: Dict[str, Any], group_state: BFOGroupState, closure: Callable
    ) -> None:
        """Adapt optimization parameters based on performance."""
        if not self._history_has(group_state, 5):
            return

        recent_improvement = float(
            torch.abs(
                self._history_get(group_state, 1)
                - self._history_get(group_state, 5)
            ).item()
        )

        # Adapt population size based on progress
        if group_state.population_shape:
            current_pop_size = int(group_state.population_shape[0])
        else:
            population_full, _, _ = self._population_full_view(group_state)
            current_pop_size = int(population_full.shape[0])
        if recent_improvement < self.convergence_tolerance:
            # Increase population if stagnating
            new_pop_size = min(
                self.max_population_size,
                int(current_pop_size * (1 + self.adaptation_rate)),
            )
        elif recent_improvement > 0.01:
            # Decrease population if making good progress
            new_pop_size = max(
                self.min_population_size,
                int(current_pop_size * (1 - self.adaptation_rate)),
            )
        else:
            new_pop_size = current_pop_size

        # Resize population if needed
        if new_pop_size != current_pop_size:
            self._resize_population(group, group_state, new_pop_size, closure)

        # Adapt elimination probability based on diversity
        diversity = self._compute_population_diversity(
            group_state.population, group_state.population_shard
        )
        if diversity < self.diversity_threshold:
            group["elimination_prob"] = min(0.5, group["elimination_prob"] * 1.2)

    def _resize_population(
        self,
        group: Dict[str, Any],
        group_state: BFOGroupState,
        new_size: int,
        closure: Callable,
    ) -> None:
        """Resize population while preserving best solutions."""
        population_full, _, _ = self._population_full_view(group_state)
        current_size = int(population_full.shape[0])

        if new_size == current_size:
            return

        if new_size > current_size:
            # Add new individuals around best solution
            additional = new_size - current_size
            new_individuals = (
                group_state.best_params.unsqueeze(0)
                + torch.randn(
                    additional,
                    population_full.shape[1],
                    device=self.device,
                    dtype=group_state.dtype,
                )
                * group_state.current_step_size
            )
            self._apply_domain_bounds(new_individuals)
            population_full = torch.cat([population_full, new_individuals], dim=0)
        else:
            # Keep best individuals by evaluating current fitness
            # Use _evaluate_batch_closure to properly track function evaluations
            fitness = self._evaluate_batch_closure(
                closure, group, group_state.population
            )

            # Sort by fitness and keep the best
            sorted_indices = torch.argsort(fitness)
            keep_indices = sorted_indices[:new_size]
            population_full = population_full.index_select(
                0, keep_indices.to(torch.long)
            )

        # Update group population size
        group["population_size"] = new_size
        self._update_population_from_full(group_state, population_full)

    def step(
        self, closure: Optional[Callable] = None, max_fe: Optional[int] = None
    ) -> float:
        """Perform optimization step with parameter adaptation."""
        if closure is None:
            raise ValueError("AdaptiveBFO requires a closure.")

        # Adapt parameters for each group *before* the optimization step
        for group in self.param_groups:
            group_id = self._get_group_id(group)
            if group_id in self.bfo_state:
                self._adapt_parameters(group, self.bfo_state[group_id], closure)

        # Now, perform the optimization step with the (potentially) resized population
        fitness = super().step(closure, max_fe=max_fe)

        return fitness

    def state_dict(self) -> Dict[str, Any]:
        """Return the optimizer's state, including adaptive parameters."""
        state_dict = super().state_dict()
        for group in self.param_groups:
            group_id = self._get_group_id(group)
            if group_id in state_dict["bfo_state"]:
                state_dict["bfo_state"][group_id]["population_size"] = group[
                    "population_size"
                ]
        return state_dict

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load the optimizer's state, including adaptive parameters."""
        super().load_state_dict(state_dict)
        for group in self.param_groups:
            group_id = self._get_group_id(group)
            if (
                "bfo_state" in state_dict
                and group_id in state_dict["bfo_state"]
                and "population_size" in state_dict["bfo_state"][group_id]
            ):
                group["population_size"] = state_dict["bfo_state"][group_id][
                    "population_size"
                ]


class HybridBFO(BFO):
    """
    Hybrid Bacterial Foraging Optimization (BFO) optimizer.

    Combines BFO with gradient information when available for faster convergence
    on differentiable problems. Includes a safety check for momentum.

    Additional Arguments:
        gradient_weight (float, optional): Weight for gradient contribution (default: 0.5)
        momentum (float, optional): Momentum coefficient for gradient updates (default: 0.9)
        enable_momentum (bool, optional): Enable momentum for gradients (default: True)
    """

    def __init__(
        self,
        params,
        gradient_weight: float = 0.5,
        momentum: float = 0.9,
        enable_momentum: bool = True,
        **kwargs,
    ):
        super().__init__(params, **kwargs)

        self.gradient_weight = gradient_weight
        self.momentum = momentum
        self.enable_momentum = enable_momentum

        if self.enable_momentum and self.momentum == 0:
            self.enable_momentum = False

        # Initialize momentum buffers for each parameter group
        if self.enable_momentum:
            for group in self.param_groups:
                group_id = self._get_group_id(group)
                if group_id not in self.bfo_state:
                    self._initialize_group_state(group)
                state = self.bfo_state[group_id]
                state.momentum_buffer = torch.zeros_like(state.param_vector)

    def _has_gradients(self, group: Dict[str, Any]) -> bool:
        """Check if any parameters in group have gradients."""
        return any(p.grad is not None for p in group["params"])

    def _collect_gradients(self, group: Dict[str, Any]) -> torch.Tensor:
        """Collect gradients from parameter group."""
        grad_list = []
        for p in group["params"]:
            if p.grad is not None:
                grad_list.append(p.grad.view(-1))
            else:
                grad_list.append(
                    torch.zeros(p.numel(), device=self.device, dtype=p.dtype)
                )

        return torch.cat(grad_list).to(self.device)

    def _apply_gradient_bias(
        self, group: Dict[str, Any], group_state: BFOGroupState
    ) -> None:
        """Apply gradient-based bias to population."""
        if not self._has_gradients(group) or self.gradient_weight == 0:
            return

        group_id = self._get_group_id(group)
        grad_vector = self._collect_gradients(group)

        # Apply momentum if enabled
        if self.enable_momentum:
            momentum_buffer = getattr(self.bfo_state[group_id], "momentum_buffer", None)
            if momentum_buffer is not None:
                momentum_buffer.mul_(self.momentum).add_(
                    grad_vector, alpha=1 - self.momentum
                )
                grad_vector = momentum_buffer.clone()

        # Gradient descent step
        gradient_step = -group["lr"] * grad_vector

        # Bias population towards gradient direction from current best params
        population_full, _, _ = self._population_full_view(group_state)
        gradient_bias = group_state.best_params + gradient_step
        population_full = (
            population_full * (1 - self.gradient_weight)
            + gradient_bias.unsqueeze(0) * self.gradient_weight
        )
        self._update_population_from_full(group_state, population_full)

    def step(
        self, closure: Optional[Callable] = None, max_fe: Optional[int] = None
    ) -> float:
        """Perform hybrid optimization step."""
        # Apply gradient bias before BFO step
        for group in self.param_groups:
            group_id = self._get_group_id(group)
            if group_id in self.bfo_state:
                self._apply_gradient_bias(group, self.bfo_state[group_id])

        # Perform BFO step
        fitness = super().step(closure, max_fe=max_fe)

        # Adaptive gradient weight based on improvement
        for group in self.param_groups:
            group_id = self._get_group_id(group)
            if group_id in self.bfo_state:
                group_state = self.bfo_state[group_id]
                if self._history_has(group_state, 5):
                    recent_improvement = float(
                        torch.abs(
                            self._history_get(group_state, 1)
                            - self._history_get(group_state, 5)
                        ).item()
                    )
                    if recent_improvement < self.convergence_tolerance:
                        self.gradient_weight = max(0.1, self.gradient_weight * 0.95)

        return fitness

    def state_dict(self) -> Dict[str, Any]:
        """Return the optimizer's state, including momentum buffers."""
        state_dict = super().state_dict()
        # Add momentum buffers to saved state
        for group in self.param_groups:
            group_id = self._get_group_id(group)
            if group_id in state_dict["bfo_state"] and "momentum_buffer" in self.bfo_state[group_id]:
                state_dict["bfo_state"][group_id]["momentum_buffer"] = (
                    self.bfo_state[group_id]["momentum_buffer"].clone()
                )
        return state_dict

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load state dict and ensure momentum buffers are properly initialized."""
        # Call parent's load_state_dict
        super().load_state_dict(state_dict)

        # Reinitialize momentum buffers if needed
        if self.enable_momentum:
            for group in self.param_groups:
                group_id = self._get_group_id(group)
                if (
                    group_id in self.bfo_state
                    and "momentum_buffer" not in self.bfo_state[group_id]
                ):
                    param_vector, _ = self._flatten_group_params(group)
                    self.bfo_state[group_id]["momentum_buffer"] = torch.zeros_like(
                        param_vector
                    )
