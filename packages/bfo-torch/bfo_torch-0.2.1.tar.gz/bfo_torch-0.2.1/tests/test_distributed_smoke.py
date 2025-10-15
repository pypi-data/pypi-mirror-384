import os

import pytest
import torch

from bfo_torch import BFO
from bfo_torch.utils import resolve_distributed_context


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required for distributed smoke")
def test_bfo_multi_rank_smoke():
    ctx = resolve_distributed_context()
    if ctx is None or not ctx.is_distributed or ctx.world_size < 2:
        pytest.skip("requires distributed world >= 2")

    rank = int(ctx.rank)
    local_rank = int(ctx.local_rank)

    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)

    torch.manual_seed(1234 + rank)
    torch.cuda.manual_seed_all(1234 + rank)

    param = torch.nn.Parameter(torch.randn(4, device=device))
    optimizer = BFO([param], population_size=16, device=device, compile_mode=None)

    def closure():
        return (param.detach() ** 2).sum().item()

    fitness = optimizer.step(closure)

    debug_enabled = os.getenv("BFO_DIST_DEBUG", "0").lower() in ("1", "true", "yes")
    if debug_enabled:
        print(f"[dist_smoke] rank={rank} entering barrier", flush=True)
    torch.distributed.barrier()
    if debug_enabled:
        print(f"[dist_smoke] rank={rank} exited barrier", flush=True)

    assert isinstance(fitness, float)
    assert fitness >= 0
