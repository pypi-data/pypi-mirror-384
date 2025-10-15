"""
Lightweight benchmarking utilities for bfo_torch.

This module provides a small suite of analytic benchmark problems alongside a
runner that executes the BFO optimizers with configurable settings. It is not
intended to be a comprehensive benchmarking harness, but it gives enough
structure to stress-test multi-GPU setups and compare behaviour across variants.
"""

from __future__ import annotations

import math
import time
import warnings
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import torch

try:  # torch.distributed is optional
    import torch.distributed as dist  # type: ignore

    _HAS_DIST = dist.is_available()
except Exception:  # pragma: no cover - distributed backend unavailable
    dist = None  # type: ignore
    _HAS_DIST = False

from ..optimizer import BFO
from ..utils import DistributedContext, resolve_distributed_context


ScalarFn = Callable[[torch.Tensor], torch.Tensor]


@dataclass(frozen=True)
class BenchmarkProblem:
    """Analytic optimisation problem specification."""

    name: str
    dimension: int
    target: float
    evaluate: ScalarFn
    bounds: Optional[Tuple[float, float]] = None

    def sample_initial(
        self,
        device: torch.device,
        generator: Optional[torch.Generator],
    ) -> torch.Tensor:
        """
        Draw an initial parameter vector for this problem.
        """

        if self.bounds is not None:
            low, high = self.bounds
            tensor = torch.empty(self.dimension, device=device)
            return tensor.uniform_(low, high, generator=generator)

        return torch.randn(self.dimension, device=device, generator=generator)


@dataclass
class BenchmarkConfig:
    """Configuration for BFO benchmark runs."""

    runs: int = 51
    population_size: int = 128
    chemotaxis_steps: int = 4
    reproduction_steps: int = 2
    elimination_steps: int = 1
    swim_length: int = 2
    device: torch.device = torch.device("cpu")
    success_tolerance: float = 1e-8
    history_stride: int = 500  # reserved for future use
    budget_multiplier: int = 10_000
    max_steps: int = 300
    compile_mode: Optional[str] = None
    base_seed: Optional[int] = None


class BenchmarkRunner:
    """
    Execute BFO on a set of benchmark problems and collect summary statistics.
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        *,
        context: Optional[DistributedContext] = None,
    ) -> None:
        self.config = config
        self.context = context or resolve_distributed_context()

    def run_suite(
        self,
        problems: Sequence[BenchmarkProblem],
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Run the configured benchmark suite.
        """

        results = {}
        for problem in problems:
            payload = self._run_problem(problem)
            results[problem.name] = payload
        return results

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _run_problem(self, problem: BenchmarkProblem) -> Dict[str, Dict[str, float]]:
        """
        Execute all assigned benchmark runs for a single problem.
        """

        run_indices = list(self._iter_run_indices())
        local_errors: List[float] = []
        local_times: List[float] = []
        local_evals: List[float] = []
        local_success = 0

        for run_id in run_indices:
            best_error, eval_count, duration, succeeded = self._execute_run(
                problem,
                run_id,
            )
            local_errors.append(best_error)
            local_evals.append(eval_count)
            local_times.append(duration)
            if succeeded:
                local_success += 1

        aggregated = self._aggregate_across_ranks(
            errors=local_errors,
            evals=local_evals,
            times=local_times,
            success=local_success,
            runs=len(run_indices),
        )

        errors = aggregated["errors"]
        evals = aggregated["evals"]
        times = aggregated["times"]
        success_count = aggregated["success"]
        total_runs = max(aggregated["runs"], 1)

        success_rate = success_count / float(total_runs)

        return {
            "dimension": {"mean": float(problem.dimension)},
            "success_rate": {
                "mean": success_rate,
                "std": 0.0,
                "min": success_rate,
                "max": success_rate,
            },
            "error_stats": _summarise(errors),
            "evaluation_stats": _summarise(evals),
            "time_stats": _summarise(times),
        }

    def _execute_run(
        self,
        problem: BenchmarkProblem,
        run_id: int,
    ) -> Tuple[float, float, float, bool]:
        """
        Execute a single optimisation run for the given benchmark problem.
        """

        device = self.config.device
        generator = self._make_generator(run_id)
        initial = problem.sample_initial(device, generator)
        param = torch.nn.Parameter(initial.clone())

        optimizer = BFO(
            [param],
            population_size=self.config.population_size,
            chemotaxis_steps=self.config.chemotaxis_steps,
            reproduction_steps=self.config.reproduction_steps,
            elimination_steps=self.config.elimination_steps,
            swim_length=self.config.swim_length,
            domain_bounds=problem.bounds,
            device=device,
            compile_mode=self.config.compile_mode,
            seed=self._seed_for_run(run_id),
        )

        eval_budget = problem.dimension * self.config.budget_multiplier
        start = time.perf_counter()
        best_error = float("inf")
        success = False

        for _ in range(self.config.max_steps):
            fitness = optimizer.step(
                lambda: float(problem.evaluate(param).item()),
                max_fe=eval_budget,
            )
            current_error = abs(fitness - problem.target)
            best_error = min(best_error, current_error)

            if current_error <= self.config.success_tolerance:
                success = True
                break

        duration = time.perf_counter() - start
        eval_count = float(optimizer.get_function_evaluations())
        return best_error, eval_count, duration, success

    def _aggregate_across_ranks(
        self,
        *,
        errors: List[float],
        evals: List[float],
        times: List[float],
        success: int,
        runs: int,
    ) -> Dict[str, List[float]]:
        """
        Combine metrics from all ranks when running under torch.distributed.
        """

        if not (self.context.is_distributed and _HAS_DIST and dist.is_initialized()):
            return {
                "errors": errors,
                "evals": evals,
                "times": times,
                "success": success,
                "runs": runs,
            }

        payload = {
            "errors": errors,
            "evals": evals,
            "times": times,
            "success": success,
            "runs": runs,
        }
        gathered: List[Dict[str, List[float]]] = [
            {} for _ in range(self.context.world_size)
        ]
        dist.all_gather_object(gathered, payload)

        merged_errors: List[float] = []
        merged_evals: List[float] = []
        merged_times: List[float] = []
        merged_success = 0
        merged_runs = 0

        for item in gathered:
            merged_errors.extend(item.get("errors", []))
            merged_evals.extend(item.get("evals", []))
            merged_times.extend(item.get("times", []))
            merged_success += int(item.get("success", 0))
            merged_runs += int(item.get("runs", 0))

        return {
            "errors": merged_errors,
            "evals": merged_evals,
            "times": merged_times,
            "success": merged_success,
            "runs": merged_runs,
        }

    def _make_generator(self, run_id: int) -> Optional[torch.Generator]:
        """
        Create a torch.Generator seeded for the given run.
        """

        if self.config.base_seed is None:
            return None

        offset = (
            int(self.config.base_seed)
            + run_id * max(1, self.context.world_size)
            + self.context.rank
        )
        generator = torch.Generator(device=self.config.device)
        generator.manual_seed(offset)
        return generator

    def _seed_for_run(self, run_id: int) -> Optional[int]:
        """
        Produce a deterministic seed for the optimiser instance.
        """

        if self.config.base_seed is None:
            return None
        return (
            int(self.config.base_seed)
            + run_id * max(1, self.context.world_size)
            + self.context.rank
        )

    def _iter_run_indices(self) -> Iterable[int]:
        """
        Yield the run indices assigned to this rank.
        """

        total_runs = max(self.config.runs, 0)
        if total_runs == 0:
            return []

        world_size = max(self.context.world_size, 1)
        if world_size == 1:
            return range(total_runs)

        return (idx for idx in range(total_runs) if idx % world_size == self.context.rank)


# ---------------------------------------------------------------------- #
# Benchmark suites
# ---------------------------------------------------------------------- #


def get_classical_suite(dimensions: Sequence[int]) -> List[BenchmarkProblem]:
    """
    Return a list of classical analytic optimisation problems.
    """

    dims = sorted(set(int(abs(d)) for d in dimensions if int(abs(d)) > 0))
    problems: List[BenchmarkProblem] = []

    for dim in dims:
        problems.append(
            BenchmarkProblem(
                name=f"sphere_{dim}d",
                dimension=dim,
                target=0.0,
                evaluate=_sphere,
                bounds=(-5.12, 5.12),
            )
        )
        if dim >= 2:
            problems.append(
                BenchmarkProblem(
                    name=f"rosenbrock_{dim}d",
                    dimension=dim,
                    target=0.0,
                    evaluate=_rosenbrock,
                    bounds=(-2.048, 2.048),
                )
            )
        problems.append(
            BenchmarkProblem(
                name=f"rastrigin_{dim}d",
                dimension=dim,
                target=0.0,
                evaluate=_rastrigin,
                bounds=(-5.12, 5.12),
            )
        )
        problems.append(
            BenchmarkProblem(
                name=f"ackley_{dim}d",
                dimension=dim,
                target=0.0,
                evaluate=_ackley,
                bounds=(-32.768, 32.768),
            )
        )

    return problems


def get_cec2015_suite(dimensions: Sequence[int]) -> List[BenchmarkProblem]:
    """
    Placeholder CEC-style suite.

    For this branch we reuse the classical problems but warn the caller so we
    remember to replace them with the full CEC 2015 definitions later.
    """

    warnings.warn(
        "CEC benchmark suite is not fully implemented; falling back to classical problems.",
        RuntimeWarning,
        stacklevel=2,
    )
    return get_classical_suite(dimensions)


# ---------------------------------------------------------------------- #
# Analytic objective functions
# ---------------------------------------------------------------------- #


def _sphere(x: torch.Tensor) -> torch.Tensor:
    return torch.sum(x * x)


def _rosenbrock(x: torch.Tensor) -> torch.Tensor:
    if x.numel() < 2:
        return torch.tensor(0.0, device=x.device, dtype=x.dtype)
    return torch.sum(
        100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1.0 - x[:-1]) ** 2,
    )


def _rastrigin(x: torch.Tensor) -> torch.Tensor:
    n = x.numel()
    return 10.0 * n + torch.sum(x * x - 10.0 * torch.cos(2.0 * math.pi * x))


def _ackley(x: torch.Tensor) -> torch.Tensor:
    n = x.numel()
    if n == 0:
        return torch.tensor(0.0, device=x.device, dtype=x.dtype)
    sum_sq = torch.mean(x * x)
    sum_cos = torch.mean(torch.cos(2.0 * math.pi * x))
    term1 = -20.0 * torch.exp(-0.2 * torch.sqrt(sum_sq))
    term2 = -torch.exp(sum_cos)
    return term1 + term2 + 20.0 + math.e


def _summarise(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

    tensor = torch.tensor(values, dtype=torch.float64)
    mean = float(tensor.mean().item())
    if tensor.numel() > 1:
        std = float(tensor.std(unbiased=False).item())
    else:
        std = 0.0
    min_val = float(tensor.min().item())
    max_val = float(tensor.max().item())
    return {
        "mean": mean,
        "std": std,
        "min": min_val,
        "max": max_val,
    }


__all__ = [
    "BenchmarkProblem",
    "BenchmarkConfig",
    "BenchmarkRunner",
    "get_classical_suite",
    "get_cec2015_suite",
]
