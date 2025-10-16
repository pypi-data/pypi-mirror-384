from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import torch

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
def describe_x(x: torch.Tensor | None) -> str:
    """Describe the fixed covariates.

    Args:
        x (torch.Tensor | None): The fixed covariates.

    Returns:
        str: The description.
    """
    if x is None:
        return "x: No covariates"
    return f"x: {x.size(0)} individual(s) with {x.size(1)} covariate(s)"


def describe_t(t: torch.Tensor) -> str:
    """Describe the measurement times.

    Args:
        t (torch.Tensor): The measurement times.

    Returns:
        str: The description.
    """
    if t.ndim == 1:
        return f"t: shared measurement times of length {t.size(0)} measurement(s)"
    return (
        f"t: individual measurement times {t.size(0)} individual(s) x {t.size(1)} "
        "measurement(s)"
    )


def describe_y(y: torch.Tensor) -> str:
    """Describe the measurements.

    Args:
        y (torch.Tensor): The measurements.

    Returns:
        str: The description.
    """
    return (
        f"y: {y.size(0)} individual(s) x {y.size(1)} measurement(s) x {y.size(2)} "
        "dimension(s)"
    )


def describe_psi(psi: torch.Tensor) -> str:
    """Describe the individual parameters.

    Args:
        psi (torch.Tensor): The individual parameters.

    Returns:
        str: The description.
    """
    if psi.ndim == 2:  # noqa: PLR2004
        return (
            f"psi: {psi.size(0)} individual(s) x {psi.size(1)} individual parameter(s)"
        )
    return (
        f"psi: {psi.size(0)} sample(s) x {psi.size(1)} individual(s) x {psi.size(2)} "
        "individual parameter(s)"
    )


def describe_trajectories(trajectories: list[Trajectory]) -> str:
    """Describe the trajectories.

    Args:
        trajectories (list[Trajectory]): The trajectories.

    Returns:
        str: The description.
    """
    buckets = build_buckets(trajectories)
    observed_transitions = ", ".join(
        f"{k[0]} --> {k[1]}: {v.idxs.numel()}" for k, v in buckets.items()
    )

    return (
        f"trajectories: {len(trajectories)} individual(s) with observed transitions "
        f"{observed_transitions or '(no transition)'}"
    )


def describe_c(c: torch.Tensor | None) -> str:
    """Describe the censoring times.

    Args:
        c (torch.Tensor | None): The censoring times.

    Returns:
        str: The description.
    """
    if c is None:
        return "c: No censoring"
    return f"c: {c.size(0)} censoring time(s)"
