import pandas as pd

from utils.dates import calculate_vehicle_age
from persistence.database import roll_forward_portfolio_in_place


def _update_bonus_malus(current_bonus_malus: float, claim_count: int) -> float:
    value = float(current_bonus_malus)

    if claim_count == 0:
        value *= 0.98
    elif claim_count == 1:
        value *= 1.10
    else:
        value *= 1.25

    return max(50.0, min(value, 200.0))


def build_roll_forward_updates(latest_policies, claims_rows, simulation_year: int):
    claims_lookup = {
        row[0]: {
            "simulation_year": row[1],
            "had_claim": row[2],
            "claim_count": row[3],
            "total_claim_amount": row[4],
        }
        for row in claims_rows
    }

    results = []

    for row in latest_policies:
        policy_id = row[0]
        customer_id = row[1]
        policy_name = row[2]
        exposure = float(row[3])
        vehicle_year = int(row[4])
        current_pricing_year = int(row[5])
        current_policy_year = int(row[6])
        current_veh_age = float(row[7])
        current_driv_age = float(row[8])
        current_bonus_malus = float(row[9])
        density = float(row[10])
        veh_gas = str(row[11])
        veh_brand = str(row[12])
        region = str(row[13])
        area = str(row[14])
        no_accident_years = int(row[15])
        accident_count_recent = int(row[16])

        claim_info = claims_lookup.get(policy_id)
        claim_count = 0 if claim_info is None else int(claim_info["claim_count"])

        next_pricing_year = max(current_pricing_year, simulation_year) + 1
        next_policy_year = max(current_policy_year, simulation_year) + 1
        next_driv_age = current_driv_age + 1
        next_veh_age = calculate_vehicle_age(vehicle_year, next_pricing_year)

        if claim_count == 0:
            next_no_accident_years = no_accident_years + 1
        else:
            next_no_accident_years = 0

        next_accident_count_recent = min(claim_count, 3)
        next_bonus_malus = _update_bonus_malus(current_bonus_malus, claim_count)

        results.append({
            "policy_id": policy_id,
            "customer_id": customer_id,
            "policy_name": policy_name,
            "exposure": exposure,
            "vehicle_year": vehicle_year,
            "current_pricing_year": current_pricing_year,
            "current_policy_year": current_policy_year,
            "current_veh_age": current_veh_age,
            "current_driv_age": current_driv_age,
            "current_bonus_malus": current_bonus_malus,
            "density": density,
            "veh_gas": veh_gas,
            "veh_brand": veh_brand,
            "region": region,
            "area": area,
            "old_no_accident_years": no_accident_years,
            "old_accident_count_recent": accident_count_recent,
            "claim_count": claim_count,
            "next_pricing_year": next_pricing_year,
            "next_policy_year": next_policy_year,
            "next_veh_age": next_veh_age,
            "next_driv_age": next_driv_age,
            "next_bonus_malus": next_bonus_malus,
            "next_no_accident_years": next_no_accident_years,
            "next_accident_count_recent": next_accident_count_recent,
        })

    return results


def roll_forward_one_year(simulation_year: int):
    """
    Snapshot the current active portfolio for the selected simulation year,
    then update active policies in place for the next year.
    """
    df, summary = roll_forward_portfolio_in_place(
        simulation_year=simulation_year,
        update_bonus_malus_fn=_update_bonus_malus,
    )

    return df, summary