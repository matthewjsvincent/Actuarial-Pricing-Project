def apply_experience_rating(
    premium: float,
    no_accident_years: int = 0,
    accident_count_recent: int = 0
) -> float:
    adjusted = premium

    # No-claim discount
    if no_accident_years >= 4 and accident_count_recent == 0:
        adjusted *= 0.90  # 10% discount

    # Surcharges
    if accident_count_recent == 1:
        adjusted *= 1.10
    elif accident_count_recent == 2:
        adjusted *= 1.25
    elif accident_count_recent >= 3:
        adjusted *= 1.50

    return adjusted