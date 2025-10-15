"""
Vertex Experiments
"""

from datetime import datetime
from typing import Dict, Union

import numpy as np
from google.cloud import aiplatform


# pylint: disable=raise-missing-from, too-many-instance-attributes, too-many-arguments


class VertexExperiment:
    """Class for logging results of experiments on Vertex Experiments.
    Parameters
    ----------
    name_experiment : str
        Name of the Vertex Experiments instance.
    model_name : str
        Type of the evaluated model.
    task : str
        Type of the machine learning task.
    metrics : dict
        Dictionary containing calculated metrics.
    model_params : dict
        Model hyperparameters for logging.
    data_path : str
        Directory path for data in DVC.
    project : str, optional
        Google Cloud project name (default: "sts-notebooks").
    location : str, optional
        Google Cloud location (default: "europe-west4").
    confusion_matrix : numpy.ndarray, optional
        Raw confusion matrix for logging (only for classification).
    labels : numpy.ndarray, optional
        Array of labels for confusion matrix (only for classification).

    Returns
    -------
    None
    """

    def __init__(
        self,
        name_experiment: str,
        model_name: str,
        task: str,
        metrics: Dict[str, float],
        model_params: Dict[str, Union[str, float, int]],
        data_path: str,
        project: str = "sts-notebooks",
        location: str = "europe-west4",
        confusion_matrix: np.ndarray = None,
        labels: np.ndarray = None,
    ):
        self.name_experiment = name_experiment
        self.model_name = model_name.lower()
        self.task = task
        self.metrics = metrics
        self.model_params = model_params
        self.data_path = data_path
        self.project = project
        self.location = location
        self.confusion_matrix = confusion_matrix
        self.labels = labels

    def log_confusion_matrix(self) -> None:
        """Calculate and write confusion matrix in vertex experiment."""
        if self.confusion_matrix is not None and self.labels is not None:
            aiplatform.log_classification_metrics(
                labels=self.labels,
                matrix=self.confusion_matrix.tolist(),
                display_name="confusion-matrix",
            )

    def log_experiment_results_to_vertex(self) -> None:
        """The function saves all values (params, metrics) on Vertex experiments.
        Returns
        -------
        None
        """

        try:
            aiplatform.init(
                project=self.project,
                location=self.location,
                experiment=self.name_experiment,
                experiment_tensorboard=False,
            )
            run_name = f"""{self.model_name
                            }{datetime.now().strftime("%Y%m%d%H%M%S")}"""
            aiplatform.start_run(run_name)

            extended_params = {
                key: str(value) if not isinstance(value, (int, str, float)) else value
                for key, value in self.model_params.items()
            }
            extended_params["data_path"] = self.data_path

            aiplatform.log_params(extended_params)
            aiplatform.log_metrics(self.metrics)

            if self.confusion_matrix is not None:
                self.log_confusion_matrix()

            aiplatform.end_run()

        except (TypeError, RuntimeError) as e:
            aiplatform.end_run()
            experiment_run = aiplatform.ExperimentRun(
                run_name=run_name,
                experiment=self.name_experiment,
                project=self.project,
                location=self.location,
            )
            experiment_run.delete()

            if isinstance(e, TypeError):
                raise TypeError(f"TypeError: Change parameters. Experiment_run {run_name} was removed.") from e
            else:
                raise RuntimeError(f"UnspecifiedRuntimeError: Experiment_run {run_name} was removed.") from e
