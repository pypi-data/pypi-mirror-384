"""Class for classification models.
"""

import pandas as pd
import numpy as np
import inspect

# pylint: disable=dangerous-default-value, invalid-name, too-many-instance-attributes, too-many-arguments


class Classifier:
    """Fit, train and get hyperparams of model.
    Parameters
    ----------
    model : callable
        Model class from library to instantiate as classifier
    X_train : pd.DataFrame
        Training features
    X_test : pd.DataFrame
        Test features
    y_train : pd.Series
        Training labels
    y_test : pd.Series
        Test labels
    is_binary_class : bool
        Whether this is a binary classification problem
    params : dict, optional
        Hyperparameters for model initialization
    proba : float, default=0.5
        Classification threshold for binary problems
    """

    def __init__(
        self,
        model,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        is_binary_class: bool,
        params: dict = {},
        proba: float = 0.5,
    ):
        self.model = model
        self.model_name = type(model()).__name__
        if "id_client" in X_train.columns:
            self.X_train = X_train.drop("id_client", axis=1)
        else:
            self.X_train = X_train
        self.y_train = y_train
        if "id_client" in X_test.columns:
            self.X_test = X_test.drop("id_client", axis=1)
        else:
            self.X_test = X_test
        self.y_test = y_test
        self.random_state = 2024
        self.is_binary_class = is_binary_class
        self.classifier = None
        self.y_pred = []
        self.proba = proba
        self.y_pred_proba = []
        self.fit_predict(params)

    def fit(self, params: dict = None):
        """Fits model to X_train, y_train.

        Parameters
        ----------
        params : dict, optional
            Hyperparams for model creation. Defaults to None.
        """
        params = {} if params is None else params
        if "random_state" in inspect.signature(self.model).parameters:
            self.classifier = self.model(**params, random_state=self.random_state)
        else:
            self.classifier = self.model(**params)
        self.classifier.fit(self.X_train, self.y_train.values.ravel())

    def predict(self):
        """Predict values for self.X_train

        Returns
        -------
        pd.Series
            Predicted labels for X_test.
        """
        self.y_pred = self.classifier.predict(self.X_test)
        return self.y_pred

    def fit_predict(self, params={}):
        """Fit model for X_train and predict for X_test.

        Parameters
        ----------
        params : dict, optional
            Params for the model. Defaults to {}.

        Returns
        -------
        pd.Series
            Predicted labels for X_test.
        """
        self.fit(params)
        self.predict()
        return self.y_pred

    def fit_predict_proba(self):
        """
        Function to train and predict for given threshold (for binary classification only).

        Returns
        -------
        None
        """

        assert self.is_binary_class, "Predict_proba works only for binary classification"

        self.y_pred_proba = (
            self.classifier.predict_proba(self.X_test.values)[:, 1] >= self.proba
        ).astype(bool)

    def hyperparams_model(self):
        """Return all hyperparameters of model, data path and all data columns.

        Returns
        -------
        dict
            All params.
        """
        params = {
            key: value
            for key, value in self.classifier.get_params().items()
            if value is not None and value is not np.nan
        }
        params["proba"] = self.proba
        params["feature_names"] = str(self.X_train.columns.tolist())
        return params
