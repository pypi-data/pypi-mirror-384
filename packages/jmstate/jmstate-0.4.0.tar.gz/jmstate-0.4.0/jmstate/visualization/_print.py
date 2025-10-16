from bisect import bisect_left
from typing import Final, cast

from prettytable import PrettyTable
from scipy import stats  # type: ignore

from ..model._base import MultiStateJointModel

# Constants
SIGNIFICANCE_LEVELS: Final[dict[float, str]] = {
    0.001: "***",
    0.01: "**",
    0.05: "*",
    0.1: ".",
    float("inf"): "",
}


def print_pvalues(model: MultiStateJointModel, format: str = ".3f"):
    """Print the p-values of the parameters as well as values and standard error.

    Args:
        model (MultiStateJointModel): The fitted model.
        format (str, optional): The format of the p-values. Defaults to ".3f".

    Raises:
        ValueError: If the model has not been fitted or the FIM not computed.
    """
    if not (model.fit_ and hasattr(model.metrics_, "fim")):
        raise ValueError(
            "Mode must be fitted and Fisher Information Matrix be computed"
        )

    named_params_list = model.params_.as_named_list
    stderror_list = model.stderror.as_list

    table = PrettyTable()
    table.field_names = [
        "Parameter name",
        "Value",
        "Standard Error",
        "z-value",
        "p-value",
        "Significance level",
    ]

    for (name, value), stderror in zip(named_params_list, stderror_list, strict=True):
        for i in range(value.numel()):
            v, s = value.reshape(-1)[i].item(), stderror.reshape(-1)[i].item()
            z = abs(v / s) if s > 0 else float("inf")
            p = 2 * (1 - cast(float, stats.norm.cdf(z)))  # type: ignore
            significance = tuple(SIGNIFICANCE_LEVELS.values())[
                bisect_left(tuple(SIGNIFICANCE_LEVELS.keys()), p)
            ]

            table.add_row(
                [
                    f"{name}[{i + 1}]" if value.numel() > 1 else name,
                    f"{v:{format}}",
                    f"{s:{format}}",
                    f"{z:{format}}",
                    f"{p:{format}}",
                    significance,
                ]
            )

    print(table)  # noqa: T201
