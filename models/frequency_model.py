import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.preprocessing import (
    clean_dataframe,
    build_frequency_design_matrix,
    extract_category_levels,
    FREQ_CATEGORICAL_COLUMNS,
)


def train_frequency_model(data: pd.DataFrame):
    required_columns = [
        "ClaimNb",
        "Exposure",
        "VehAge",
        "DrivAge",
        "BonusMalus",
        "Density",
        "VehGas",
        "VehBrand",
        "Region",
        "Area",
    ]

    model_data = data[required_columns].copy()
    model_data = clean_dataframe(model_data)

    model_data["ClaimNb"] = pd.to_numeric(model_data["ClaimNb"], errors="coerce")
    model_data["Exposure"] = pd.to_numeric(model_data["Exposure"], errors="coerce")

    model_data = model_data.dropna()
    model_data = model_data[model_data["Exposure"] > 0].copy()

    category_levels = extract_category_levels(model_data, FREQ_CATEGORICAL_COLUMNS)

    y = pd.to_numeric(model_data["ClaimNb"], errors="coerce").astype(float)

    X = build_frequency_design_matrix(model_data, category_levels=category_levels)
    X = sm.add_constant(X, has_constant="add")
    X = X.astype(float)

    offset = np.log(model_data["Exposure"].astype(float))

    model = sm.GLM(
        y,
        X,
        family=sm.families.Poisson(),
        offset=offset
    )

    result = model.fit()

    return {
        "model": result,
        "columns": list(X.columns),
        "category_levels": category_levels,
    }