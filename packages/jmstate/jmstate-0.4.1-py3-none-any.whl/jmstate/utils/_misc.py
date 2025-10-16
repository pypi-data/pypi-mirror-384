from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import torch
from rich.tree import Tree

from ..typedefs._defs import Info, Job, Trajectory
from ..utils._dtype import get_dtype
from ..utils._surv import build_buckets

if TYPE_CHECKING:
    from ..typedefs._params import ModelParams


def legendre_quad(n_quad: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Get the Legendre quadrature nodes and weights.

    Args:
        n_quad (int): The number of quadrature points.

    Returns:
        tuple[torch.Tensor, torch.Tensor]: The nodes and weights.
    """
    nodes, weights = cast(
        tuple[
            np.ndarray[Any, np.dtype[np.float64]],
            np.ndarray[Any, np.dtype[np.float64]],
        ],
        np.polynomial.legendre.leggauss(n_quad),  # type: ignore
    )

    dtype = get_dtype()
    std_nodes = torch.tensor(nodes, dtype=dtype).unsqueeze(0)
    std_weights = torch.tensor(weights, dtype=dtype)

    return std_nodes, std_weights


def map_fn_params(
    params: ModelParams, fn: Callable[[torch.Tensor], torch.Tensor]
) -> ModelParams:
    """Map operation and get new parameters.

    Args:
        params (ModelParams): The model parameters to use.
        fn (Callable[[torch.Tensor], torch.Tensor]): The operation.

    Returns:
        ModelParams: The new parameters (it might be a reshape).
    """
    from ..typedefs._params import ModelParams  # noqa: PLC0415

    def _map_fn(dict: dict[tuple[Any, Any], torch.Tensor]):
        return {key: fn(val) for key, val in dict.items()}

    return ModelParams(
        None if params.gamma is None else fn(params.gamma),
        params.Q_repr._replace(flat=fn(params.Q_repr.flat)),
        params.R_repr._replace(flat=fn(params.R_repr.flat)),
        _map_fn(params.alphas),
        None if params.betas is None else _map_fn(params.betas),
        extra=params.extra,
        skip_validation=True,
    )


def run_jobs(jobs: list[Job], info: Info) -> bool:
    """Call jobs.

    Args:
        jobs (list[Job]): The jobs to execute.
        info (Info): The information container.

    Returns:
        bool: Set to true to stop the iterations.
    """
    stop = None
    for job in jobs:
        result = job.run(info=info)
        stop = (
            stop if result is None else (result if stop is None else (stop and result))
        )

    return False if stop is None else stop


# Descriptors
def add_x(x: torch.Tensor | None, tree: Tree):
    """Add the fixed covariates to the tree.

    Args:
        x (torch.Tensor | None): The fixed covariates.
        tree (Tree): The tree to add to.
    """
    if x is not None:
        tree.add(f"x: {x.size(0)} individual(s) with {x.size(1)} covariate(s)")


def add_t(t: torch.Tensor, tree: Tree):
    """Add the measurement times.

    Args:
        t (torch.Tensor): The measurement times.
        tree (Tree): The tree to add to.
    """
    if t.ndim == 1:
        tree.add(f"t: shared measurement times of length {t.size(0)} measurement(s)")
    else:
        tree.add(
            f"t: individual measurement times {t.size(0)} individual(s) x {t.size(1)} "
            "measurement(s)"
        )


def add_y(y: torch.Tensor, tree: Tree):
    """Add the measurements.

    Args:
        y (torch.Tensor): The measurements.
        tree (Tree): The tree to add to.
    """
    tree.add(
        f"y: {y.size(0)} individual(s) x {y.size(1)} measurement(s) x {y.size(2)} "
        "dimension(s)"
    )


def add_psi(psi: torch.Tensor, tree: Tree):
    """Add the individual parameters.

    Args:
        psi (torch.Tensor): The individual parameters.
        tree (Tree): The tree to add to.
    """
    if psi.ndim == 2:  # noqa: PLR2004
        tree.add(
            f"psi: {psi.size(0)} individual(s) x {psi.size(1)} individual parameter(s)"
        )
    else:
        tree.add(
            f"psi: {psi.size(0)} sample(s) x {psi.size(1)} individual(s) x "
            f"{psi.size(2)} individual parameter(s)"
        )


def add_trajectories(trajectories: list[Trajectory], tree: Tree):
    """Add the trajectories.

    Args:
        trajectories (list[Trajectory]): The trajectories.
        tree (Tree): The tree to add to.
    """
    buckets = build_buckets(trajectories)

    node = tree.add(
        f"trajectories: {len(trajectories)} individual(s) with "
        f"{sum(len(trajectory) - 1 for trajectory in trajectories)} obs transitions"
    )
    for k, v in buckets.items():
        node.add(f"{k[0]} --> {k[1]}: {v.idxs.numel()}")


def add_c(c: torch.Tensor | None, tree: Tree):
    """Add the censoring times.

    Args:
        c (torch.Tensor | None): The censoring times.
        tree (Tree): The tree to add to.
    """
    if c is not None:
        tree.add(f"c: {c.size(0)} censoring time(s)")
