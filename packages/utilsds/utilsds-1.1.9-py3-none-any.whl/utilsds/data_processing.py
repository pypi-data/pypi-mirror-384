"""
Data processing classes compatible with scikit-learn pipelines
"""

from typing import Any, Dict, List, Optional, TypeVar

import duckdb
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.preprocessing import PowerTransformer, QuantileTransformer


T = TypeVar("T", bound="BaseEstimator")
DataFrame = pd.DataFrame


class SkewnessTransformer(BaseEstimator, TransformerMixin):  # type: ignore
    """
    A transformer for handling skewed data with various transformation methods.
    Compatible with scikit-learn pipelines.

    Parameters
    ----------
    ihs : list, optional
        Columns for inverse hyperbolic sine transformation
    neglog : list, optional
        Columns for logarithmic transformation with negative values handling
    yeo_johnson : list, optional
        Columns for Yeo-Johnson transformation
    quantile : list, optional
        Columns for quantile transformation
    parameters : dict, optional
        Dictionary containing parameters for transformations by column
    random_state : int, optional
        Random state for QuantileTransformer (default: 2025)
    """

    def __init__(
        self,
        ihs: Optional[List[str]] = None,
        neglog: Optional[List[str]] = None,
        yeo_johnson: Optional[List[str]] = None,
        quantile: Optional[List[str]] = None,
        random_state: int = 2025,
    ) -> None:
        self.ihs = ihs or []
        self.neglog = neglog or []
        self.yeo_johnson = yeo_johnson or []
        self.quantile = quantile or []
        self.random_state = random_state
        self.yj_transformers_: Dict[str, Any] = {}
        self.qt_transformers_: Dict[str, Any] = {}

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "SkewnessTransformer":
        """
        Fit the transformer to the data.
        For Yeo-Johnson and Quantile transformations, this stores the fitted transformers.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        for column in self.yeo_johnson:
            if column in X.columns:
                transformer = PowerTransformer(method="yeo-johnson")
                transformer.fit(X[[column]])
                self.yj_transformers_[column] = transformer

        for column in self.quantile:
            if column in X.columns:
                transformer = QuantileTransformer(output_distribution="normal", random_state=self.random_state)
                transformer.fit(X[[column]])
                self.qt_transformers_[column] = transformer

        return self

    def transform(self, X: pd.DataFrame, y: Optional[Any] = None) -> pd.DataFrame:
        """
        Apply the transformations to the input data.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        pd.DataFrame
            Transformed data
        """
        X_transformed = X.copy()

        self._apply_ihs_transformations(X_transformed)
        self._apply_neglog_transformations(X_transformed)
        self._apply_yeo_johnson_transformations(X_transformed)
        self._apply_quantile_transformations(X_transformed)

        return X_transformed

    def _apply_ihs_transformations(self, data: pd.DataFrame) -> None:
        """Apply ihs transformation to all ihs columns"""
        for column in self.ihs:
            if column in data.columns:
                self._ihs_transformation(data, column)

    def _apply_neglog_transformations(self, data: pd.DataFrame) -> None:
        """Apply neglog transformation to all neglog columns"""
        for column in self.neglog:
            if column in data.columns:
                self._neglog_transformation(data, column)

    def _apply_yeo_johnson_transformations(self, data: pd.DataFrame) -> None:
        """Apply Yeo-Johnson transformation using fitted transformers"""
        for column in self.yeo_johnson:
            if column in data.columns and column in self.yj_transformers_:
                data[column] = self.yj_transformers_[column].transform(data[[column]])

    def _apply_quantile_transformations(self, data: pd.DataFrame) -> None:
        """Apply Quantile transformation using fitted transformers"""
        for column in self.quantile:
            if column in data.columns and column in self.qt_transformers_:
                data[column] = self.qt_transformers_[column].transform(data[[column]])

    def _ihs_transformation(self, data: pd.DataFrame, column: str) -> None:
        """Inverse hyperbolic sine transformation"""
        data[column] = np.arcsinh(data[column])

    def _neglog_transformation(self, data: pd.DataFrame, column: str) -> None:
        """Neglog transformation"""
        data[column] = data[column].apply(lambda x: np.sign(x) * np.log(abs(x) + 1))


class NullReplacer(BaseEstimator, TransformerMixin):  # type: ignore
    """
    Replace null values in specified columns with a given value.

    Parameters
    ----------
    columns : list
        List of columns to transform
    value : float, str, or dict
        Value to replace nulls with. If a dict, it should map column names to
        replacement values.
    strategy : str, optional
        Strategy to use when value is None. Options: 'mean', 'median', 'mode'.
        Default is None (use provided value).
    """

    def __init__(self, columns: List[str], value: Any = None, strategy: Optional[str] = None):
        self.columns = columns
        self.value = value
        self.strategy = strategy
        self._column_values: Dict[str, Any] = {}

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "NullReplacer":
        """
        Learn values to replace nulls with if strategy is specified.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        if self.strategy is not None:
            for column in self.columns:
                if column in X.columns:
                    if self.strategy == "mean":
                        self._column_values[column] = X[column].mean()
                    elif self.strategy == "median":
                        self._column_values[column] = X[column].median()
                    elif self.strategy == "mode":
                        self._column_values[column] = X[column].mode()[0]
                    else:
                        raise ValueError(f"Unknown strategy: {self.strategy}")
        return self

    def transform(self, X: pd.DataFrame, y: Optional[Any] = None) -> pd.DataFrame:
        """
        Replace null values in the input data.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility
        Returns
        -------
        pd.DataFrame
            Data with nulls replaced
        """
        X_transformed = X.copy()

        for column in self.columns:
            if column in X_transformed.columns:

                if isinstance(self.value, dict) and column in self.value:
                    fill_value = self.value[column]
                elif self.strategy is not None and column in self._column_values:
                    fill_value = self._column_values[column]
                else:
                    fill_value = self.value

                X_transformed[column] = X_transformed[column].fillna(fill_value)

        return X_transformed


class ColumnDropper(BaseEstimator, TransformerMixin):  # type: ignore
    """
    Drop specified columns from the DataFrame.

    Parameters
    ----------
    columns : list
        List of columns to drop
    """

    def __init__(self, columns: List[str]):
        self.columns = columns

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "ColumnDropper":
        """
        No-op, present for API compatibility.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        return self

    def transform(self, X: pd.DataFrame, y: Optional[Any] = None) -> pd.DataFrame:
        """
        Drop specified columns from the input data.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        pd.DataFrame
            Data with columns dropped
        """
        X_transformed = X.copy()

        columns_to_drop = [col for col in self.columns if col in X_transformed.columns]

        return X_transformed.drop(columns=columns_to_drop, axis=1)


class OutliersCleaner(BaseEstimator, TransformerMixin):  # type: ignore
    """
    Clean outliers by clipping values outside specified percentile ranges or fixed values.

    Parameters
    ----------
    columns : list
        List of columns to transform
    upper_threshold : float
        Upper threshold - percentile (e.g., 0.95) or fixed value depending on use_percentiles
    lower_threshold : float, optional
        Lower threshold - percentile (e.g., 0.05) or fixed value depending on use_percentiles
    use_percentiles : bool, default True
        If True, treat thresholds as percentiles to calculate from data
        If False, treat them as fixed clipping values
    """

    def __init__(
        self,
        columns: List[str],
        upper_threshold: float,
        lower_threshold: Optional[float] = None,
        use_percentiles: bool = True,
    ):
        self.columns = columns
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.use_percentiles = use_percentiles
        self.outliers_values: Dict[str, Dict[str, float]] = {}

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "OutliersCleaner":
        """
        Learn percentile thresholds from the data (only if use_percentiles=True).
        """
        if self.use_percentiles:
            for column in self.columns:
                if column in X.columns:
                    upper_value = X[column].quantile(self.upper_threshold)

                    if self.lower_threshold is not None:
                        lower_value = X[column].quantile(self.lower_threshold)
                        self.outliers_values[column] = {"lower": lower_value, "upper": upper_value}
                    else:
                        self.outliers_values[column] = {"upper": upper_value}

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply clipping to the data."""
        X_transformed = X.copy()

        for column in self.columns:
            if column in X_transformed.columns:
                if self.use_percentiles:
                    if column in self.outliers_values:
                        values = self.outliers_values[column]
                        if "upper" in values:
                            X_transformed[column] = X_transformed[column].clip(upper=values["upper"])
                        if "lower" in values:
                            X_transformed[column] = X_transformed[column].clip(lower=values["lower"])
                else:
                    X_transformed[column] = X_transformed[column].clip(upper=self.upper_threshold)
                    if self.lower_threshold is not None:
                        X_transformed[column] = X_transformed[column].clip(lower=self.lower_threshold)

        return X_transformed


class CategoricalMapper(BaseEstimator, TransformerMixin):  # type: ignore
    """
    Map values in a categorical column according to a specified mapping scheme.

    Parameters
    ----------
    column_to_categorize : str
        Name of the column to transform
    map_scheme : dict
        Dictionary mapping original values to new values
    fill_na : any, optional
        Value to use for filling NAs after mapping
    """

    def __init__(self, column_to_categorize: str, map_scheme: Dict[Any, Any], fill_na: Any = None):
        self.column_to_categorize = column_to_categorize
        self.map_scheme = map_scheme
        self.fill_na = fill_na

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "CategoricalMapper":
        """
        No-op, present for API compatibility.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        return self

    def transform(self, X: pd.DataFrame, y: Optional[Any] = None) -> pd.DataFrame:
        """
        Apply mapping to the specified column in the input data.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        pd.DataFrame
            Data with mapping applied
        """
        X_transformed = X.copy()

        if self.column_to_categorize in X_transformed.columns:
            X_transformed[self.column_to_categorize] = X_transformed[self.column_to_categorize].map(self.map_scheme)

            if self.fill_na is not None:
                X_transformed[self.column_to_categorize] = X_transformed[self.column_to_categorize].fillna(self.fill_na)

        return X_transformed


class NumericalMapper(BaseEstimator, TransformerMixin):  # type: ignore
    """
    Convert numerical column to categorical by binning.

    Parameters
    ----------
    column : str
        Name of the column to transform
    bins : list
        List of bin edges for creating intervals
    labels : list, optional
        Custom labels for the bins. If None, generates interval labels with
        'below_' prefix for first bin and 'above_' prefix for last bin

    """

    def __init__(self, column: str, bins: List[float], labels: Optional[List[str]] = None):
        self.column = column
        self.bins = bins
        self.labels = labels
        self._generated_labels: Optional[List[str]] = None
        self._complete_bins: List[float] = []

    def _create_labels(self) -> List[str]:
        """
        Create bin labels in the format:
        ['below_X', 'X_Y', 'Y_Z', ..., 'above_Z']

        Returns
        -------
        List[str]
            List of bin labels
        """
        labels = []

        labels.append(f"below_{self.bins[0]}")

        for i in range(len(self.bins) - 1):
            labels.append(f"{self.bins[i]}_{self.bins[i + 1]}")

        labels.append(f"above_{self.bins[-1]}")

        return labels

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "NumericalMapper":
        """
        Prepare labels for binning.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        if self.column in X.columns:
            self._complete_bins = [-float("inf")] + self.bins + [float("inf")]

            if self.labels is None:
                self._generated_labels = self._create_labels()

            if self.labels is not None and len(self._complete_bins) - 1 != len(self.labels):
                raise ValueError(
                    f"Number of bins ({len(self._complete_bins) - 1}) does not match "
                    f"number of custom labels ({len(self.labels)})"
                )

            if self.labels is None and len(self._complete_bins) - 1 != len(self._generated_labels or []):
                raise ValueError(
                    f"Number of bins ({len(self._complete_bins) - 1}) does not match "
                    f"number of generated labels ({len(self._generated_labels or [])})"
                )

        return self

    def transform(self, X: pd.DataFrame, y: Optional[Any] = None) -> pd.DataFrame:
        """
        Bin numerical column into categories.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        pd.DataFrame
            Data with numerical column converted to categorical
        """
        X_transformed = X.copy()

        if self.column in X_transformed.columns:
            labels_to_use = self.labels if self.labels is not None else self._generated_labels

            if labels_to_use:
                X_transformed[self.column] = pd.cut(
                    X_transformed[self.column],
                    bins=self._complete_bins,
                    labels=labels_to_use,
                    right=False,
                    include_lowest=True,
                )

        return X_transformed


class Encoder(BaseEstimator, TransformerMixin):  # type: ignore
    """
    One-hot encode categorical columns in the data.

    Parameters
    ----------
    columns : list
        Column(s) to encode
    encoder : object, optional
        Encoder object with fit and transform methods (e.g., OneHotEncoder).
    drop_original : bool, optional
        Whether to drop the original column(s) after encoding
    """

    def __init__(self, columns: List[str], encoder: Optional[Any] = None, drop_original: bool = True):
        self.columns = columns
        self.encoder = encoder
        self.drop_original = drop_original
        self.encoders_: Dict[str, Any] = {}

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "Encoder":
        """
        Fit the encoder for each column.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        for column in self.columns:
            if column in X.columns:
                encoder = clone(self.encoder)
                encoder.fit(X[[column]])
                self.encoders_[column] = encoder

        return self

    def transform(self, X: pd.DataFrame, y: Optional[Any] = None) -> pd.DataFrame:
        """
        One-hot encode categorical columns using the provided encoder.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        pd.DataFrame
            Data with categorical columns one-hot encoded
        """
        X_transformed = X.copy()

        for column in self.columns:
            if column in X_transformed.columns and column in self.encoders_:
                encoder = self.encoders_[column]

                encoded_data = encoder.transform(X_transformed[[column]]).toarray()
                encoded_columns = encoder.get_feature_names_out([column])

                encoded_df = pd.DataFrame(encoded_data, columns=encoded_columns, index=X_transformed.index)

                X_transformed = pd.concat([X_transformed, encoded_df], axis=1)

                if self.drop_original:
                    X_transformed = X_transformed.drop(column, axis=1)

        return X_transformed


class Normalizer(BaseEstimator, TransformerMixin):  # type: ignore
    """
    Normalize numerical columns using a provided scaler.

    Parameters
    ----------
    scaler : object
        Scaler object with fit and transform methods (e.g., StandardScaler).
    columns : list
        If provided, only these columns will be scaled (overrides exclude_columns)
    copy : bool, optional
        Whether to create a copy of the data or modify in-place
    """

    def __init__(
        self,
        scaler: Any,
        columns: List[str],
        copy: bool = True,
    ):
        self.scaler = scaler
        self.columns = columns
        self.copy = copy
        self.columns_to_scale_: List[str] = []

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "Normalizer":
        """
        Learn scaling parameters and identify columns to scale.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        self.columns_to_scale_ = [col for col in self.columns if col in X.columns]

        if self.columns_to_scale_:
            self.scaler.fit(X[self.columns_to_scale_])

        return self

    def transform(self, X: pd.DataFrame, y: Optional[Any] = None) -> pd.DataFrame:
        """
        Scale numerical columns.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        pd.DataFrame
            Data with numerical columns scaled
        """
        if not self.columns_to_scale_:
            return X

        X_transformed = X.copy() if self.copy else X

        X_transformed[self.columns_to_scale_] = self.scaler.transform(X_transformed[self.columns_to_scale_])

        return X_transformed


class DuckDBColumnSQLTransformer(BaseEstimator, TransformerMixin):  # type: ignore
    """
    Transform a column in the data using a SQL expression.

    Parameters
    ----------
    column: str
        Name of the column to transform
    sql_expr: str
        SQL expression to use for transformation
    """

    def __init__(self, column: str, sql_expr: str):
        self.column = column
        self.sql_expr = sql_expr

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "DuckDBColumnSQLTransformer":
        """
        No-op, present for API compatibility.

        Parameters
        ----------
        X : pd.DataFrame
            Input data
        y : ignored
            Not used, present for API compatibility

        Returns
        -------
        self : returns self
        """
        self.is_fitted_ = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the specified column using the SQL expression.

        Parameters
        ----------
        X : pd.DataFrame
            Input data

        Returns
        -------
        pd.DataFrame
            Data with the specified column transformed
        """
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        cols = X.columns.tolist()
        transformed_columns = []
        column_found = False

        for col in cols:
            if col == self.column:
                transformed_columns.append(f"{self.sql_expr} AS {col}")
                column_found = True
            else:
                transformed_columns.append(f'"{col}"')  # noqa: B907

        if not column_found:
            transformed_columns.append(f"{self.sql_expr} AS {self.column}")

        query = f"SELECT {', '.join(transformed_columns)} FROM X"
        return duckdb.query(query).df()
