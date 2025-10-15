"""
Minimal utility helpers for distributed-aware execution in bfo_torch.

This file intentionally exposes only the pieces required by the GPU-enabled
optimizer (seed partitioning and distributed context resolution) so we can
ship a focused CUDA smoke-testing branch without the full benchmarking
toolkit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

import torch

try:  # torch.distributed is optional
    import torch.distributed as dist  # type: ignore

    _HAS_DIST = dist.is_available()
except Exception:  # pragma: no cover - torch.distributed unavailable
    dist = None  # type: ignore
    _HAS_DIST = False


@dataclass
class DistributedContext:
    """Lightweight view of the current distributed execution environment."""

    rank: int = 0
    local_rank: int = 0
    world_size: int = 1
    is_distributed: bool = False


def resolve_distributed_context() -> DistributedContext:
    """
    Infer rank/local_rank/world_size from torch.distributed or common env vars.

    Returns:
        DistributedContext describing the current process topology.
    """

    if _HAS_DIST and dist.is_initialized():
        try:
            rank = dist.get_rank()
            world_size = dist.get_world_size()
            local_rank = dist.get_rank(group=dist.group.WORLD)
        except Exception:  # pragma: no cover - defensive fallback
            rank = dist.get_rank()
            world_size = dist.get_world_size()
            local_rank = int(torch.cuda.current_device()) if torch.cuda.is_available() else rank
        return DistributedContext(
            rank=rank,
            local_rank=local_rank,
            world_size=world_size,
            is_distributed=True,
        )

    # torchrun sets these environment variables; honour them if present
    env_rank = os.getenv("RANK")
    env_local = os.getenv("LOCAL_RANK", env_rank)
    env_world = os.getenv("WORLD_SIZE")
    if env_rank is not None and env_world is not None:
        return DistributedContext(
            rank=int(env_rank),
            local_rank=int(env_local) if env_local is not None else int(env_rank),
            world_size=int(env_world),
            is_distributed=int(env_world) > 1,
        )

    return DistributedContext()


def make_generator_for_rank(
    base_seed: int,
    *,
    rank: int,
    world_size: int,
    batch_id: int = 0,
    device: Optional[torch.device] = None,
) -> torch.Generator:
    """
    Derive a `torch.Generator` that is unique per rank/batch combination.
    """

    if base_seed is None:
        raise ValueError("base_seed must be provided for deterministic seeding.")
    if world_size <= 0:
        raise ValueError(f"world_size must be positive, got {world_size}.")
    if not (0 <= rank < world_size):
        raise ValueError(f"rank must be in [0, {world_size}), got {rank}.")

    gen = torch.Generator(device=device)
    offset = int(base_seed) + batch_id * int(world_size) + int(rank)
    gen.manual_seed(offset)
    return gen


def partition_seed_for_rank(
    base_seed: int,
    *,
    rank: int,
    world_size: int,
    run_id: int = 0,
) -> int:
    """
    Deterministically map a base seed to the current rank.
    """

    if base_seed is None:
        raise ValueError("base_seed must be provided for deterministic seeding.")
    if world_size <= 0:
        raise ValueError(f"world_size must be positive, got {world_size}.")
    if not (0 <= rank < world_size):
        raise ValueError(f"rank must be in [0, {world_size}), got {rank}.")

    return int(base_seed) + run_id * int(world_size) + int(rank)


def shard_population(
    population: torch.Tensor,
    rank: int,
    world_size: int,
) -> Tuple[torch.Tensor, dict]:
    """
    Evenly split a population tensor across ranks for distributed evaluation.
    """

    if population.dim() == 0:
        raise ValueError("population tensor must be at least 1-D.")
    pop_size = population.size(0)
    if world_size <= 0:
        raise ValueError("world_size must be positive.")
    if not (0 <= rank < world_size):
        raise ValueError(f"rank must be in [0, {world_size}), got {rank}.")

    counts = pop_size // world_size
    remainder = pop_size % world_size
    start = rank * counts + min(rank, remainder)
    end = start + counts + (1 if rank < remainder else 0)
    shard = population[start:end]
    metadata = {
        "rank": rank,
        "world_size": world_size,
        "start": start,
        "end": end,
        "count": end - start,
    }
    return shard, metadata


__all__ = [
    "DistributedContext",
    "resolve_distributed_context",
    "make_generator_for_rank",
    "partition_seed_for_rank",
    "shard_population",
]
