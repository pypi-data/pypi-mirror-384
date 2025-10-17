# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Union

from pydantic import BaseModel, ValidationError

MetricType = Union[float, int, list[Union[float, int]]]


class Metric(BaseModel):
    """
    Pydantic model for validating metric values.

    This model ensures that metric values are of the correct type,
    accepting single numeric values or lists of numeric values.

    Attributes
    ----------
    value : MetricType
        The metric value, which can be a float, int, or list of floats/ints.
    """

    value: MetricType


def validate_metric_value(value: Any) -> MetricType:
    """
    Validate and convert a value to a proper metric type.

    Uses Pydantic validation to ensure the input value conforms to
    the MetricType specification (float, int, or list of floats/ints).

    Parameters
    ----------
    value : Any
        The value to validate and convert.

    Returns
    -------
    MetricType
        The validated metric value.

    Raises
    ------
    ValueError
        If the value cannot be converted to a valid metric type.
    """
    try:
        return Metric(value=value).value
    except ValidationError as e:
        raise ValueError("Invalid metric value. Must be a list of floats or ints or a float or an int.") from e


def set_metrics(
    metrics: dict[str, MetricType],
    key: str,
    value: Any,
    overwrite: bool,
    single_value: bool,
) -> dict[str, MetricType]:
    """
    Set or update a metric value in the metrics dictionary.

    This function routes to appropriate handling based on the value type
    and the single_value flag. It can handle single values, lists, and
    appending to existing metrics.

    Parameters
    ----------
    metrics : dict[str, MetricType]
        The metrics dictionary to update.
    key : str
        The metric key to set or update.
    value : Any
        The value to set for the metric.
    overwrite : bool
        Whether to overwrite existing metrics.
    single_value : bool
        Whether to treat the value as a single metric rather than
        appending to a list.

    Returns
    -------
    dict[str, MetricType]
        The updated metrics dictionary.
    """
    if isinstance(value, list):
        return handle_metric_list(metrics, key, value, overwrite)
    elif single_value:
        return handle_metric_single(metrics, key, value, overwrite)
    return handle_metric_list_append(metrics, key, value, overwrite)


def handle_metric_single(
    metrics: dict[str, MetricType],
    key: str,
    value: float | int,
    overwrite: bool,
) -> dict:
    """
    Handle setting a single metric value.

    Sets or overwrites a metric with a single numeric value. If the key
    already exists and overwrite is False, the existing value is preserved.

    Parameters
    ----------
    metrics : dict[str, MetricType]
        The metrics dictionary to update.
    key : str
        The metric key to set.
    value : float | int
        The single numeric value to set.
    overwrite : bool
        Whether to overwrite an existing metric with the same key.

    Returns
    -------
    dict
        The updated metrics dictionary.
    """
    if key not in metrics or overwrite:
        metrics[key] = value
    return metrics


def handle_metric_list_append(
    metrics: dict[str, MetricType],
    key: str,
    value: float | int,
    overwrite: bool,
) -> dict:
    """
    Handle appending a single value to a metric list.

    If the metric doesn't exist or overwrite is True, creates a new list
    with the single value. If the metric exists as a list, appends to it.
    If the metric exists as a single value, converts it to a list and appends.

    Parameters
    ----------
    metrics : dict[str, MetricType]
        The metrics dictionary to update.
    key : str
        The metric key to append to.
    value : float | int
        The numeric value to append.
    overwrite : bool
        Whether to overwrite an existing metric instead of appending.

    Returns
    -------
    dict
        The updated metrics dictionary.
    """
    if key not in metrics or overwrite:
        metrics[key] = [value]
    elif isinstance(metrics[key], list):
        metrics[key].append(value)
    else:
        metrics[key] = [metrics[key], value]
    return metrics


def handle_metric_list(
    metrics: dict[str, MetricType],
    key: str,
    value: list[int | float],
    overwrite: bool,
) -> dict:
    """
    Handle setting or extending a metric with a list of values.

    If the metric doesn't exist or overwrite is True, sets the metric to
    the provided list. If the metric exists and overwrite is False, extends
    the existing list with the new values.

    Parameters
    ----------
    metrics : dict[str, MetricType]
        The metrics dictionary to update.
    key : str
        The metric key to set or extend.
    value : list[int | float]
        The list of numeric values to set or extend with.
    overwrite : bool
        Whether to overwrite an existing metric instead of extending it.

    Returns
    -------
    dict
        The updated metrics dictionary.
    """
    if key not in metrics or overwrite:
        metrics[key] = value
    else:
        metrics[key].extend(value)
    return metrics
