"""
Visualization functions and classes for data analysis and clustering.

This module provides various visualization tools including:
- Metrics plotting for clustering evaluation
- Radar plots for cluster characteristics
- Distribution comparison plots
- Feature distribution visualization
- Cluster metrics and characteristics
- Statistical visualization helpers
"""

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import PowerTransformer, QuantileTransformer
from yellowbrick.cluster import KElbowVisualizer


class MetricsPlot:
    """Class to compare clustering metrics for different parameter values.

    Calculates and plots silhouette, calinski-harabasz and davies-bouldin scores
    across a range of parameter values for clustering algorithms.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        start_param: int,
        stop_param: int,
        step_param: int,
        silhouette_scores: list[float] | None = None,
        calinski_harabasz_scores: list[float] | None = None,
        davies_bouldin_scores: list[float] | None = None,
    ):
        """Initialize the metrics plotting class.

        Parameters
        ----------
        data: pd.DataFrame
            Data to plot
        start_param : int
            Start number dynamic parameter
        stop_param : int
            Stop number dynamic parameter
        step_param : int
            Step number dynamic parameter
        silhouette_scores : list (default)
            Default list for metrics
        calinski_harabasz_scores : list (default)
            Default list for metrics
        davies_bouldin_scores : list (default)
            Default list for metrics
        """

        self.silhouette_scores = [] if silhouette_scores is None else silhouette_scores
        self.calinski_harabasz_scores = [] if calinski_harabasz_scores is None else calinski_harabasz_scores
        self.davies_bouldin_scores = [] if davies_bouldin_scores is None else davies_bouldin_scores
        self.start_param = start_param
        self.stop_param = stop_param
        self.step_param = step_param
        self.data = data

    def model(self, name_model: object, params: dict[str, Any]) -> object:
        """Create model instance with given parameters.

        Parameters
        ----------
        name_model : class
            Clustering model class
        params : dict
            Model parameters

        Returns
        -------
        model instance
            Initialized clustering model
        """
        return name_model(**params)  # type: ignore

    def calculate_metrics(
        self,
        name_model: object,
        name_dynamic_param: str,
        name_const_param: Optional[str] = None,
        value_const_param: Optional[int] = None,
    ) -> None:
        """Calculate clustering metrics and add results to list of metrics.

        Parameters
        ----------
        name_model : object
            Clustering model class (not a string, e.g. HDBSCAN not 'HDBSCAN')
        name_dynamic_param : str
            Name of dynamic parameter
        name_const_param : str, optional
            Name of constant parameter
        value_const_param : int, optional
            Value of constant parameter

        WARNING: The following arguments must be specified at once
        name_const_param: str, optional
            Name of constant parameter
        value_const_param: int, optional
            Value of constant parameter
        """

        self.name_dynamic = name_dynamic_param
        for dynamic_param in range(self.start_param, self.stop_param, self.step_param):
            if name_const_param:
                params = {name_dynamic_param: dynamic_param, name_const_param: value_const_param}
            else:
                params = {name_dynamic_param: dynamic_param}

            hdbscan = self.model(name_model, params)
            results = hdbscan.fit_predict(self.data)  # type: ignore
            self.silhouette_scores.append(silhouette_score(self.data, results))
            self.calinski_harabasz_scores.append(calinski_harabasz_score(self.data, results))
            self.davies_bouldin_scores.append(davies_bouldin_score(self.data, results))

    def plot(self) -> None:
        """Plot the calculated metrics."""
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        ax1.plot(range(self.start_param, self.stop_param, self.step_param), self.silhouette_scores, "bx-")
        ax1.set_title("Silhouette Score Method")
        ax1.set_xlabel(f"{self.name_dynamic}")
        ax1.set_ylabel("Silhouette Scores")

        ax2.plot(
            range(self.start_param, self.stop_param, self.step_param),
            self.calinski_harabasz_scores,
            "rx-",
        )
        ax2.set_title("Calinski harabasz Score Method")
        ax2.set_xlabel(f"{self.name_dynamic}")
        ax2.set_ylabel("Calinski harabasz Scores")

        ax3.plot(
            range(self.start_param, self.stop_param, self.step_param),
            self.davies_bouldin_scores,
            "gx-",
        )
        ax3.set_title("Davies bouldin Score Method")
        ax3.set_xlabel(f"{self.name_dynamic}")
        ax3.set_ylabel("Davies bouldi Scores")

        plt.xticks(range(self.start_param, self.stop_param, self.step_param))
        plt.tight_layout()
        plt.show()


class Radar:
    """Class for creating radar/spider plots."""

    def __init__(
        self,
        figure: plt.Figure,
        title: list[str],
        labels: list[str],
        rect: list[float] | None = None,
    ) -> None:
        """Initialize radar plot.

        Parameters
        ----------
        figure : matplotlib.figure.Figure
            Figure to draw on
        title : list
            List of titles for radar axes
        labels : list
            List of labels for data points
        rect : list, optional
            Plot rectangle dimensions [left, bottom, width, height]
        """
        if rect is None:
            rect = [0.05, 0.05, 0.95, 0.95]

        self.n = len(title)
        self.angles = list(np.linspace(0, 2 * np.pi, self.n, endpoint=False))

        self.axes = [figure.add_axes(rect, projection="polar", label=f"axes{i}") for i in range(self.n)]
        self.ax = self.axes[0]
        self.ax.set_thetagrids(np.degrees(self.angles), labels=title, fontsize=10)

        for ax in self.axes[1:]:
            ax.xaxis.set_visible(False)
            ax.set_yticklabels([])
            ax.set_zorder(-99)

        for ax, _ in zip(self.axes, self.angles, strict=True):
            ax.spines["polar"].set_color("black")
            ax.spines["polar"].set_zorder(-99)

    def plot(self, values: np.ndarray, *args: Any, **kw: Any) -> None:
        """Plot data on the radar chart.

        Parameters
        ----------
        values : array-like
            Values to plot
        *args, **kw
            Additional arguments passed to plot
        """
        angle = np.r_[self.angles, self.angles[0]]
        values = np.r_[values, values[0]]
        self.ax.plot(angle, values, *args, **kw)
        kw["label"] = "_noLabel"
        self.ax.fill(angle, values, *args, **kw)


def cluster_characteristics(data: pd.DataFrame) -> None:
    """Plot radar chart showing characteristics of clusters.

    Parameters
    ----------
    data : pd.DataFrame
        Standardized data with 'clusters' column
    """

    cluster_colors = [
        "#C630FC",
        "#b4d2b1",
        "#568f8b",
        "#1d4a60",
        "#cd7e59",
        "#ddb247",
        "#d15252",
        "#3832a8",
        "#4de307",
    ]

    df_result_std_mean = pd.concat(
        [
            pd.DataFrame(data.mean().drop("clusters"), columns=["mean"]),
            data.groupby("clusters").mean().T,
        ],
        axis=1,
    )

    df_result_std_dev_rel = df_result_std_mean.apply(lambda x: round((x - x["mean"]) / x["mean"], 2) * 100, axis=1)
    df_result_std_dev_rel.drop(columns=["mean"], inplace=True)
    df_result_std_mean.drop(columns=["mean"], inplace=True)

    fig = plt.figure(figsize=(15, 15))
    radar = Radar(fig, data.drop("clusters", axis=1).columns, np.unique(data["clusters"]))

    for k in range(data["clusters"].unique().min(), data["clusters"].unique().max() + 1):
        cluster_data = df_result_std_mean[k].values.tolist()
        radar.plot(
            cluster_data,
            "-",
            lw=2,
            color=cluster_colors[k],
            alpha=0.7,
            label="cluster {}".format(k),
        )

    radar.ax.legend()
    radar.ax.set_title("Cluster characteristics: Feature means per cluster", size=22, pad=60)
    plt.show()


def comparison_density(data: pd.DataFrame, column_name: str, random_state: int = 2025) -> None:
    """Compare different density transformations of skewed data.

    Parameters
    ----------
    data : pd.DataFrame
        Input data
    column_name : str
        Column to transform
    random_state : int, optional
        Random state for QuantileTransformer (default: 2025)
    """

    print(f"-----COLUMN:{column_name}-----")

    data = data[column_name]

    transformations = {}

    neglog = data.apply(lambda x: np.sign(x) * np.log(abs(x) + 1))
    transformations["neglog"] = (neglog, abs(neglog.skew()))

    ihs = np.arcsinh(data)
    transformations["ihs"] = (ihs, abs(ihs.skew()))

    yeo_johnson_transformed = PowerTransformer(method="yeo-johnson").fit_transform(data.values.reshape(-1, 1))
    transformations["yeo_johnson"] = (
        yeo_johnson_transformed.flatten(),
        abs(pd.Series(yeo_johnson_transformed.flatten()).skew()),
    )

    quantile_transformed = QuantileTransformer(output_distribution="normal", random_state=random_state).fit_transform(
        data.values.reshape(-1, 1)
    )
    transformations["quantile"] = (
        quantile_transformed.flatten(),
        abs(pd.Series(quantile_transformed.flatten()).skew()),
    )

    sorted_transforms = sorted(transformations.items(), key=lambda x: x[1][1])

    print(f"\nOriginal data skewness: {abs(data.skew())}")

    colors = {"neglog": "blue", "ihs": "green", "yeo_johnson": "red", "quantile": "purple"}

    fig, axes = plt.subplots(1, len(transformations) + 1, figsize=(5 * (len(transformations) + 1), 5))

    sns.kdeplot(data, ax=axes[0], color="black").set(title="Original Skewed Data")

    print("\nAll transformations:")
    for i, (name, (transform, skewness)) in enumerate(sorted_transforms):
        print(f"{name}: {skewness}")
        sns.kdeplot(transform, ax=axes[i + 1], color=colors[name]).set(
            title=f"{name} transformation\nSkewness: {skewness:.4f}"
        )

    plt.tight_layout()
    plt.show()


def elbow_visualisation(data: np.ndarray) -> None:
    """Plot elbow curve for KMeans clustering.

    Parameters
    ----------
    data : np.ndarray
        Data to fit KMeans on
    """
    fig, ax = plt.subplots()

    visualizer = KElbowVisualizer(KMeans(), k=(2, 30), ax=ax)
    visualizer.fit(data)

    ax.set_xticks(range(2, 7))
    visualizer.show()
    plt.show()


def describe_clusters_metrics(data: pd.DataFrame, transpose: bool = False) -> pd.DataFrame:
    """Calculate descriptive statistics for clusters.

    Parameters
    ----------
    data : pd.DataFrame
        Data with 'clusters' column
    transpose : bool, optional
        Whether to transpose output table

    Returns
    -------
    pd.DataFrame
        Styled DataFrame with cluster metrics
    """
    if "id_client" in data.columns:
        data.drop("id_client", axis=1, inplace=True)
    if transpose:
        return (
            data.groupby("clusters")
            .agg(["mean", "median", "std", "min", "max"])
            .T.style.background_gradient(cmap="copper", axis=1)
        )
    return (
        data.groupby("clusters").agg(["mean", "median", "std", "min", "max"]).style.background_gradient(cmap="copper")
    )


def category_null_variables(dataframe: pd.DataFrame, groupby_column: str, count_column: str) -> pd.DataFrame:
    """Calculate null and non-null counts and percentages for a column grouped by another column.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Input dataframe containing the columns to analyze
    groupby_column : str
        Column name to group by
    count_column : str
        Column name to count null/non-null values for

    Returns
    -------
    pd.DataFrame
        DataFrame containing counts and percentages of null/non-null values for each group
    """
    counts = (
        dataframe.groupby(groupby_column)[count_column]
        .agg([lambda x: x.isnull().sum(), lambda x: x.notnull().sum()])
        .reset_index()
    )
    counts.columns = [f"{groupby_column}", "null_count", "not_null_count"]
    counts["null_percentage"] = counts["null_count"] / (counts["null_count"] + counts["not_null_count"]) * 100
    counts["not_null_percentage"] = counts["not_null_count"] / (counts["null_count"] + counts["not_null_count"]) * 100
    return counts


def normal_distr_plots(dataframe: pd.DataFrame, variable: str) -> None:
    """Create histogram, density plot and boxplot for a numeric variable.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Input dataframe containing the variable to plot
    variable : str
        Column name to create plots for
    """
    plt.figure(figsize=(12, 6))
    sns.histplot(data=dataframe, x=variable, bins=50).set(
        title=f"Histogram - {variable!r}", xlabel=variable, ylabel="Number of observations"
    )
    plt.show()

    # Wykres gęstości
    sns.displot(dataframe[variable], kind="kde", height=5, aspect=2.122).set(
        title=f"Density Plot - {variable!r}", xlabel=variable, ylabel=""
    )
    plt.show()

    # Boxplot
    plt.figure(figsize=(12, 6))
    sns.boxplot(dataframe[variable]).set(
        title=f"Boxplot - {variable!r}", xlabel=variable, ylabel="Number of observations"
    )
    plt.show()
    print("-------------------------------------------------------------")


def distplot_limitations(
    dataframe_with_limitation: pd.DataFrame,
    variable: str,
    category: str,
    only_kde: bool = False,
) -> None:
    """Create distribution plot for a variable split by category.

    Parameters
    ----------
    dataframe_with_limitation : pd.DataFrame
        Input dataframe containing the variable and category columns
    variable : str
        Column name to plot distribution for
    category : str
        Column name to split distribution by
    only_kde : bool, optional
        If True, only show kernel density estimate plot, by default False
    """
    if only_kde:
        sns.displot(
            x=dataframe_with_limitation[variable],
            kind="kde",
            hue=dataframe_with_limitation[category],
            height=5,
            aspect=2.122,
        )
    else:
        sns.displot(
            x=dataframe_with_limitation[variable],
            kde=True,
            hue=dataframe_with_limitation[category],
            height=5,
            aspect=2.122,
        )
    plt.title(f"{variable} distribution depends on {category}")
    plt.show()


def boxplot_limitations(dataframe_with_limitation: pd.DataFrame, variable: str, category: str) -> None:
    """Create boxplot for a variable split by category.

    Parameters
    ----------
    dataframe_with_limitation : pd.DataFrame
        Input dataframe containing the variable and category columns
    variable : str
        Column name to create boxplot for
    """
    plt.figure(figsize=(14.4, 6))
    sns.boxplot(x=category, y=variable, data=dataframe_with_limitation)
    plt.title(f"Box {variable} distribution by {category}")
    plt.show()


def violinplot_limitations(
    dataframe_with_limitation: pd.DataFrame,
    category: str,
    variable: str = "y",
    group: Optional[str] = None,
    group_order: Optional[list[str]] = None,
    order: Optional[list[str]] = None,
) -> None:
    """Create violin plot for a variable(category).

    Parameters
    ----------
    dataframe_with_limitation : pd.DataFrame
        Input dataframe containing the categorys to plot
    category : str
        Column name for x-axis
    variable : str, optional
        Column name for y-axis, by default "y"
    group : str, optional
        Column name for color grouping, by default None
    group_order : list[str], optional
        Order for group categories, by default None
    order : list[str], optional
        Order for x-axis categories, by default None
    """
    plt.figure(figsize=(14.4, 6))
    sns.violinplot(
        x=category,
        y=variable,
        data=dataframe_with_limitation,
        hue=group,
        hue_order=group_order,
        order=order,
    )
    plt.title(f"Violin {category} distribution")
    plt.show()


def countplot_limitations(
    dataframe_with_limitation: pd.DataFrame,
    variable: str,
    category: str,
    order: Optional[list[str]] = None,
) -> None:
    """Create count plot for a categorical variable split by category.

    Parameters
    ----------
    dataframe_with_limitation : pd.DataFrame
        Input dataframe containing the variable and category columns
    variable : str
        Column name to count values for
    category : str
        Column name to split distribution by
    order : list[str], optional
        Order for x-axis categories, by default None
    """
    plt.figure(figsize=(14.4, 6))
    sns.countplot(
        x=dataframe_with_limitation[variable],
        hue=dataframe_with_limitation[category],
        order=order,
    )
    plt.title(f"Influence {variable} on {category}")
    plt.xticks(rotation=50)
    plt.show()


def categorical_variable_perc(df: pd.DataFrame, variable: str, category: str) -> pd.DataFrame:
    """Calculate percentage distribution of a categorical variable by category.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing the variable and category columns
    variable : str
        Column name to calculate percentages for
    category : str
        Column name to split distribution by

    Returns
    -------
    pd.DataFrame
        DataFrame containing percentage distributions
    """
    group_counts = df.groupby([category, variable]).size().unstack(fill_value=0)
    perc_group = group_counts.div(group_counts.sum(axis=1), axis=0).round(4) * 100
    return perc_group


def cramers_v(tab: pd.DataFrame) -> float:
    """Calculate Cramer's V statistic for categorical variables.

    Parameters
    ----------
    tab : pd.DataFrame
        Contingency table of categorical variables

    Returns
    -------
    float
        Cramer's V statistic
    """
    a = scipy.stats.chi2_contingency(tab)[0] / sum(tab.sum())
    b = min(
        tab.shape[0] - 1,
        tab.shape[1] - 1,
    )
    return float(np.sqrt(a / b))


def calculate_crammers_v(tab: pd.DataFrame) -> pd.DataFrame:
    """Calculate Cramer's V statistic for all pairs of categorical variables.

    Parameters
    ----------
    tab : pd.DataFrame
        DataFrame containing categorical variables

    Returns
    -------
    pd.DataFrame
        Matrix of Cramer's V statistics for all variable pairs
    """
    ret = []
    for m in tab:
        row = []
        for n in tab:
            cross_tab = pd.crosstab(tab[m].values, tab[n].values)
            row.append(cramers_v(cross_tab))
        ret.append(row)

    crammer = pd.DataFrame(ret, columns=tab.columns, index=tab.columns)

    plt.figure(figsize=(10, 6))
    sns.heatmap(crammer, cmap="Reds", linewidths=0.5).set(title="Cramer's V Dependency Coefficient Heatmap")
    plt.show()
    return crammer


def spearman_correlation(
    df: pd.DataFrame,
    target_variable: str,
    abs: bool = False,
) -> None:
    """Calculate and plot Spearman correlations between variables.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing ONLY numeric variables
    target_variable : str
        Name of target column to calculate correlations against
    abs : bool, optional
        Whether to use absolute correlation values, by default False
    """
    # Validate that all columns are numeric
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
    if len(non_numeric_cols) > 0:
        raise ValueError(f"All columns must be numeric. Found non-numeric columns: {list(non_numeric_cols)}")

    corr_spearman = df.corr(method="spearman")
    if abs:
        corr_with_y = corr_spearman[target_variable].drop(target_variable).abs().sort_values(ascending=False)
    else:
        corr_with_y = corr_spearman[target_variable].drop(target_variable).sort_values(ascending=False)

    plt.figure(figsize=(10, 10))
    sns.barplot(
        x=corr_with_y.values,
        y=corr_with_y.index,
    )

    if abs:
        plt.title(f"Variable Correlation with {target_variable} (Spearman) - Absolute Values")
    else:
        plt.title(f"Variable Correlation with {target_variable} (Spearman) - Sorted")
    plt.xlabel("Correlation Value")
    plt.ylabel("Variable")
    plt.xlim(-1, 1)  # Range from -1 to 1
    plt.axvline(0, color="black", linestyle="--")  # Reference line at zero
    plt.show()
