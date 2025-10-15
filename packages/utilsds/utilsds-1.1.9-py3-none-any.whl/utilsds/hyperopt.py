"""
Hyperopt
"""

from functools import partial
from typing import Any, Dict

import pandas as pd
from hyperopt import STATUS_OK, Trials, fmin, space_eval, tpe

from .algorithm import Algorithm
from .metrics import Metrics


class Hyperopt:
    """Class for obtaining best hyperparams by hyperopt.

    Parameters
    ----------
    model : object
        Model object (Classifier or Regressor) to optimize
    X_train : pd.DataFrame
        Training features
    X_test : pd.DataFrame
        Testing features
    y_train : pd.Series
        Training target
    y_test : pd.Series
        Testing target
    task : str
        Type of task ('classification' or 'regression')
    main_metric : str
        Name of the metric to optimize
    model_params : Dict[str, Any]
        Model parameters
    proba : float
        Probability threshold for classification
    own_metrics : Dict[str, Any]
        Dictionary of custom metrics
    metrics_average : str
        Averaging method for metrics calculation
    beta : float
        Beta parameter for F-beta score
    fbeta_average : str
        Averaging method for F-beta score
    fbeta_weights : list[float]
        Weights for F-beta score calculation
    is_loss_function : bool
        Defines if main_metric is loss_function or needs to be adjusted as loss function
    """

    def __init__(
        self,
        model: Any,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        task: str,
        main_metric: str,
        model_params: Dict[str, Any],
        proba: float,
        own_metrics: Dict[str, Any],
        metrics_average: str,
        beta: float,
        fbeta_average: str,
        fbeta_weights: list[float],
        is_loss_function: bool,
    ):

        self.trial_model = Algorithm(
            model=model,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            task=task,
            params=model_params,
            proba=proba,
        )

        self.trial_metricser = Metrics(
            y_test=self.trial_model.y_test,
            y_pred=self.trial_model.y_pred,
            main_metric=main_metric,
            task=task,
            metrics_average=metrics_average,
            beta=beta,
            fbeta_average=fbeta_average,
            fbeta_weights=fbeta_weights,
            own_metrics=own_metrics,
        )
        self.is_loss_function = is_loss_function
        self.best_params: Dict[str, Any] = {}
        self.trials = None

    def _fit_predict_metrics(self, params: Dict[str, Any]) -> None:
        """Fit predict model with given parameters and calculate metrics.

        Parameters
        ----------
        params : Dict[str, Any]
            Parameters for model fitting
        """
        self.trial_model.fit_predict(params)
        self.trial_metricser.y_pred = self.trial_model.y_pred
        self.trial_metricser.calculate_metrics()

    def objective(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Function for hyperopt to fit predict and calculate loss.

        Parameters
        ----------
        params : Dict[str, Any]
            Dict of hyperparameter for model

        Returns
        -------
        Dict[str, Any]
            Dictionary containing loss value and status with keys:
            - 'loss': float
            - 'status': str
        """
        self._fit_predict_metrics(params)
        main_metric_score = self.trial_metricser.get_main_metric()["score"]
        hyperopt_multiplier = 1 if self.is_loss_function else -1
        loss = hyperopt_multiplier * main_metric_score  # type: ignore

        # Print current iteration parameters and score
        current_trial_num = len(self.trials.trials)  # type: ignore
        print(f"\nIteration {current_trial_num}")
        print(f"Current params: {params}")
        print(f"Current score: {main_metric_score}")

        # Get current best parameters and print them if we have completed trials
        if current_trial_num > 0:  # Check if we have any completed trials
            try:
                best_trial = sorted(self.trials.trials, key=lambda x: x["result"]["loss"])[0]  # type: ignore
                current_best_params = space_eval(self.trials.space, best_trial["misc"]["vals"])  # type: ignore
                current_best_loss = best_trial["result"]["loss"]
                print(f"Best params so far: {current_best_params}")
                print(f"Best score so far: {current_best_loss * hyperopt_multiplier}")
            except (KeyError, IndexError):
                # Skip printing best params if there's an error accessing trial results
                pass

        return {"loss": loss, "status": STATUS_OK}

    def calculate_hyperopt_best_params(
        self,
        space: Dict[str, Any],
        model: Any,
        metricser: Any,
        n_startup_jobs: int = 5,
        hyperopt_iter: int = 100,
    ) -> Dict[str, Any]:
        """Calculate models and return the best parameters.

        Parameters
        ----------
        space : Dict[str, Any]
            Dict of parameter space, example: "'C': hp.uniform('C', 0.1, 100)"
        model : Any
            Model object to be optimized
        metricser : Any
            Metrics object for evaluation
        n_startup_jobs : int, optional
            Number of random hyperparameters search, by default 5
        hyperopt_iter : int, optional
            Number of iteration for hyperopt, by default 100

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the best parameters found
        """
        self.trials = Trials()
        self.best_params = fmin(
            fn=self.objective,
            space=space,
            algo=partial(tpe.suggest, n_startup_jobs=n_startup_jobs),
            max_evals=hyperopt_iter,
            trials=self.trials,
        )

        self.best_params = space_eval(space, self.best_params)
        model.fit_predict(self.best_params)
        metricser.calculate_metrics()

        print(f"The best params: {self.best_params}\n")
        return self.best_params
