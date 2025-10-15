"""
Class to preprocessing data
"""

# pylint: disable=too-many-instance-attributes

from typing import Optional

import numpy as np
import pandas as pd


class DataTransformer:
    """
    A class for preprocessing numerical data with various transformation methods.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing data to be transformed
    sqrt_col : list, optional
        Columns for square root transformation (requires non-negative values)
    log_default : list, optional
        Columns for logarithmic transformation with added constant 0.01
    ihs : list, optional
        Columns for inverse hyperbolic sine transformation
    extensive_log : list, optional
        Columns for extensive logarithmic transformation
    neglog : list, optional
        Columns for logarithmic transformation with negative values handling
    log_x_divide_2 : list, optional
        Columns for logarithmic transformation with half minimum non-zero value
    """

    def __init__(
        self,
        data: pd.DataFrame,
        sqrt_col: Optional[list[str]] = None,
        log_default: Optional[list[str]] = None,
        ihs: Optional[list[str]] = None,
        extensive_log: Optional[list[str]] = None,
        neglog: Optional[list[str]] = None,
        log_x_divide_2: Optional[list[str]] = None,
    ) -> None:

        self.transform_data = data.copy()
        self.sqrt_col = sqrt_col if sqrt_col is not None else []
        self.log_default = log_default if log_default is not None else []
        self.ihs = ihs if ihs is not None else []
        self.extensive_log = extensive_log if extensive_log is not None else []
        self.neglog = neglog if neglog is not None else []
        self.log_x_divide_2 = log_x_divide_2 if log_x_divide_2 is not None else []
        self.transform_scheme: dict[str, dict[str, float]] = {"log_x_divide_2": {}, "extensive_log": {}}

    def sqrt_transformation(self, column: str) -> None:
        """Sqrt transformation

        Parameters
        ----------
        column : list
            List of column to transform.
        """
        if (self.transform_data[column] < 0).any():
            raise ValueError(f"Column {column} contains negative values")
        self.transform_data[column] = np.sqrt(self.transform_data[column])

    def log_default_transformation(self, column: str, value_add: float) -> None:
        """Log transformation

        Parameters
        ----------
        column : str
            Name of the column to transform.
        value_add : float
            Constant added before logarithmic transformation.
        """
        self.transform_data[column] = np.log(self.transform_data[column] + value_add)

    def ihs_transformation(self, column: str) -> None:
        """IHS transformation

        Parameters
        ----------
        column : list
            List of column to transform.
        """
        self.transform_data[column] = np.arcsinh(self.transform_data[column])

    def extensive_log_transformation(self, column: str, value: Optional[float] = None) -> None:
        """Extensive log transformation

        Parameters
        ----------
        column : str
            Name of the column to transform.
        value : float, optional
            Minimum value for clipping the data. If None, uses the minimum value from the column.
        """
        min_data = value if value is not None else self.transform_data[column].min()
        self.transform_data[column] = self.transform_data[column].clip(lower=min_data)

        shift = min_data - 1

        if (self.transform_data[column] - shift <= 0).any():
            raise ValueError(f"Column {column} contains negative values")

        self.transform_data[column] = np.log(self.transform_data[column] - shift)

        if value is None:
            self.transform_scheme["extensive_log"][column] = min_data

    def neglog_transformation(self, column: str) -> None:
        """Neglog transformation

        Parameters
        ----------
        column : list
            List of column to transform.
        """
        self.transform_data[column] = self.transform_data[column].apply(lambda x: np.sign(x) * np.log(abs(x) + 1))

    def log_x_divide_2_transformation(self, column: str, value: Optional[float] = None) -> None:
        """Log transformation

        Parameters
        ----------
        column : list
            List of column to transform.
        value : float, optional
            Minimum df value
        """
        min_non_zero = (
            value if value is not None else self.transform_data[self.transform_data[column] > 0][column].min()
        )

        shift = min_non_zero / 2

        if (self.transform_data[column] + shift <= 0).any():
            raise ValueError(f"Column {column} contains negative values")
        self.transform_data[column] = np.log(self.transform_data[column] + shift)

        if value is None:
            self.transform_scheme["log_x_divide_2"][column] = min_non_zero

    def func_transform_data(
        self,
        parameters: Optional[dict[str, dict[str, float]]] = None,
    ) -> pd.DataFrame:
        """Function to transform all data with optional parameters for each transformation.

        Parameters
        ----------
        parameters : dict, optional
            Dictionary containing parameters for transformations and columns in format:
            {
                'transformation_name': {
                    'column_name': parameter_value
                }
            }
            Example:
            {
                'log_x_divide_2': {
                    'column1': 0.5,
                    'column2': 1.0
                },
                'extensive_log': {
                    'column3': 2.0
                }
            }
            If not provided, default parameters will be used for transformations.

        Returns
        -------
        pd.DataFrame
            Transformed DataFrame.
        """

        parameters = parameters or {}

        transformations = {
            "log_default": (self.log_default, self.log_default_transformation, 0.01),
            "sqrt": (self.sqrt_col, self.sqrt_transformation),
            "ihs": (self.ihs, self.ihs_transformation),
            "extensive_log": (self.extensive_log, self.extensive_log_transformation),
            "neglog": (self.neglog, self.neglog_transformation),
            "log_x_divide_2": (self.log_x_divide_2, self.log_x_divide_2_transformation),
        }

        # Definiujemy które transformacje przyjmują jeden parameter
        single_param_transforms = {"sqrt", "ihs", "neglog"}

        for transform_name, transform_info in transformations.items():
            columns = transform_info[0]
            transform_func = transform_info[1]
            transform_params = parameters.get(transform_name, {})

            for column in columns:  # type: ignore
                if column not in self.transform_data.columns:
                    raise ValueError(f"Column {column} not in dataframe")

                if transform_name in single_param_transforms:
                    transform_func(column)  # type: ignore
                else:
                    param_value = transform_info[2] if len(transform_info) == 3 else transform_params.get(column)
                    if param_value is not None:
                        transform_func(column, param_value)  # type: ignore
                    else:
                        transform_func(column)  # type: ignore

        return self.transform_data
