"""
Metrics for both classification and regression models
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    fbeta_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


class Metrics:
    """Calculates metrics for model and allows own metrics to be calculated.
    Parameters
    ----------
    y_test : pd.Series
        True values
    y_pred : pd.Series
        Predicted values
    task : str
        Type of task - 'reg' for regression, 'bin' for binary classification,
        or 'multi' for multiclass classification
    main_metric : str
        Name of the main metric used for optimization
    metrics_average : str, optional (default='binary')
        Averaging method for metrics in multiclass classification
    beta : float, optional (default=2)
        Beta parameter for fbeta_score metric
    fbeta_average : str, optional (default='binary')
        Averaging method for fbeta_score in multiclass classification
    fbeta_weights : list, optional (default=[0.5, 0.5])
        Weights for individual classes when calculating fbeta_score
    own_metrics : dict, optional (default=None)
        Dictionary of custom metrics in format {'name': function(y_test, y_pred)}
    """

    REGRESSION_METRICS = {
        "mean_absolute_error": "MAE",
        "mean_squared_error": "MSE",
        "root_mean_squared_error": "RMSE",
        "r2_score": "R²",
    }

    CLASSIFICATION_METRICS = {
        "specificity": "Specificity",
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "f_beta": "F-beta Score",
    }

    def __init__(
        self,
        y_test: pd.Series,
        y_pred: pd.Series,
        task: str,
        main_metric: str,
        metrics_average: str = "binary",
        beta: float = 2,
        fbeta_average: str = "binary",
        fbeta_weights: list[float] | None = None,
        own_metrics: dict[str, Any] | None = None,
    ):
        if task not in ["reg", "bin", "multi"]:
            raise ValueError("Task must be one of: 'reg', 'bin', 'multi'")

        self.y_test = y_test
        self.y_pred = y_pred
        self.task = task
        self.metrics_average = metrics_average
        self.beta = beta
        self.fbeta_average = fbeta_average
        self.fbeta_weights = [0.5, 0.5] if fbeta_weights is None else fbeta_weights
        self.metrics: dict[str, float] = {}
        self.own_metrics = own_metrics
        self.main_metric = main_metric
        self.main_metric_score: float | None = None

        if self.own_metrics:
            self.add_own_metrics(self.own_metrics)
        self.set_main_metric(self.main_metric)

        if task != "reg" and not np.isclose(sum(self.fbeta_weights), 1.0):
            raise ValueError("Sum of fbeta_weights must be equal to 1.")

    def custom_fbeta_score(self, y_test: pd.Series, y_pred: pd.Series) -> float:
        """
        Calculate fbeta score

        Parameters
        ----------
        y_test : pd.Series
            Target variable of test data
        y_pred : pd.Series
            Target variable of prediction model

        Returns
        -------
        float
            fbeta_score
        """
        if self.task == "bin":
            score = fbeta_score(y_test, y_pred, beta=self.beta)
            return float(round(score, 4))
        else:
            scores = fbeta_score(
                y_true=y_test,
                y_pred=y_pred,
                beta=self.beta,
                average=self.fbeta_average,
            )
            calculated_fbeta_score = 0
            try:
                for i in range(len(scores)):
                    calculated_fbeta_score = calculated_fbeta_score + scores[i] * self.fbeta_weights[i]
                return calculated_fbeta_score
            except IndexError as e:
                raise ValueError("Length of scores and fbeta_weights are not equal") from e

    def specifity_score(self, y_test: pd.Series, y_pred: pd.Series) -> float:
        """Calculates specifity_score for binary_classification.

        Parameters
        ----------
        y_test : pd.Series
            Target variable of test data
        y_pred : pd.Series
            Target variable of prediction model

        Returns
        -------
        float
            specificity score.
        """
        tn, fp, _, _ = confusion_matrix(y_test, y_pred).ravel()
        return float(tn / (tn + fp))

    def _calculate_regression_metrics(self) -> dict[str, float]:
        """Calculate metrics for regression tasks."""
        return {
            "mean_absolute_error": mean_absolute_error(self.y_test, self.y_pred),
            "mean_squared_error": mean_squared_error(self.y_test, self.y_pred),
            "root_mean_squared_error": np.sqrt(mean_squared_error(self.y_test, self.y_pred)),
            "r2_score": r2_score(self.y_test, self.y_pred),
        }

    def _calculate_classification_metrics(self) -> dict[str, float]:
        """Calculate metrics for classification tasks."""
        metrics = {
            "accuracy": accuracy_score(self.y_test, self.y_pred),
            "precision": precision_score(self.y_test, self.y_pred, average=self.metrics_average),
            "recall": recall_score(self.y_test, self.y_pred, average=self.metrics_average),
        }

        if self.task == "bin":
            metrics["specificity"] = self.specifity_score(self.y_test, self.y_pred)

        if self.beta is not None:
            try:
                metrics["f_beta"] = self.custom_fbeta_score(self.y_test, self.y_pred)
            except Exception as e:
                print(f"Error calculating fbeta_score: {str(e)}")

        return metrics

    def calculate_metrics(self) -> dict[str, float]:
        """Calculate all metrics based on model type.

        Returns
        -------
        dict
            Dictionary containing {'metric_name': metric_value}

        """
        metrics = (
            self._calculate_regression_metrics() if self.task == "reg" else self._calculate_classification_metrics()
        )

        metrics = self._add_custom_metrics(metrics)
        self.metrics = {metric_name: round(float(metric_value), 4) for metric_name, metric_value in metrics.items()}

        return self.metrics

    def _get_valid_metrics(self) -> dict[str, str]:
        """Helper method to get valid metrics based on task type."""
        return self.REGRESSION_METRICS if self.task == "reg" else self.CLASSIFICATION_METRICS

    def add_own_metrics(self, own_metrics: dict) -> None:  # type: ignore
        """Add own metrics and calculate all metrics.

        Parameters
        ----------
            own_metrics (dict): Dictionary containing{'name_of_metric': function_to_calculate_metric},
                where function_to_calculate_metric must have parameters(y_test, y_pred).

        Returns
        -------
            None
        """
        self.own_metrics = own_metrics
        self.calculate_metrics()

    def _add_custom_metrics(self, metrics: dict[str, float]) -> dict[str, float]:
        """Add user-defined metrics to the metrics dictionary.

        Parameters
        ----------
        metrics : dict[str, float]
            Dictionary of existing metrics to be extended

        Returns
        -------
        dict[str, float]
            Dictionary containing both existing and custom metrics
        """
        if not self.own_metrics:
            return metrics

        for metric_name, metric_func in self.own_metrics.items():
            try:
                metrics[metric_name] = metric_func(self.y_test, self.y_pred)
            except Exception as e:
                print(f"Error calculating custom metric {metric_name!r}: {str(e)}")

        return metrics

    def set_main_metric(self, metric_name: str) -> None:
        """Select main metric for optimizing.

        Parameters
        ----------
        metric_name : str
            Name of metrics to be set as default.
            For classification: specificity, accuracy, precision, recall, f_beta
            For regression: mean_absolute_error, mean_squared_error, root_mean_squared_error, r2_score

        Raises
        ------
        ValueError
            If metric_name is not valid for the current task type
        """
        self.calculate_metrics()
        valid_metrics = self._get_valid_metrics()

        if metric_name in self.metrics:
            self.main_metric = metric_name
            self.main_metric_score = self.metrics[metric_name]
            print(f"Current main metric: {self.main_metric}")
        else:
            metrics_list = [f"{value} ({key})" for key, value in valid_metrics.items()]
            raise ValueError(
                f"Invalid metric name for {self.task} task.\n" f"Please choose from: {', '.join(metrics_list)}"
            )

    def get_main_metric(self) -> dict[str, str | float | None]:
        """Get main metric name and value.

        Returns
        -------
        dict
            Dictionary with {'name': name_of_main_metric, 'score': score_of_main_metric.}
        """
        self.main_metric_score = self.metrics[self.main_metric]
        return {"name": self.main_metric, "score": self.main_metric_score}
