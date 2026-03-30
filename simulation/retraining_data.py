import pandas as pd
from persistence.database import get_all_policies_raw, get_all_simulated_claims


def build_retraining_datasets():
    policy_rows = get_all_policies_raw()
    claim_rows = get_all_simulated_claims()

    policies_df = pd.DataFrame(policy_rows, columns=[
        "IDpol",
        "customer_id",
        "policy_name",
        "Exposure",
        "VehicleYear",
        "PricingYear",
        "policy_year",
        "VehAge",
        "DrivAge",
        "BonusMalus",
        "Density",
        "VehGas",
        "VehBrand",
        "Region",
        "Area",
        "no_accident_years",
        "accident_count_recent",
        "source_policy_id",
    ])

    claims_df = pd.DataFrame(claim_rows, columns=[
        "claim_id",
        "IDpol",
        "simulation_year",
        "had_claim",
        "ClaimNb",
        "ClaimAmount",
        "created_at",
    ])

    if claims_df.empty:
        freq_df = policies_df.copy()
        freq_df["ClaimNb"] = 0
    else:
        claim_counts = claims_df.groupby("IDpol", as_index=False)["ClaimNb"].sum()
        freq_df = policies_df.merge(claim_counts, on="IDpol", how="left")
        freq_df["ClaimNb"] = freq_df["ClaimNb"].fillna(0).astype(int)

    freq_training = freq_df[[
        "IDpol",
        "ClaimNb",
        "Exposure",
        "VehAge",
        "DrivAge",
        "BonusMalus",
        "VehBrand",
        "VehGas",
        "Density",
        "Region",
        "Area",
    ]].copy()

    sev_training = claims_df[claims_df["ClaimAmount"] > 0][[
        "IDpol",
        "ClaimAmount",
    ]].copy()

    return freq_training, sev_training