"""
Confusion matrix class
"""

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from .classifier import Classifier


class ConfusionMatrix:
    """Class for combined and raw confusion matrix.
    Parameters:
        classifier (Classifier): classifier for which CM is calculated.
        labels (list): list of labels to print on CM.
    """

    def __init__(self, classifier: Classifier, labels: list = None):
        self.classifier = classifier
        self.labels = labels

    def get_raw_confusion_matrix(self):
        """Function that returns raw confusion matrix.

        Returns:
            array: Raw confusion matrix, as nested array.
        """
        return confusion_matrix(self.classifier.y_test, self.classifier.y_pred)

    def plot_combined_confusion_matrix(self):
        """
        Plot confusion matrix with three values in each cell:
            absolute count
            recall (normalized by row)
            percentage of total

        Returns:
            Nothing.
        """
        cm = confusion_matrix(self.classifier.y_test, self.classifier.y_pred)

        cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

        group_counts = [f"{value}" for value in cm.flatten()]
        group_recall_percentage = [f"{round(value, 2)}" for value in cm_norm.flatten()]
        group_percentages = [f"{round(value*100, 2)}%" for value in cm.flatten() / np.sum(cm)]

        labels = [
            f"{v1}\n{v2}\n{v3}"
            for v1, v2, v3 in zip(group_counts, group_recall_percentage, group_percentages)
        ]
        labels = np.asarray(labels).reshape(cm.shape)

        plt.figure(figsize=(4, 3), facecolor="w")
        sns.heatmap(cm_norm, annot=labels, fmt="", cbar=False, vmin=0, cmap="Blues")
        plt.xlabel("Predicted label")
        plt.ylabel("True label")
        plt.title(f"Confusion matrix for {self.classifier.model_name}")
