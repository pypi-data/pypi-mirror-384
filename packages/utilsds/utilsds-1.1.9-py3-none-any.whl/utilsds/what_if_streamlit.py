"""
Class for what-if analysis in streamlit.
"""

import json
import os
import pickle
from typing import Any, Optional, Union

import pandas as pd


class ShapSaver:
    """
    Class for saving SHAP explainer components.
    Extracts and saves only necessary components for later lazy loading.
    """

    def __init__(self) -> None:
        """Initialize SHAP saver."""
        pass

    def save_from_shap_explainer(self, shap_explainer: Any, filepath: str) -> bool:
        """
        Save components from ShapExplainer object.

        Args:
            shap_explainer: ShapExplainer - should be passed as model.shap_explainer from our modeling
            filepath: File path

        Returns:
            bool: True if success
        """
        try:
            # Utwórz katalog jeśli nie istnieje
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Przygotuj komponenty do zapisania
            components = {
                "task": shap_explainer.task,
                "shap_values": shap_explainer.shap_values,
                "X_test": shap_explainer.X_test,
                "background": shap_explainer.background,
                "algorithm_info": {
                    "model_name": getattr(shap_explainer.algorithm, "model_name", "Unknown"),
                    "task": shap_explainer.algorithm.task,
                },
            }

            # Zapisz expected_values (bez explainer'ów)
            if shap_explainer.task in ["bin", "multi"]:
                expected_values = []
                for explainer in shap_explainer.explainers:
                    expected_values.append(explainer.expected_value)
                components["expected_values"] = expected_values
                components["n_classes"] = len(shap_explainer.explainers)
            else:
                components["expected_values"] = shap_explainer.explainer.expected_value
                components["n_classes"] = 1

            # Spróbuj zapisać model (dla lazy recreation)
            if hasattr(shap_explainer.algorithm, "estimator"):
                try:
                    components["model"] = shap_explainer.algorithm.estimator
                    components["has_model"] = True
                except Exception:
                    components["has_model"] = False
            else:
                components["has_model"] = False

            # Zapisz z pickle
            with open(filepath, "wb") as f:
                pickle.dump(components, f)

            return True

        except Exception:
            return False


class ColumnMetadataGenerator:
    def __init__(self, data_source: Union[str, pd.DataFrame]) -> None:
        """
        Initialize column metadata generator.

        Parameters:
        data_source (Union[str, pd.DataFrame]): Path to CSV file or pandas DataFrame
        """
        if isinstance(data_source, str):
            self.df = pd.read_csv(data_source)
        elif isinstance(data_source, pd.DataFrame):
            self.df = data_source.copy()
        else:
            raise TypeError("data_source must be either a file path (str) or pandas DataFrame")

    def generate_column_metadata(self, excluded_columns: Optional[list[str]] = None) -> dict[str, Any]:
        """
        Generate basic metadata for DataFrame columns.

        Parameters:
        excluded_columns (list): List of column names to exclude

        Returns:
        dict: Dictionary with column metadata
        """
        excluded_columns = excluded_columns or ["id_client"]
        columns_metadata = {}

        for col in self.df.columns:
            if col in excluded_columns:
                continue

            col_type = str(self.df[col].dtype)
            col_info: dict[str, Any] = {"dtype": col_type}

            if col_type in ["int64", "int32", "float64", "float32"]:
                values = self.df[col].dropna()
                if not values.empty:
                    col_info["min_value"] = float(values.min())
                    col_info["max_value"] = float(values.max())

            elif col_type == "object":
                col_info["unique_values"] = sorted(self.df[col].dropna().unique().tolist())

            columns_metadata[col] = col_info

        return columns_metadata

    def save_metadata_to_json(
        self, output_file: str = "columns_metadata.json", excluded_columns: Optional[list[str]] = None
    ) -> None:
        """
        Generate metadata and save it to JSON file.

        Parameters:
        output_file (str): Output file name
        excluded_columns (list): List of column names to exclude
        """
        metadata = self.generate_column_metadata(excluded_columns)

        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)
