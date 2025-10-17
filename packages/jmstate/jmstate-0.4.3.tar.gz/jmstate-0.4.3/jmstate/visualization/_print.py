from __future__ import annotations

from bisect import bisect_left
from collections.abc import Callable
from typing import TYPE_CHECKING, Final, cast

import torch
from numpy import array2string
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from torch.distributions import Normal

from ..typedefs._defs import Any, Trajectory
from ..utils._surv import build_buckets

if TYPE_CHECKING:
    from ..model._base import MultiStateJointModel
    from ..typedefs._data import ModelData, ModelDesign, SampleData
    from ..typedefs._params import ModelParams

# Constants
SIGNIFICANCE_LVLS: Final[tuple[float, ...]] = (
    0.001,
    0.01,
    0.05,
    0.1,
    float("inf"),
)
SIGNIFICANCE_CODES: Final[tuple[str, ...]] = (
    "[red3]***[/]",
    "[orange3]**[/]",
    "[yellow3]*[/]",
    ".",
    "",
)


# Utils
def _rich_str(obj: Any) -> str:
    """Get the rich string representation of an object.

    Args:
        obj (Any): The object to get the string representation of.

    Returns:
        str: The string representation.
    """
    console = Console()
    return console._render_buffer(console.render(obj))[:-1]  # type: ignore


# Descriptors
def _add_x(x: torch.Tensor | None, tree: Tree):
    """Add the fixed covariates to the tree.

    Args:
        x (torch.Tensor | None): The fixed covariates.
        tree (Tree): The tree to add to.
    """
    if x is not None:
        tree.add(f"x: {x.size(0)} individual(s) with {x.size(1)} covariate(s)")


def _add_t(t: torch.Tensor, tree: Tree):
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


def _add_y(y: torch.Tensor, tree: Tree):
    """Add the measurements.

    Args:
        y (torch.Tensor): The measurements.
        tree (Tree): The tree to add to.
    """
    tree.add(
        f"y: {y.size(0)} individual(s) x {y.size(1)} measurement(s) x {y.size(2)} "
        "dimension(s)"
    )


def _add_psi(psi: torch.Tensor, tree: Tree):
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


def _add_trajectories(trajectories: list[Trajectory], tree: Tree):
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


def _add_c(c: torch.Tensor | None, tree: Tree):
    """Add the censoring times.

    Args:
        c (torch.Tensor | None): The censoring times.
        tree (Tree): The tree to add to.
    """
    if c is not None:
        tree.add(f"c: {c.size(0)} censoring time(s)")


# Printers
def model_design_str(model_design: ModelDesign) -> str:
    """String of the model design.

    Args:
        model_design (ModelDesign): The model design.

    Returns:
        str: The string representation.
    """

    def _fn_str(fn: Callable[..., Any]) -> str:
        return getattr(fn, "__name__", str(fn))

    tree = Tree("ModelDesign")
    tree.add(f"individual_effects_fn: {_fn_str(model_design.individual_effects_fn)}")
    tree.add(f"regression_fn: {_fn_str(model_design.regression_fn)}")
    surv = tree.add("surv: survival base hazard and link functions")
    for k, v in model_design.surv.items():
        surv.add(f"{k[0]} --> {k[1]}: ({_fn_str(v[0])}, {_fn_str(v[1])})")

    return _rich_str(tree)


def model_data_str(model_data: ModelData) -> str:
    """String of the model data.

    Args:
        model_data (ModelData): The model data.

    Returns:
        str: The string representation.
    """
    tree = Tree("ModelData")
    _add_x(model_data.x, tree)
    _add_t(model_data.t, tree)
    _add_y(model_data.y, tree)
    _add_trajectories(model_data.trajectories, tree)
    _add_c(model_data.c, tree)

    return _rich_str(tree)


def sample_data_str(sample_data: SampleData) -> str:
    """String of the sample data.

    Args:
        sample_data (SampleData): The sample data.

    Returns:
        str: The string representation.
    """
    tree = Tree("SampleData")
    _add_x(sample_data.x, tree)
    _add_trajectories(sample_data.trajectories, tree)
    _add_psi(sample_data.psi, tree)
    _add_c(sample_data.c, tree)

    return _rich_str(tree)


def model_params_str(model_params: ModelParams) -> str:
    """String of the model parameters.

    Args:
        model_params (ModelParams): The model parameters.

    Returns:
        str: The string representation.
    """

    def _to_str(t: torch.Tensor) -> str:
        return array2string(t.numpy(), precision=3, suppress_small=True)

    def _indent(t: str) -> str:
        return t.replace("\n", "\n  ")

    tree = Tree("ModelParams")
    if model_params.gamma is not None:
        tree.add(f"gamma: {_to_str(model_params.gamma)} population parameter(s)")
    tree.add(f"Q: {_indent(_to_str(model_params.get_cov('Q')))} prior cov matrix")
    tree.add(f"R: {_indent(_to_str(model_params.get_cov('R')))} residual cov matrix")
    alphas = tree.add("alphas: link linear parameter(s)")
    for k, v in model_params.alphas.items():
        alphas.add(f"{k[0]} --> {k[1]}: {_to_str(v)}")
    if model_params.betas is not None:
        betas = tree.add("betas: covariate(s) linear parameter(s)")
        for k, v in model_params.betas.items():
            betas.add(f"{k[0]} --> {k[1]}: {_to_str(v)}")

    return _rich_str(tree)


def model_str(model: MultiStateJointModel) -> str:
    """String of the model.

    Args:
        model (MultiStateJointModel): The model.

    Returns:
        str: The string representation.
    """

    def _fn_str(fn: Callable[..., Any] | None) -> str:
        return getattr(fn, "__name__", str(fn))

    pen_line = f"pen: {'no penalty' if model.pen is None else _fn_str(model.pen)}"
    cache_limit_line = (
        f"cache_limit: {'inf' if model.cache_limit is None else model.cache_limit}"
    )
    data_line = "data: train data not seen" if model.data is None else str(model.data)
    metrics_line = (
        f"metrics_: metrics with {list(vars(model.metrics_).keys()) or 'no attributes'}"
    )
    fit_line = f"fit_: model {'fitted' if model.fit_ else 'not fitted'}"

    tree = Tree("MultiStateJointModel")
    tree.add(str(model.model_design))
    tree.add(str(model.params_))
    tree.add(pen_line)
    tree.add(f"n_quad: {model.n_quad} points for Gauss-Legendre quadrature")
    tree.add(f"n_bisect: {model.n_bisect} bisection steps")
    tree.add(cache_limit_line)
    tree.add(data_line)
    tree.add(metrics_line)
    tree.add(fit_line)

    return _rich_str(tree)


def summary(model: MultiStateJointModel, fmt: str = ".3f"):
    """Prints the p-values of the parameters as well as values and standard error.

    Also prints the log likelihood, AIC, BIC.

    Args:
        model (MultiStateJointModel): The fitted model.
        fmt (str, optional): The format of the p-values. Defaults to ".3f".
    """
    named_params_list = model.params_.as_named_list
    values = model.params_.as_flat_tensor
    stderrors = model.stderror.as_flat_tensor
    zvalues = torch.abs(values / stderrors)
    pvalues = cast(torch.Tensor, 2 * (1 - Normal(0, 1).cdf(zvalues)))

    table = Table()
    table.add_column("Parameter name", justify="left")
    table.add_column("Value", justify="center")
    table.add_column("Standard Error", justify="center")
    table.add_column("z-value", justify="center")
    table.add_column("p-value", justify="center")
    table.add_column("Significance level", justify="center")

    i = 0
    for name, value in named_params_list:
        for j in range(1, value.numel() + 1):
            code = SIGNIFICANCE_CODES[bisect_left(SIGNIFICANCE_LVLS, pvalues[i].item())]

            table.add_row(
                f"{name}[{j}]" if value.numel() > 1 else name,
                f"{values[i]:{fmt}}",
                f"{stderrors[i]:{fmt}}",
                f"{zvalues[i]:{fmt}}",
                f"{pvalues[i]:{fmt}}",
                code,
            )
            i += 1

    criteria = Text(
        f"Log-likelihood: {model.loglik:{fmt}}\n"
        f"AIC: {model.aic:{fmt}}\n"
        f"BIC: {model.bic:{fmt}}",
        style="bold cyan",
    )

    content = Group(table, Rule(style="dim"), criteria, Rule(style="dim"))
    panel = Panel(content, title="Model Summary", border_style="green", expand=False)

    Console().print(panel)
