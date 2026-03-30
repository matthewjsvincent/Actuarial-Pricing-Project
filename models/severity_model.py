import pandas as pd
import statsmodels.api as sm

from utils.preprocessing import (
    clean_dataframe,
    build_severity_design_matrix,
    extract_category_levels,
    SEV_CATEGORICAL_COLUMNS,
)


def train_severity_model(freq_data: pd.DataFrame, sev_data: pd.DataFrame):
    merged = pd.merge(sev_data, freq_data, on="IDpol", how="left")

    required_columns = [
        "ClaimAmount",
        "VehAge",
        "DrivAge",
        "BonusMalus",
        "Density",
        "VehGas",
        "VehBrand",
        "Region",
        "Area",
    ]

    model_data = merged[required_columns].copy()
    model_data = clean_dataframe(model_data)

    model_data["ClaimAmount"] = pd.to_numeric(model_data["ClaimAmount"], errors="coerce")
    model_data = model_data.dropna()
    model_data = model_data[model_data["ClaimAmount"] > 0].copy()

    category_levels = extract_category_levels(model_data, SEV_CATEGORICAL_COLUMNS)

    y = pd.to_numeric(model_data["ClaimAmount"], errors="coerce").astype(float)

    X = build_severity_design_matrix(model_data, category_levels=category_levels)
    X = sm.add_constant(X, has_constant="add")
    X = X.astype(float)

    model = sm.GLM(
        y,
        X,
        family=sm.families.Gamma(link=sm.families.links.Log())
    )

    result = model.fit()

    return {
        "model": result,
        "columns": list(X.columns),
        "category_levels": category_levels,
    }