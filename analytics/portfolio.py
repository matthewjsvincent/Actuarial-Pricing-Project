import pandas as pd
from persistence.database import get_all_policies_raw
from pricing.premium_calculator import calculate_premium


def forecast_current_portfolio(
    freq_model,
    sev_model,
    freq_columns,
    sev_columns,
    freq_category_levels,
    sev_category_levels,
    expense_ratio=0.25,
    profit_margin=0.10,
    annual_inflation_rate=0.03,
    inflation_years=1,
):
    rows = get_all_policies_raw()
    results = []

    for row in rows:
        policy_id = row[0]

        policy_data = pd.DataFrame([{
            "Exposure": row[3],
            "VehicleYear": row[4],
            "PricingYear": row[5],
            "VehAge": row[7],
            "DrivAge": row[8],
            "BonusMalus": row[9],
            "Density": row[10],
            "VehGas": row[11],
            "VehBrand": row[12],
            "Region": row[13],
            "Area": row[14],
        }])

        result = calculate_premium(
            freq_model,
            sev_model,
            freq_columns,
            sev_columns,
            freq_category_levels,
            sev_category_levels,
            policy_data,
            expense_ratio=expense_ratio,
            profit_margin=profit_margin,
            annual_inflation_rate=annual_inflation_rate,
            inflation_years=inflation_years,
            no_accident_years=int(row[15]),
            accident_count_recent=int(row[16]),
        )

        results.append({
            "policy_id": policy_id,
            "expected_claims": result["expected_claims"],
            "expected_severity": result["expected_severity"],
            "expected_loss": result["expected_loss"],
            "inflated_loss": result["inflated_loss"],
            "technical_premium": result["technical_premium"],
            "final_premium": result["final_premium"],
        })

    df = pd.DataFrame(results)

    if df.empty:
        summary = {
            "policy_count": 0,
            "total_expected_loss": 0.0,
            "total_inflated_loss": 0.0,
            "total_technical_premium": 0.0,
            "total_final_premium": 0.0,
            "avg_final_premium": 0.0,
        }
    else:
        summary = {
            "policy_count": int(len(df)),
            "total_expected_loss": float(df["expected_loss"].sum()),
            "total_inflated_loss": float(df["inflated_loss"].sum()),
            "total_technical_premium": float(df["technical_premium"].sum()),
            "total_final_premium": float(df["final_premium"].sum()),
            "avg_final_premium": float(df["final_premium"].mean()),
        }

    return df, summary