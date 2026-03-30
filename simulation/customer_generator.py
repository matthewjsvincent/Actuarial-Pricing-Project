import random

from utils.dates import calculate_vehicle_age
from persistence.database import (
    create_customer,
    create_policy,
    create_simulation_batch,
    update_simulation_batch_counts,
)

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Jamie", "Riley",
    "Cameron", "Drew", "Logan", "Avery", "Harper", "Blake", "Parker"
]

LAST_NAMES = [
    "Smith", "Johnson", "Brown", "Jones", "Miller", "Davis",
    "Garcia", "Wilson", "Anderson", "Thomas", "Martin", "White"
]

VEH_GAS_OPTIONS = ["Diesel", "Regular"]
VEH_BRAND_OPTIONS = ["B1", "B2", "B3", "B4", "B5", "B6", "B10", "B11", "B12", "B13", "B14"]
REGION_OPTIONS = [
    "R11", "R21", "R22", "R23", "R24", "R25",
    "R31", "R41", "R42", "R43", "R52", "R53",
    "R54", "R72", "R73", "R74", "R82", "R83",
    "R91", "R93", "R94"
]
AREA_OPTIONS = ["A", "B", "C", "D", "E", "F"]


def sample_policy_count_for_customer():
    return random.choices(
        population=[1, 2, 3],
        weights=[0.70, 0.22, 0.08],
        k=1
    )[0]


def _random_customer_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _random_email(full_name, unique_id):
    return f"{full_name.lower().replace(' ', '.')}{unique_id}@example.com"


def _random_phone():
    return f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


def generate_customers_and_policies_to_target(
    n_policies: int,
    pricing_year: int,
    batch_name: str = "Simulated Portfolio Batch"
):
    if n_policies <= 0:
        raise ValueError("n_policies must be greater than 0.")

    batch_id = create_simulation_batch(
        batch_name=batch_name,
        pricing_year=pricing_year,
        target_policy_count=n_policies
    )

    created_customers = 0
    created_policies = 0
    customer_sequence = 1

    while created_policies < n_policies:
        full_name = _random_customer_name()
        email = _random_email(full_name, customer_sequence)
        phone = _random_phone()

        customer_id = create_customer(full_name, email, phone)

        created_customers += 1
        customer_sequence += 1

        policy_count = sample_policy_count_for_customer()
        remaining = n_policies - created_policies
        policy_count = min(policy_count, remaining)

        for policy_num in range(1, policy_count + 1):
            vehicle_year = random.randint(2005, pricing_year)
            veh_age = calculate_vehicle_age(vehicle_year, pricing_year)

            create_policy(
                customer_id=customer_id,
                policy_name=f"Policy {policy_num} - {vehicle_year} Vehicle",
                exposure=round(random.uniform(0.5, 1.0), 2),
                vehicle_year=vehicle_year,
                pricing_year=pricing_year,
                policy_year=pricing_year,
                veh_age=veh_age,
                driv_age=random.randint(18, 85),
                bonus_malus=random.randint(50, 150),
                density=random.randint(1, 5000),
                veh_gas=random.choice(VEH_GAS_OPTIONS),
                veh_brand=random.choice(VEH_BRAND_OPTIONS),
                region=random.choice(REGION_OPTIONS),
                area=random.choice(AREA_OPTIONS),
                no_accident_years=random.choice([0, 0, 1, 2, 3, 4, 5]),
                accident_count_recent=random.choice([0, 0, 0, 1, 1, 2, 3]),
                source_policy_id=None,
            )

            created_policies += 1

    update_simulation_batch_counts(
        batch_id=batch_id,
        created_customer_count=created_customers,
        created_policy_count=created_policies
    )

    return {
        "batch_id": batch_id,
        "created_customers": created_customers,
        "created_policies": created_policies,
    }