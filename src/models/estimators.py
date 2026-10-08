"""Fold-fitted preprocessing and portable global forecast bundles."""

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class ModelBundle:
    """Predict using a frozen feature contract and past-only cold-start fallback."""

    name: str
    pipeline: Pipeline
    feature_columns: list[str]
    trained_through: str
    category_means: dict[str, float]
    overall_mean: float
    transformed_mean: np.ndarray
    cold_start_days: int
    quantile: float | None = None

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        """Keep unknown categories valid and clamp nonnegative expected item counts."""
        prediction = self.pipeline.predict(frame[self.feature_columns])
        cold = frame["history_days"].lt(self.cold_start_days)
        fallback = (
            frame["category_past_mean"]
            .fillna(frame["category"].map(self.category_means))
            .fillna(self.overall_mean)
        )
        if self.quantile is not None:
            fallback = frame["category"].map(self.category_means).fillna(self.overall_mean)
        return np.maximum(np.where(cold, fallback, prediction), 0.0)


def make_pipeline(
    name: str,
    columns: list[str],
    config: dict[str, Any],
    parameters: dict | None = None,
    quantile: float | None = None,
) -> Pipeline:
    """Fit category encoding, medians and optional scaling within each training fold."""
    cats = ["item", "category"]
    numeric = [column for column in columns if column not in cats]
    number_steps = [("impute", SimpleImputer(strategy="median", keep_empty_features=True))]
    if name == "ridge":
        number_steps.append(("scale", StandardScaler()))
    preprocess = ColumnTransformer(
        [
            ("numeric", Pipeline(number_steps), numeric),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats),
        ],
        verbose_feature_names_out=True,
    )
    preprocess.set_output(transform="pandas")
    if name == "ridge":
        estimator = Ridge(alpha=config["models"]["ridge_alpha"])
    elif name == "lightgbm":
        settings = {**config["models"]["lightgbm"], **(parameters or {})}
        settings.update(
            random_state=config["project"]["seed"], deterministic=True, force_col_wise=True
        )
        if quantile is not None:
            settings.update(objective="quantile", alpha=quantile)
        estimator = LGBMRegressor(**settings)
    else:
        raise ValueError(f"Unknown estimator: {name}")
    return Pipeline([("preprocess", preprocess), ("model", estimator)])


def fit_bundle(
    name: str,
    frame: pd.DataFrame,
    columns: list[str],
    config: dict[str, Any],
    parameters: dict | None = None,
    quantile: float | None = None,
) -> ModelBundle:
    """Use eligible training targets only; callers must pass the intended date slice."""
    training = frame.loc[frame.target_eligible].copy()
    if training.empty:
        raise ValueError("No eligible training targets.")
    pipeline = make_pipeline(name, columns, config, parameters, quantile)
    pipeline.fit(training[columns], training.target)
    encoded = pipeline.named_steps["preprocess"].transform(training[columns])
    return ModelBundle(
        name,
        pipeline,
        list(columns),
        training.date.max().strftime("%Y-%m-%d"),
        (
            training.groupby("category").target.mean()
            if quantile is None
            else training.groupby("category").target.quantile(quantile)
        ).to_dict(),
        float(training.target.mean() if quantile is None else training.target.quantile(quantile)),
        encoded.mean(axis=0).to_numpy(),
        config["features"]["cold_start_days"],
        quantile,
    )
