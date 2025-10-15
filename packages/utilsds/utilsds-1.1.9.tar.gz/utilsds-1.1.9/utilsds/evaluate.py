"""Visualization tools for model evaluation."""

from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import shap
from sklearn.metrics import confusion_matrix


class ModelEvaluator:
    """Class for visualizing model performance for both classification and regression.

    Parameters
    ----------
    algorithm : Algorithm
        Algorithm object containing model predictions and actual values
    labels : list, optional
        Labels for plots (class names for classification, axis labels for regression)
    """

    def __init__(self, algorithm: Any, labels: list[str] | None = None) -> None:
        self.algorithm = algorithm
        self.labels = labels

    def plot_evaluation(self) -> None:
        """Generate appropriate visualization based on the task type."""
        if self.algorithm.task in ["bin", "multi"]:
            self.plot_confusion_matrix()
        else:
            self.plot_regression_diagnostics()

    def get_confusion_matrix(self) -> np.array:
        """Return raw confusion matrix for classification tasks.

        Returns
        -------
        np.array
            Raw confusion matrix as nested array
        """
        assert self.algorithm.task in ["bin", "multi"], "Confusion matrix is only for classification tasks"
        return confusion_matrix(self.algorithm.y_test, self.algorithm.y_pred)

    def plot_confusion_matrix(self) -> None:
        """Plot confusion matrix with three values in each cell:
        - absolute count
        - recall (normalized by row)
        - percentage of total
        """
        assert self.algorithm.task in ["bin", "multi"], "Confusion matrix is only for classification tasks"

        cm = confusion_matrix(self.algorithm.y_test, self.algorithm.y_pred)
        cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

        group_counts = [f"{value}" for value in cm.flatten()]
        group_recall_percentage = [f"{round(value, 2)}" for value in cm_norm.flatten()]
        group_percentages = [f"{round(value * 100, 2)}%" for value in cm.flatten() / np.sum(cm)]

        labels = [
            f"{v1}\n{v2}\n{v3}"
            for v1, v2, v3 in zip(group_counts, group_recall_percentage, group_percentages, strict=True)
        ]
        labels = np.asarray(labels).reshape(cm.shape)

        plt.figure(figsize=(4, 3), facecolor="w")
        sns.heatmap(cm_norm, annot=labels, fmt="", cbar=False, vmin=0, cmap="Blues")
        plt.xlabel("Predicted label")
        plt.ylabel("True label")
        plt.title(f"Confusion matrix for {self.algorithm.model_name}")
        plt.show()

    def plot_regression_diagnostics(self) -> None:
        """Generate diagnostic plots for regression:
        - Residual plot
        - Residual histogram
        - Comparison histogram of predicted vs actual values
        """
        assert self.algorithm.task == "reg", "Regression diagnostics are only for regression tasks"

        y_test = np.array(self.algorithm.y_test).ravel()
        y_pred = np.array(self.algorithm.y_pred).ravel()
        residuals = y_test - y_pred

        plt.figure(figsize=(8, 6))
        plt.scatter(y_test, residuals, alpha=0.3, color="green")
        plt.hlines(0, min(y_pred), max(y_pred), colors="red", lw=2)
        plt.title("Residual plot")
        plt.xlabel("Actual values")
        plt.ylabel("Residuals (actual - predicted)")
        plt.grid(True)
        plt.show()

        plt.figure(figsize=(8, 6))
        plt.hist(residuals, bins=50, color="purple", edgecolor="black", alpha=0.7)
        plt.title("Prediction error histogram")
        plt.xlabel("Residuals (actual - predicted)")
        plt.ylabel("Count")
        plt.grid(True)
        plt.show()

        q75, q25 = np.percentile(y_test, [75, 25])
        iqr = q75 - q25
        n = len(y_test)
        h = 2 * iqr / (n ** (1 / 3))
        if h == 0:
            num_bins = int(np.sqrt(n))
        else:
            range_data = np.ptp(y_test)
            num_bins = int(np.ceil(range_data / h))

        num_bins = max(min(num_bins, 100), 20)

        value_range = [min(min(y_test), min(y_pred)), max(max(y_test), max(y_pred))]
        bins = np.linspace(value_range[0], value_range[1], num_bins)
        bin_width = (bins[-1] - bins[0]) / num_bins

        fig, ax = plt.subplots(figsize=(10, 6))

        hist_pred, bins_pred = np.histogram(y_pred, bins=bins)
        ax.barh(
            bins_pred[:-1],
            -hist_pred,
            color="salmon",
            edgecolor="black",
            alpha=0.7,
            height=bin_width,
            label="Predicted values",
            align="edge",
        )

        hist_test, bins_test = np.histogram(y_test, bins=bins)
        ax.barh(
            bins_test[:-1],
            hist_test,
            color="skyblue",
            edgecolor="black",
            alpha=0.7,
            height=bin_width,
            label="Actual values",
            align="edge",
        )

        ax.set_title("Distribution comparison: Actual vs Predicted values")
        ax.set_xlabel("Count")
        ax.set_ylabel("Values")
        max_count = max(hist_pred.max(), hist_test.max())
        padding = max_count * 0.05
        ax.set_xlim(-max_count - padding, max_count + padding)
        ax.legend(loc="upper right")
        ax.grid(True)
        plt.tight_layout()
        plt.show()


class ShapExplainer:
    """Helper class for SHAP explanations.

    Parameters
    ----------
    algorithm : Algorithm
        Algorithm object containing model and data.
    task : {'bin', 'multi', 'reg'}
        Type of machine learning task.
    sample_size : float, optional
        Percentage of test data to use for SHAP analysis (0.01 to 1.0).

    Attributes
    ----------
    algorithm : Algorithm
        Stored algorithm object.
    X_test : pandas.DataFrame
        Test data features.
    task : str
        Type of machine learning task.
    background : numpy.ndarray
        Background data for SHAP calculations.
    explainers : list
        List of SHAP explainers (for classification).
    shap_values : list or numpy.ndarray
        SHAP values for predictions.
    """

    def __init__(self, algorithm: Any, task: Literal["bin", "multi", "reg"], sample_size: float | None = None) -> None:

        self.algorithm = algorithm
        self.X_test = algorithm.X_test
        self.task = task

        if sample_size is not None:
            self.X_test = self.X_test.sample(n=int(len(self.X_test) * sample_size), random_state=42)

        self.background = shap.kmeans(self.X_test, 10)

        # Różna inicjalizacja dla klasyfikacji i regresji
        if self.task in ["bin", "multi"]:
            self.explainers = []
            self.shap_values = []

            # Funkcja do predykcji konkretnej klasy
            def model_predict_class(X: np.ndarray, class_num: int) -> np.ndarray:
                return self.algorithm.estimator.predict_proba(X)[:, class_num]

            n_classes = len(np.unique(self.algorithm.y_test))
            for class_num in range(n_classes):
                explainer = shap.KernelExplainer(lambda x, c=class_num: model_predict_class(x, c), self.background)
                shap_values_class = explainer.shap_values(self.X_test)
                self.explainers.append(explainer)
                self.shap_values.append(shap_values_class)
        else:
            # Inicjalizacja dla regresji
            self.explainer = shap.KernelExplainer(self.algorithm.estimator.predict, self.background)
            self.shap_values = self.explainer.shap_values(self.X_test)

    def plot_summary(self, class_index: int | None = None, split_classes: bool = False) -> None:
        """Generate SHAP summary plot showing feature importance.

        Parameters
        ----------
        class_index : int, optional
            For classification, index of the class to plot. Ignored for regression.
        split_classes : bool, default=False
            If True, generates separate plots for each class in classification tasks.

        Notes
        -----
        For regression tasks, generates a single summary plot.
        For classification tasks, can generate either a single plot for specified class
        or separate plots for all classes if split_classes=True.
        """
        if not split_classes:
            plt.figure(figsize=(10, 6))
            # Dla regresji używamy self.shap_values, dla klasyfikacji bierzemy konkretną klasę
            shap_values_to_plot = (
                self.shap_values
                if self.algorithm.task == "reg"
                else self.shap_values[class_index if class_index is not None else 0]
            )

            shap.summary_plot(shap_values_to_plot, self.X_test, show=False, plot_type="dot")

            title = f"SHAP Feature Impact - {self.algorithm.model_name}"
            if self.algorithm.task in ["bin", "multi"] and class_index is not None:
                title += f" - Class {class_index}"

            plt.title(title)
            plt.tight_layout()
            plt.show()
            return

        # Pokaż osobne wykresy dla każdej klasy (tylko dla klasyfikacji)
        if self.task in ["bin", "multi"]:
            n_classes = len(self.shap_values)
            for i in range(n_classes):
                plt.figure(figsize=(10, 6))
                shap.summary_plot(self.shap_values[i], self.X_test, show=False, plot_type="dot")
                plt.title(f"SHAP Feature Impact - {self.algorithm.model_name} - Class {i}")
                plt.tight_layout()
                plt.show()

    def plot_dependence(
        self,
        feature_name: str,
        interaction_feature: str | None = None,
        class_index: int | None = None,
        split_classes: bool = False,
    ) -> None:
        """Generate SHAP dependence plot for analyzing feature relationships.

        Parameters
        ----------
        feature_name : str
            Name of the feature to analyze.
        interaction_feature : str, optional
            Name of the feature to use for interaction analysis.
            If None, uses the main feature.
        class_index : int, optional
            For classification, index of the class to plot.
            Ignored for regression tasks.
        split_classes : bool, default=False
            If True, generates separate plots for each class in classification tasks.
        """
        if not split_classes:
            plt.figure(figsize=(10, 6))
            # Dla regresji używamy self.shap_values, dla klasyfikacji bierzemy konkretną klasę
            shap_values_to_plot = (
                self.shap_values
                if self.algorithm.task == "reg"
                else self.shap_values[class_index if class_index is not None else 0]
            )

            shap.dependence_plot(
                feature_name,
                shap_values_to_plot,
                self.X_test,
                interaction_index=interaction_feature if interaction_feature else feature_name,
                show=False,
            )

            title = f"SHAP Dependence Plot - {feature_name}"
            if self.algorithm.task in ["bin", "multi"] and class_index is not None:
                title += f" - Class {class_index}"

            plt.title(title)
            plt.tight_layout()
            plt.show()
            return

        # Pokaż osobne wykresy dla każdej klasy (tylko dla klasyfikacji)
        if self.task in ["bin", "multi"]:
            for i in range(len(self.shap_values)):
                plt.figure(figsize=(10, 6))
                shap.dependence_plot(
                    feature_name,
                    self.shap_values[i],
                    self.X_test,
                    interaction_index=interaction_feature if interaction_feature else feature_name,
                    show=False,
                )
                plt.title(f"SHAP Dependence Plot - {feature_name} - Class {i}")
                plt.tight_layout()
                plt.show()

    def plot_waterfall(
        self,
        instance_id: int | None = None,
        max_display: int = 15,
        class_idx: int = 0,
        prediction_class: int | None = None,
    ) -> None:
        """Generate SHAP waterfall plot for detailed instance-level explanation.

        Parameters
        ----------
        instance_id : int, optional
            Index of the instance to explain. If None, randomly selects an instance.
            If prediction_class is specified, this parameter is ignored.
        max_display : int, default=15
            Maximum number of features to show in the plot.
        class_idx : int, default=0
            For classification, index of the class to explain.
            Ignored for regression tasks.
        prediction_class : int, optional
            For classification, finds a random instance that actually belongs to this class.
            If specified, overrides instance_id parameter.
            Uses y_test to find instances with this true label.
        """
        # Jeśli podano prediction_class, znajdź instancję z tej klasy
        if prediction_class is not None and self.task in ["bin", "multi"]:
            # Znajdź indeksy wszystkich instancji z danej klasy
            y_test_aligned = self.algorithm.y_test.loc[self.X_test.index]
            class_instances = np.where(y_test_aligned == prediction_class)[0]

            if len(class_instances) == 0:
                raise ValueError(f"Nie znaleziono żadnej instancji z klasą {prediction_class} w zbiorze testowym")

            # Wybierz losową instancję z tej klasy
            instance_id = np.random.choice(class_instances)
            print(f"Wybrana instancja {instance_id} z predykcją klasy {prediction_class}")
            print(f"Dostępnych instancji z tą predykcją: {len(class_instances)}")
        else:
            # Standardowe zachowanie
            match instance_id:
                case None:
                    instance_id = np.random.randint(0, len(self.X_test))
                case _:
                    pass

        if self.task in ["bin", "multi"]:
            values = self.shap_values[class_idx]  # Wybieramy wartości dla wybranej klasy
            base_value = self.explainers[class_idx].expected_value
            instance_values = values[instance_id]
        else:
            values = self.shap_values
            base_value = self.explainer.expected_value
            instance_values = values[instance_id]

        shap_explanation = shap.Explanation(
            values=instance_values, base_values=base_value, data=self.X_test.iloc[instance_id]
        )

        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(shap_explanation, max_display=max_display)
        title = f"📊 SHAP Waterfall Plot - Instance {instance_id}"
        if self.task in ["bin", "multi"]:
            title += f" - Class {class_idx}"
            if prediction_class is not None:
                title += f" (Predykcja: {prediction_class})"
        print(title)
