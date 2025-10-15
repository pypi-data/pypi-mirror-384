"""
Model class
"""

from typing import Any, Literal

import pandas as pd

from .algorithm import Algorithm
from .evaluate import ModelEvaluator, ShapExplainer
from .experiments import VertexExperiment
from .hyperopt import Hyperopt
from .metrics import Metrics


# pylint: disable=attribute-defined-outside-init
# pylint: disable=raise-missing-from
# pylint: disable=invalid-name
# pylint: disable=dangerous-default-value
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-instance-attributes


class Modeling:
    """Modeling, metrics and vertex logging.

    Parameters
    ----------
    model : object
        Model class (scikit-learn compatible) that implements fit/predict methods
    X_train : pd.DataFrame
        Training features
    X_test : pd.DataFrame
        Test features
    y_train : pd.Series
        Training labels/values
    y_test : pd.Series
        Test labels/values
    task : Literal["bin", "multi", "reg"]
        Task type: 'reg' for regression, 'bin' for binary classification,
        or 'multi' for multiclass classification
    main_metric : str
        Metric name to optimize during hyperparameter tuning
    name_experiment : str
        Name of the experiment in Vertex AI
    model_params : dict[str, Any] | None, optional
        Initial hyperparameters for model initialization, by default None
    proba : float, default=0.5
        Classification threshold for binary problems. Ignored for regression.
    own_metrics : dict[str, Any] | None, optional
        Custom metrics as {'name': callable(y_true, y_pred)}, by default None
    metrics_average : str, default='binary'
        Averaging method for precision/recall in multiclass case. Ignored for regression.
    beta : float, default=2
        Beta value for fbeta_score calculation. Ignored for regression.
    fbeta_average : str, default='binary'
        Averaging method for fbeta_score in multiclass case. Ignored for regression.
    fbeta_weights : list[float] | None, optional
        Class weights for fbeta_score calculation. Default is [0.5, 0.5]. Ignored for regression.
    data_path : str | None, optional
        Path to data files in DVC, by default None
    labels : list[str] | None, optional
        Class labels for confusion matrix. Ignored for regression. By default None
    shap_sample_size : float | None, optional
        Percentage of samples to use for SHAP explanation, by default None
    project : str, default='sts-notebooks'
        Vertex AI project name
    location : str, default='europe-west4'
        Vertex AI location

    Attributes
    ----------
    model : Algorithm
        Initialized model instance
    metricser : Metrics
        Metrics calculation instance
    evaluator : ModelEvaluator
        Model evaluation instance
    shap_explainer : ShapExplainer, optional
        SHAP values calculator instance
    """

    def __init__(
        self,
        model: Any,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        task: Literal["bin", "multi", "reg"],
        main_metric: str,
        name_experiment: str,
        model_params: dict[str, Any] | None = None,
        proba: float = 0.5,
        own_metrics: dict[str, Any] | None = None,
        metrics_average: str = "binary",
        beta: float = 2,
        fbeta_average: str = "binary",
        fbeta_weights: list[float] | None = None,
        data_path: str | None = None,
        labels: list[str] | None = None,
        shap_sample_size: float | None = None,
        project: str = "sts-notebooks",
        location: str = "europe-west4",
    ) -> None:
        if task not in ["reg", "bin", "multi"]:
            raise ValueError("task must be one of: 'reg', 'bin', 'multi'")

        self.init_model = model
        self.init_X_train = X_train
        self.init_X_test = X_test
        self.init_y_train = y_train
        self.init_y_test = y_test
        self.init_task = task
        self.init_main_metric = main_metric
        self.init_model_params = model_params or {}
        self.init_proba = proba if task != "reg" else 0.5
        self.init_own_metrics = own_metrics
        self.init_metrics_average = metrics_average
        self.init_beta = beta
        self.init_fbeta_average = fbeta_average
        self.init_fbeta_weights = [0.5, 0.5] if fbeta_weights is None else fbeta_weights

        self.model = Algorithm(
            model=model,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            task=task,
            params=self.init_model_params,
            proba=self.init_proba,
        )

        self.metricser = Metrics(
            y_test=self.model.y_test,
            y_pred=self.model.y_pred,
            main_metric=main_metric,
            task=task,
            metrics_average=metrics_average,
            beta=beta,
            fbeta_average=fbeta_average,
            fbeta_weights=self.init_fbeta_weights,
            own_metrics=own_metrics,
        )

        # Determine labels and confusion matrix based on task
        if task != "reg":
            if labels is None:
                labels = [str(label) for label in sorted(self.model.y_test.iloc[:, 0].unique())]
            self.evaluator = ModelEvaluator(self.model, labels)
            confusion_matrix = self.evaluator.get_confusion_matrix()
        else:
            labels = None
            self.evaluator = ModelEvaluator(self.model)  # No labels for regression
            confusion_matrix = None

        self.name_experiment = name_experiment
        self.data_path = data_path
        self.project = project
        self.location = location
        self.task = task

        self.log_vertex_experiments(confusion_matrix, labels)  # Pass confusion_matrix and labels

        if shap_sample_size is not None:
            self.shap_explainer = ShapExplainer(self.model, self.init_task, sample_size=shap_sample_size)

    def log_vertex_experiments(self, confusion_matrix: pd.DataFrame | None, labels: list[str] | None) -> None:
        """Log results of model to Vertex Experiments.

        Parameters
        ----------
        confusion_matrix : pd.DataFrame | None
            Confusion matrix for classification tasks
        labels : list[str] | None
            Class labels for confusion matrix

        Returns
        -------
        None
        """
        if not self.metricser.metrics:
            self.metricser.calculate_metrics()

        vertex_experiment = VertexExperiment(
            self.name_experiment,
            self.model.model_name,
            self.model.task,
            self.metricser.metrics,
            self.model.hyperparams_model(),
            self.data_path,  # type:ignore
            project=self.project,
            location=self.location,
            confusion_matrix=confusion_matrix,  # Use the passed-in value
            labels=labels,  # Use the passed-in value
        )
        vertex_experiment.log_experiment_results_to_vertex()
        self.get_general_metrics()

    def calculate_hyperopt_best_params(
        self, space: dict[str, Any], n_startup_jobs: int, hyperopt_iter: int, is_loss_function: bool = False
    ) -> dict[str, Any]:
        """Calculate optimal hyperparameters using hyperopt.

        Parameters
        ----------
        space : dict
            Hyperparameter search space definition
        n_startup_jobs : int
            Number of random initialization trials
        hyperopt_iter : int
            Total number of optimization iterations
        is_loss_function : bool, default=False
            If True, metric should be minimized instead of maximized

        Returns
        -------
        dict
            Dictionary containing the best parameters found
        """
        self.hyperopt = Hyperopt(
            self.init_model,
            self.init_X_train,
            self.init_X_test,
            self.init_y_train,
            self.init_y_test,
            self.init_task,
            self.init_main_metric,
            self.init_model_params,
            self.init_proba,
            self.init_own_metrics,  # type: ignore
            self.init_metrics_average,
            self.init_beta,
            self.init_fbeta_average,
            self.init_fbeta_weights,
            is_loss_function,
        )
        return self.hyperopt.calculate_hyperopt_best_params(
            space=space,
            model=self.model,
            metricser=self.metricser,
            n_startup_jobs=n_startup_jobs,
            hyperopt_iter=hyperopt_iter,
        )

    def get_general_metrics(self) -> None:
        """Get all metrics and visualization."""
        print(self.metricser.get_main_metric())
        print(self.metricser.metrics)
        self.evaluator.plot_evaluation()

    def get_metrics_for_val(self, X_val: pd.DataFrame, y_val: pd.Series) -> None:
        """Calculate and display model metrics for a validation dataset.

        Parameters
        ----------
        X_val : pd.DataFrame
            Validation features
        y_val : pd.Series
            Validation labels/values
        """
        X_test_orig = self.model.X_test
        y_test_orig = self.model.y_test

        self.model.X_test = X_val
        self.model.y_test = y_val

        self.model.predict()
        self.metricser.calculate_metrics()

        self.get_general_metrics()

        self.model.X_test = X_test_orig
        self.model.y_test = y_test_orig

    def cross_val(self, n_splits: int = 5) -> Any:
        """Perform cross-validation.

        Parameters
        ----------
        n_splits : int, default=5
            Number of folds for cross-validation

        Returns
        -------
        Any
            Cross-validation results
        """
        return self.model.cross_val(self.metricser, n_splits)
