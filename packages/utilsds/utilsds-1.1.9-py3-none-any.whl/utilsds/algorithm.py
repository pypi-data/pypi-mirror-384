"""Base class for machine learning algorithms (classification and regression)."""

import inspect
import pickle
from contextlib import contextmanager
from typing import Any, Dict, Iterator

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold


# pylint: disable=dangerous-default-value, invalid-name, too-many-instance-attributes, too-many-arguments


class Algorithm:
    """Fit, train and get hyperparams of model.
    Parameters
    ----------
    model : callable
        Model class from library to instantiate
    X_train : pd.DataFrame
        Training features
    X_test : pd.DataFrame
        Test features
    y_train : pd.Series
        Training target values/labels
    y_test : pd.Series
        Test target values/labels
    task : str
        Type of task - 'reg' for regression, 'bin' for binary classification,
        or 'multi' for multiclass classification
    params : dict, optional
        Hyperparameters for model initialization
    proba : float, default=0.5
        Classification threshold for binary problems (ignored for regression)
    """

    def __init__(
        self,
        model: Any,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        task: str,
        params: Dict[str, Any] | None = None,
        proba: float = 0.5,
    ):
        if task not in ["reg", "bin", "multi"]:
            raise ValueError("Task must be one of: 'reg', 'bin', 'multi'")

        self.model = model
        self.model_name = type(model()).__name__
        self.task = task

        self.X_train = X_train.drop("id_client", axis=1) if "id_client" in X_train.columns else X_train
        self.y_train = y_train
        self.X_test = X_test.drop("id_client", axis=1) if "id_client" in X_test.columns else X_test
        self.y_test = y_test

        self.random_state = 2024
        self.estimator = None
        self.y_pred: list[np.ndarray] = []
        self.y_pred_val: list[np.ndarray] = []

        if task != "reg":
            self.is_binary_class = task == "bin"
            self.proba = proba
            self.y_pred_proba: list[np.ndarray] = []

        self.fit_predict(params if params is not None else {})

    @contextmanager
    def _temporary_state(self, metrics: Any) -> Iterator[None]:
        """Temporarily modify model state and restore it afterwards.

        Parameters
        ----------
        metrics : Any
            Metrics object used for calculating model performance metrics

        Yields
        ------
        None
            Yields control back to the caller
        """
        temp_model = pickle.loads(pickle.dumps(self.estimator))
        original_X_train = self.X_train.copy(deep=True)
        original_X_test = self.X_test.copy(deep=True)
        original_y_train = self.y_train.copy(deep=True)
        original_y_test = self.y_test.copy(deep=True)

        try:
            yield
        finally:
            self.X_train = original_X_train
            self.X_test = original_X_test
            self.y_train = original_y_train
            self.y_test = original_y_test
            self.estimator = temp_model
            self.fit_predict()
            metrics.calculate_metrics()

    def fit(self, params: Dict[str, Any] | None = None) -> None:
        """Fits model to X_train, y_train.

        Parameters
        ----------
        params : dict, optional
            Hyperparams for model creation. Defaults to None.
        """
        params = {} if params is None else params

        if "random_state" in inspect.signature(self.model).parameters:
            self.estimator = self.model(**params, random_state=self.random_state)
        else:
            self.estimator = self.model(**params)

        self.estimator.fit(self.X_train, self.y_train.values.ravel())  # type: ignore

    def predict(self) -> np.ndarray:
        """Predict values for self.X_test

        Returns
        -------
        np.ndarray
            Predicted values/labels for X_test
        """
        self.y_pred = self.estimator.predict(self.X_test)  # type: ignore
        return self.y_pred

    def predict_val(self, X_val: pd.DataFrame) -> np.ndarray:
        """Predict values for X_val

        Parameters
        ----------
        X_val : pd.DataFrame
            Validation features

        Returns
        -------
        np.array
            Predicted values/labels for X_val.
        """
        self.y_pred_val = self.estimator.predict(X_val)  # type: ignore
        return self.y_pred_val

    def fit_predict(self, params: Dict[str, Any] | None = None) -> np.ndarray:
        """Fit model for X_train and predict for X_test.

        Parameters
        ----------
        params : dict, optional
            Params for the model. Defaults to {}.

        Returns
        -------
        np.array
            Predicted values/labels for X_test.
        """
        params = {} if params is None else params
        self.fit(params)
        self.predict()
        return self.y_pred

    def predict_proba(self, X: pd.DataFrame | None = None) -> np.ndarray:
        """
        Predict probabilities for multi-class classification.

        Parameters
        ----------
        X : array-like, optional
            Test dataset. If None, it uses self.X_test.

        Returns
        -------
        np.array
            Predicted probabilities for each class.
        """
        if X is None:
            X = self.X_test  # Use stored test data if not provided

        if self.task == "bin":
            return self.estimator.predict_proba(X)[:, 1].reshape(-1, 1)  # type: ignore # Binary classification

        elif self.task == "multi":
            return self.estimator.predict_proba(X)  # type: ignore # Multi-class classification

        else:
            raise ValueError("Task must be 'bin' or 'multi'")

    def hyperparams_model(self) -> Dict[str, Any]:
        """Return all hyperparameters of model and feature names.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing model parameters and feature names
        """
        params = {
            key: value
            for key, value in self.estimator.get_params().items()  # type: ignore
            if value is not None and value is not np.nan
        }
        params["feature_names"] = str(self.X_train.columns.tolist())

        if self.task != "reg":
            params["proba"] = self.proba

        return params

    def cross_val(self, metrics: Any, n_splits: int = 5) -> None:
        """Calculate average score from cross validation.

        Parameters
        ----------
        metrics : Metrics
            Metrics object for calculating scores
        n_splits: int, default=5
            Number of folds. Must be at least 2.
        """
        with self._temporary_state(metrics):
            X = pd.concat([self.X_train, self.X_test])
            y = pd.concat([self.y_train, self.y_test]).squeeze()

            scores = []
            cv_splitter = KFold if self.task == "reg" else StratifiedKFold
            splitter = cv_splitter(n_splits=n_splits, random_state=self.random_state, shuffle=True)

            split_args = (X,) if self.task == "reg" else (X, y)

            for train_idx, test_idx in splitter.split(*split_args):
                self.X_train, self.X_test = X.iloc[train_idx], X.iloc[test_idx]
                self.y_train, self.y_test = y.iloc[train_idx], y.iloc[test_idx]

                self.fit_predict()
                metrics.calculate_metrics()
                scores.append(metrics.get_main_metric()["score"])

            cv_type = "k-fold" if self.task == "reg" else "stratified k-fold"
            print(f"For {cv_type}: {metrics.main_metric} = {np.mean(scores)}; std = {np.std(scores)}")
