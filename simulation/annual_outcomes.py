import math
import random
import pandas as pd

from persistence.database import create_simulated_claim, get_all_policies_raw
from pricing.premium_calculator import calculate_expected_loss


def _simulate_poisson(lam: float) -> int:
    if lam <= 0:
        return 0

    limit = math.exp(-lam)
    k = 0
    p = 1.0

    while p > limit:
        k += 1
        p *= random.random()

    return k - 1


def _simulate_claim_amount(expected_severity: float) -> float:
    if expected_severity <= 0:
        return 0.0

    return float(random.lognormvariate(math.log(max(expected_severity, 1.0)), 0.5))


def simulate_annual_claims_for_current_portfolio(
    freq_model,
    sev_model,
    freq_columns,
    sev_columns,
    freq_category_levels,
    sev_category_levels,
    simulation_year: int
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

        expected = calculate_expected_loss(
            freq_model,
            sev_model,
            freq_columns,
            sev_columns,
            freq_category_levels,
            sev_category_levels,
            policy_data
        )

        expected_claims = expected["expected_claims"]
        expected_severity = expected["expected_severity"]

        claim_count = _simulate_poisson(expected_claims)

        total_claim_amount = 0.0
        for _ in range(claim_count):
            total_claim_amount += _simulate_claim_amount(expected_severity)

        had_claim = 1 if claim_count > 0 else 0

        create_simulated_claim(
            policy_id=policy_id,
            simulation_year=simulation_year,
            had_claim=had_claim,
            claim_count=claim_count,
            total_claim_amount=total_claim_amount
        )

        results.append({
            "policy_id": policy_id,
            "expected_claims": expected_claims,
            "expected_severity": expected_severity,
            "claim_count": claim_count,
            "total_claim_amount": total_claim_amount,
        })

    return pd.DataFrame(results)