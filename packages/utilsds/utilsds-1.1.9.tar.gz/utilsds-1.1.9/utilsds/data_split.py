"""
Train test validation split function
"""

# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals

from typing import Any, Dict, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


def train_test_validation_split(
    data: pd.DataFrame,
    col_target: str,
    train_percent: float = 0.7,
    test_percent: float = 0.15,
    validate_percent: float = 0.15,
    random_state: int = 2024,
    col_order: str | None = None,
    task: str = "str",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Splits a Pandas dataframe into three subsets (train, val, and test).
    Function uses train_test_split (from sklearn) and stratify to receive
    the same ratio response (y, target) in each splits for classification tasks.
    Stratification is automatically disabled for continuous targets (regression).
    If col_order is given, split is not shuffled, but divided by col_order order.

    Parameters
    ----------
    data: pd.DataFrame
        Data to split
    col_target: str
        Name of column target
    train_percent: float (0,1)
        Percent of train data
    test_percent: float (0,1)
        Percent of test data
    validate_percent: float (0,1)
        Percent of validate data
    random_state: int
        Random state for reproducibility. Defaults to 2024.
    col_order: str | None
        Column to sort values for train/test/validation split by date.
        If none, standard split is done - data are shuffled.
    task: str
        Type of task - 'reg' for regression, 'bin' for binary classification,
        or 'multi' for multiclass classification. Defaults to "str".

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]
        X_train : Training data features
        X_test : Test data features
        X_val : Validation data features
        y_train : Training data target
        y_test : Test data target
        y_val : Validation data target

    Raises
    ------
    ValueError
        If sum of train_percent, validate_percent and test_percent is not equal to 1.0
        If col_target is not present in the input dataframe

    Notes
    -----
    Sum of train_percent, validate_percent and test_percent must be equal to 1.0.
    """

    if train_percent + validate_percent + test_percent != 1.0:
        raise ValueError("Sum of train, validate and test is not 1.0")
    if col_target not in data.columns:
        raise ValueError(f"{col_target} is not a column in the dataframe")

    if col_order is not None:
        data = data.sort_values(by=col_order, ignore_index=True)
        data = data.drop(col_order, axis=1)
    y = data[[col_target]]
    data = data.drop(col_target, axis=1)

    train_temp_params = {} if task == "reg" or col_order is not None else {"stratify": y}
    X_train, X_temp, y_train, y_temp = train_test_split(
        data, y, test_size=(1.0 - train_percent), random_state=random_state, **train_temp_params
    )

    test_val_params = {} if task == "reg" or col_order is not None else {"stratify": y_temp}
    validate_to_split = validate_percent / (validate_percent + test_percent)
    X_test, X_val, y_test, y_val = train_test_split(
        X_temp, y_temp, test_size=validate_to_split, random_state=random_state, **test_val_params
    )

    assert len(data) == len(X_train) + len(X_test) + len(
        X_val
    ), "Length of X is different than sum of x_train + x_test + x_val"
    assert len(y) == len(y_train) + len(y_test) + len(
        y_val
    ), "Length of y is different than sum of y_train + y_test + y_val"
    assert len(X_train) == len(y_train), "Length of X_train is different than y_train"
    assert len(X_test) == len(y_test), "Length of X_test is different than y_test"
    assert len(X_val) == len(y_val), "Length of X_val is different than y_val"

    return (
        X_train,
        X_test,
        X_val,
        y_train,
        y_test,
        y_val,
    )


def resample_X_y(
    X_train: pd.DataFrame, y_train: pd.Series, sampler_object: Any, params: Dict[str, Any] | None = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """Function for resampling train data and target column.

    Parameters
    ----------
    X_train : pd.DataFrame
        Data with all columns to train model
    y_train : pd.Series
        Target column
    sampler_object : Any
        Object of selected sampler to execute
    params : Dict[str, Any], optional
        Dictionary of params for selected sampler, by default None

    Returns
    -------
    Tuple[pd.DataFrame, pd.Series]
        - X_resampled : Resampled training data
        - y_resampled : Resampled target column
    """
    if params is None:
        params = {}

    if "id_client" in X_train.columns:
        X_train = X_train.drop("id_client", axis=1)
    sampler = sampler_object(**params)
    X_resampled, y_resampled = sampler.fit_resample(X_train, y_train)
    return X_resampled, y_resampled
