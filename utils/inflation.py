def apply_inflation(amount: float, annual_inflation_rate: float = 0.03, years: int = 1) -> float:
    return amount * ((1 + annual_inflation_rate) ** years)