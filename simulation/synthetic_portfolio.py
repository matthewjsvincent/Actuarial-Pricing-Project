import random
import pandas as pd


def generate_synthetic_portfolio(n=5000, pricing_year=2026):
    veh_gas_options = ["Diesel", "Regular"]
    veh_brand_options = ["B1", "B2", "B3", "B4", "B5", "B6", "B10", "B11", "B12", "B13", "B14"]
    region_options = [
        "R11", "R21", "R22", "R23", "R24", "R25",
        "R31", "R41", "R42", "R43", "R52", "R53",
        "R54", "R72", "R73", "R74", "R82", "R83",
        "R91", "R93", "R94"
    ]
    area_options = ["A", "B", "C", "D", "E", "F"]

    rows = []

    for _ in range(n):
        vehicle_year = random.randint(2005, pricing_year)
        veh_age = max(pricing_year - vehicle_year, 0)

        row = {
            "Exposure": round(random.uniform(0.5, 1.0), 2),
            "VehicleYear": vehicle_year,
            "PricingYear": pricing_year,
            "VehAge": veh_age,
            "DrivAge": random.randint(18, 85),
            "BonusMalus": random.randint(50, 150),
            "Density": random.randint(1, 5000),
            "VehGas": random.choice(veh_gas_options),
            "VehBrand": random.choice(veh_brand_options),
            "Region": random.choice(region_options),
            "Area": random.choice(area_options),
            "NoAccidentYears": random.choice([0, 0, 1, 2, 3, 4, 5]),
            "AccidentCountRecent": random.choice([0, 0, 0, 1, 1, 2, 3]),
        }
        rows.append(row)

    return pd.DataFrame(rows)