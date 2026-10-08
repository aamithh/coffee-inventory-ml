"""Ensure required libraries import successfully on the installed platform."""

import importlib
import pytest


@pytest.mark.parametrize(
    "module",
    [
        "numpy",
        "pandas",
        "sklearn",
        "lightgbm",
        "statsmodels.api",
        "shap",
        "matplotlib.pyplot",
        "plotly",
        "fastapi",
        "uvicorn",
        "streamlit",
        "sqlalchemy",
        "yaml",
        "joblib",
        "holidays",
        "httpx",
        "nbformat",
    ],
)
def test_required_library_import(module: str) -> None:
    importlib.import_module(module)
