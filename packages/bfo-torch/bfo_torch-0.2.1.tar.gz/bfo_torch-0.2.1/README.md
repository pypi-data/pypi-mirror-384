# bfo-torch

[![PyPI version](https://badge.fury.io/py/bfo-torch.svg)](https://badge.fury.io/py/bfo-torch)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Modern, GPU-ready Bacterial Foraging Optimization for PyTorch.

---

## Highlights

- **Device coverage** – CPU, CUDA, and Apple MPS with mixed precision (FP16, BF16,
  FP32, FP64).
- **Performance knobs** – configurable Lévy and step-size schedules, batched
  closures, `torch.compile` integration, and function evaluation budgets.
- **Distributed aware** – automatic rank/world discovery, optional DTensor
  sharding, and ready-to-run benchmarks for multi-GPU hosts.
- **Ecosystem friendly** – drop-in replacement for `torch.optim.Optimizer`,
  checkpointable via `state_dict`, and instrumented with callbacks.
- **Batteries included benchmarks** – `bfo_torch.benchmarks` powers the
  classical suite at `examples/run_benchmark_suite.py`.

---

## Installation

```bash
pip install bfo-torch
```

---

## Quick Start

```python
import torch
import torch.nn as nn
from bfo_torch import BFO

x = nn.Parameter(torch.tensor([5.0, -3.0]))
optimizer = BFO([x], population_size=32, step_schedule="adaptive")

def closure() -> float:
    loss = (x ** 2).sum()
    return float(loss.item())

for iteration in range(8):
    best = optimizer.step(closure, max_fe=2_000)
    print(f"iter={iteration:02d} best={best:.4e} x={x.data.tolist()}")
```

Use the optional `callback` argument to stream telemetry:

```python
def callback(info: dict) -> None:
    print(
        f"iter={info['iteration']:03d} "
        f"best={info['best_fitness']:.3e} "
        f"diversity={info['population_diversity']:.3f} "
        f"fe={info['function_evaluations']}"
    )

optimizer.step(closure, callback=callback)
```

Batch objectives can skip parameter swapping by supplying `batch_eval_fn`:

```python
def batched_sphere(pop: torch.Tensor) -> torch.Tensor:
    return (pop ** 2).sum(dim=1)

optimizer = BFO(
    [x],
    population_size=128,
    domain_bounds=(-5.0, 5.0),
    batch_eval_fn=batched_sphere,
)

best = optimizer.step(lambda: float(batched_sphere(x.unsqueeze(0))[0]))
```

To receive rank-local randomness or metadata, accept the optional keyword
arguments the optimiser provides (`rng` for a pre-seeded `torch.Generator`,
`shard` for distributed info).

Enable `torch.compile` for the inner optimisation loop with
`compile_mode="default"` (falls back automatically if tracing fails).

More recipes live in [docs/QUICKSTART.md](docs/QUICKSTART.md).

---

## Benchmark Runner

Stress test single- or multi-GPU hosts with the bundled classical suite. The
runner provides functional smoke/regression coverage rather than official
performance claims.

```bash
python examples/run_benchmark_suite.py classical \
  --device cuda \
  --population 128 \
  --dims 30 50 \
  --runs 12
```

For two GPUs:

```bash
torchrun --standalone --nproc_per_node=2 examples/run_benchmark_suite.py classical \
  --device cuda \
  --population 160
```

The script pins each rank to `cuda:{LOCAL_RANK}`, destroys the process group on
shutdown, and logs summaries to `logs/benchmark_*.log`.

**Suites**
- `classical` – Sphere, Rosenbrock (for dimensions ≥2), Rastrigin, and Ackley for
  every value passed via `--dims`.
- `cec` – currently reuses the classical set and emits a warning until the full
  CEC 2015 definitions arrive.

**Useful flags**
- `--population`, `--chemotaxis-steps`, `--reproduction-steps`,
  `--elimination-steps`, `--swim-length` to mirror optimiser knobs.
- `--with-compile` / `--compile-mode` to wrap the optimisation loop in
  `torch.compile`.
- `--budget-multiplier`, `--max-steps`, `--success-tol` to bound work and define
  success thresholds.
- `--seed` to partition deterministic seeds across torchrun ranks and runs.
- `--output results.json` to persist aggregate statistics for later analysis.

---

## Documentation

- [Algorithm Guide](docs/ALGORITHM.md)
- [Hyperparameter Tuning](docs/HYPERPARAMETERS.md)
- [Quick Start Recipes](docs/QUICKSTART.md)
- [Optimizer API Reference](docs/OPTIMIZER_API.md)
- [Benchmark Harness](docs/BENCHMARKS.md)

Example scripts:

- [Simple function optimisation](examples/simple_function.py)
- [Neural network training](examples/neural_network.py)
- [Hyperparameter tuning wrapper](examples/hyperparameter_tuning.py)
- [Benchmark entry point](examples/run_benchmark_suite.py)

---

## Key Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `population_size` | 50 | Candidates evolved per group |
| `chemotaxis_steps` | 10 | Tumble/swim iterations before reproduction |
| `swim_length` | 4 | Max swims after an improvement |
| `levy_alpha` | 1.5 | Lévy flight shape (1.0–2.0) |
| `levy_schedule` | `"linear-decrease"` | Scale schedule for Lévy flights |
| `step_schedule` | `"adaptive"` | Step-size update policy |
| `elimination_prob` | 0.25 | Base elimination probability |
| `global_respawn_ratio` | 0.5 | Share of respawns drawn globally |

See the [hyperparameter guide](docs/HYPERPARAMETERS.md) for deeper tuning
advice.

---

## Optimiser Variants

- **BFO** – population-based optimizer with Lévy flights and adaptive respawn.
- **AdaptiveBFO** – adjusts population size and elimination probability at
  runtime based on progress.
- **HybridBFO** – biases the swarm using model gradients before each BFO step,
  optionally with momentum.

All variants accept the same constructor arguments; extra knobs are documented
in the class docstrings. The `lr` argument acts as the gradient step size only
for hybrid variants; pure BFO dynamics rely on the Lévy and step-size schedules.

---

## Applicability

**Great for**
- Black-box optimisation where gradients are unavailable or unreliable.
- Noisy, discontinuous, or piecewise objectives.
- Hyperparameter search and compact neural architecture exploration.

**Less suited to**
- Extremely high-dimensional (>1 000 parameters) tasks without heavy tuning.
- Scenarios where cheap gradients are available (classic SGD/Adam remain faster).

---

## Implementation Overview

`BFO.step` performs a full elimination → reproduction → chemotaxis loop using
vectorised tensor ops:

1. **Chemotaxis** – Lévy-generated tumble directions optionally lead to short
   swims; evaluations are batched and can be distributed across ranks.
2. **Swarming** – attraction/repulsion forces operate on normalised direction
   vectors to prevent blow-ups while keeping distance sensitivity.
3. **Reproduction** – the elite half overwrites the worst half, handling odd
   population sizes and copying fitness values in one pass.
4. **Elimination–dispersal** – diversity and stagnation heuristics decide how
   many bacteria respawn globally versus near the current elite.

Function evaluations are counted per parameter group and exposed via
`get_function_evaluations`. The optimiser serialises its entire state (including
Lévy caches and distributed placement metadata) so jobs can be interrupted and
resumed with no drift.

---

## Distributed Notes

- Launch under `torchrun` or your preferred backend; `BFO` discovers rank and
  world size via `resolve_distributed_context()`.
- Bind each rank to its local device (`torch.cuda.set_device(local_rank)`) before
  constructing the optimiser when you are not using the benchmark runner.
- Call `torch.distributed.destroy_process_group()` during teardown of custom
  scripts to avoid NCCL leak warnings in the logs. The benchmark entry point
  handles this automatically.
