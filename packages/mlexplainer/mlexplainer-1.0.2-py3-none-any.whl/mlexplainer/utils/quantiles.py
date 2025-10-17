"""Utility functions for quantile calculations in ML Explainer."""

from typing import Optional, Union


from pandas import DataFrame, Series, isna, notna, qcut, merge
from numpy import arange, inf, isclose, nan


def is_in_quantile(
    value: int, quantile_values: list[Union[int, float]]
) -> Union[int, float]:
    """Return the quantile of a value, given a list of quantiles.

    Args:
        value (int): Search value.
        quantile_values (list[Union[int, float]]): List of quantiles.

    Returns:
        Union[int, float]: Upper bound of the quantile.
    """
    if isna(value):
        return -1

    for quantile in quantile_values:
        if value <= quantile:
            return quantile

    # return the last quantile if value exceeds all
    return inf


def nb_min_quantiles(x: DataFrame, q: Optional[int] = None) -> int:
    """Calculate the number of quantiles to use for a feature.

    Args:
        x (DataFrame): DataFrame to calculate the number of quantiles for.
        q (int, optional): Number of quantiles.
            Defaults to None.

    Returns:
        int: Final number of quantiles to use.
    """
    if q is None:
        nb_quantile = 20  # min 5% of observations in each quantile
        min_size = 0  # min size after cutting

        while min_size < 0.01:
            cutting = qcut(x, nb_quantile, duplicates="drop").value_counts(
                dropna=False, normalize=True
            )

            # using only not NaN cut: cannot cut according to these type of observations
            not_nan = [u for u in cutting.index if notna(u)]
            min_size = cutting[not_nan].min()

            # using a smaller value of quantile to respect constraint
            nb_quantile -= 1
    else:
        nb_quantile = q

    # correction for NaN value: if it is relevant to consider it as a class or not
    pct_nan = x.isna().mean()
    nb_quantile = min(int(nb_quantile * (1 - pct_nan)) + 1, nb_quantile)

    return nb_quantile


def group_values(
    x: Series, y: Series, q: Optional[int], threshold_nb_values: float = 15
) -> tuple[DataFrame, int]:
    """Create a new DataFrame of cut values.
    This function groups the values of a feature into quantiles and computes
    the mean of the target variable for each group. It also counts the number
    of observations in each group.

    Args:
        x (Series): Feature values.
        y (Series): Target values.
        q (int): Number of quantiles.

    Returns:
        DataFrame: Grouped values with statistics.
        int: Used quantiles.
    """
    # Check if the series is full of missing values
    if x.isna().all():
        results = DataFrame(
            {"group": [nan], "target": [y.mean()], "volume": [len(x)]}
        )
        return results, 1

    df = DataFrame({"value": x, "target": y})

    if q is None:
        df["group"] = df["value"]
    elif x.nunique() <= threshold_nb_values:
        df["group"] = df["value"]
    else:
        q = nb_min_quantiles(x, q)
        quantiles = arange(1 / q, 1, 1 / q)
        quantiles = quantiles[~isclose(quantiles, 1)].flatten()
        quantiles_values = list(df["value"].quantile(quantiles)) + [inf]

        df["group"] = df["value"].apply(
            lambda u: is_in_quantile(u, quantiles_values)
        )

    # handle missing value
    replaced_nan_value = df["group"].min() - 10
    df.loc[df["value"].isna(), "group"] = replaced_nan_value

    # compute statistics
    stats_groupby = df.groupby("group").mean().sort_index().reset_index()
    volume = (
        df["group"]
        .value_counts()
        .to_frame()
        .sort_index()
        .reset_index()
        .sort_index()
    )
    results = merge(volume, stats_groupby, how="left", on="group")

    # if there is at least one missing value in the dataset
    if df["value"].isna().any():
        results["group"] = results["group"].replace(
            results["group"].min(), nan
        )

    return results.sort_index(), q
