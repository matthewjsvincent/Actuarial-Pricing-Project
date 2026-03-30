from datetime import datetime


def get_pricing_year():
    return datetime.now().year


def get_current_year() -> int:
    return datetime.now().year


def calculate_vehicle_age(vehicle_year: int, pricing_year: int | None = None) -> int:
    if pricing_year is None:
        pricing_year = get_current_year()

    age = pricing_year - vehicle_year
    return max(age, 0)