import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.preprocessing import (
    build_frequency_design_matrix,
    build_severity_design_matrix,
    align_to_training_columns,
)
from utils.dates import calculate_vehicle_age
from utils.inflation import apply_inflation
from pricing.adjustments import calculate_technical_premium
from pricing.rating import apply_experience_rating


def calculate_expected_loss(
    freq_model,
    sev_model,
    freq_columns,
    sev_columns,
    freq_category_levels,
    sev_category_levels,
    policy_data: pd.DataFrame
):
    policy_data = policy_data.copy()

    if "VehicleYear" in policy_data.columns and "PricingYear" in policy_data.columns:
        policy_data["VehAge"] = policy_data.apply(
            lambda row: calculate_vehicle_age(
                int(row["VehicleYear"]),
                int(row["PricingYear"])
            ),
            axis=1
        )

    # Frequency
    X_freq = build_frequency_design_matrix(
        policy_data,
        category_levels=freq_category_levels
    )
    X_freq = sm.add_constant(X_freq, has_constant="add")
    X_freq = align_to_training_columns(X_freq, freq_columns)
    X_freq = X_freq.astype(float)

    exposure = pd.to_numeric(policy_data["Exposure"], errors="coerce").astype(float)
    offset = np.log(exposure)

    expected_claims = freq_model.predict(X_freq, offset=offset)

    # Severity
    X_sev = build_severity_design_matrix(
        policy_data,
        category_levels=sev_category_levels
    )
    X_sev = sm.add_constant(X_sev, has_constant="add")
    X_sev = align_to_training_columns(X_sev, sev_columns)
    X_sev = X_sev.astype(float)

    expected_severity = sev_model.predict(X_sev)

    expected_loss = expected_claims * expected_severity

    return {
        "veh_age": float(policy_data["VehAge"].iloc[0]),
        "expected_claims": float(expected_claims.iloc[0]),
        "expected_severity": float(expected_severity.iloc[0]),
        "expected_loss": float(expected_loss.iloc[0]),
    }


def calculate_final_premium(
    expected_loss: float,
    expense_ratio: float = 0.25,
    profit_margin: float = 0.10,
    annual_inflation_rate: float = 0.03,
    inflation_years: int = 1,
    no_accident_years: int = 0,
    accident_count_recent: int = 0
):
    inflated_loss = apply_inflation(
        expected_loss,
        annual_inflation_rate=annual_inflation_rate,
        years=inflation_years
    )

    technical_premium = calculate_technical_premium(
        inflated_loss,
        expense_ratio=expense_ratio,
        profit_margin=profit_margin
    )

    final_premium = apply_experience_rating(
        technical_premium,
        no_accident_years=no_accident_years,
        accident_count_recent=accident_count_recent
    )

    return {
        "inflated_loss": float(inflated_loss),
        "technical_premium": float(technical_premium),
        "final_premium": float(final_premium),
    }


def calculate_premium(
    freq_model,
    sev_model,
    freq_columns,
    sev_columns,
    freq_category_levels,
    sev_category_levels,
    policy_data: pd.DataFrame,
    expense_ratio: float = 0.25,
    profit_margin: float = 0.10,
    annual_inflation_rate: float = 0.03,
    inflation_years: int = 1,
    no_accident_years: int = 0,
    accident_count_recent: int = 0,
):
    loss_result = calculate_expected_loss(
        freq_model,
        sev_model,
        freq_columns,
        sev_columns,
        freq_category_levels,
        sev_category_levels,
        policy_data
    )

    premium_result = calculate_final_premium(
        expected_loss=loss_result["expected_loss"],
        expense_ratio=expense_ratio,
        profit_margin=profit_margin,
        annual_inflation_rate=annual_inflation_rate,
        inflation_years=inflation_years,
        no_accident_years=no_accident_years,
        accident_count_recent=accident_count_recent
    )

    return {
        **loss_result,
        **premium_result,
    }