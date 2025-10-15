"""
Statistics function
"""

from typing import Union

import pandas as pd
from scipy import stats


def test_kruskal_wallis(
    *groups: pd.DataFrame, variable: str, dataframe: pd.DataFrame, y: str = "y", alpha: float = 0.02, fill_na: int = 0
) -> Union[pd.Series, None]:
    """
    Statistical Kruskal-Wallis test.

    Parameters
    ----------
    groups : packaging argument, pd.DataFrame
        Dataframe with one of the target groups.
    variable : str
        Column name to analyze
    dataframe : pd.DataFrame
        Dataframe with all target groups
    y : str, optional
        Target column name, by default "y"
    alpha : float, optional
        Statistical significance, by default 0.02
    fill_na : int, optional
        Fill empty rows, by default 0

    Returns
    -------
    Union[pd.Series, None]
        If p_value < alpha, returns median values for each group.
        If p_value >= alpha, returns None.
    """
    krus_group = []
    for group in groups:
        group = group[variable].fillna(fill_na).to_list()
        krus_group.append(group)
    h_statistic, p_value = stats.kruskal(*krus_group)

    print("H-statistic value:", h_statistic)
    print("p-value:", p_value)

    if p_value < alpha:
        print(
            "The null hypothesis is rejected, indicating a statistically significant "
            "difference in at least one group pair. See the medians below."
        )
        return dataframe.groupby(y)[variable].median()
    print(
        "There is no basis to reject the null hypothesis—no statistically significant "
        "differences exist between the groups."
    )
    return None


def test_agosto_pearsona(column: str, dataframe: pd.DataFrame, alpha: float = 0.02) -> None:
    """Test for normality using D'Agostino-Pearson test.

    Parameters
    ----------
    column : str
        Column name to test for normality
    dataframe : pd.DataFrame
        Input dataframe containing the column
    alpha : float, optional
        Statistical significance level, by default 0.02
    """

    stat, p_value = stats.normaltest(dataframe[column])

    print(f"D'Agostino-Pearson statistic value: {stat}")
    print(f"p-value: {p_value}")

    alpha = 0.05
    if p_value > alpha:
        print("There is no basis to reject the null hypothesis: the data follow a normal distribution.")
    else:
        print("The null hypothesis is rejected: the data deviate from a normal distribution.")
