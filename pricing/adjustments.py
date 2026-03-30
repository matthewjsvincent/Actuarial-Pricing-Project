def calculate_technical_premium(
    expected_loss: float,
    expense_ratio: float = 0.25,
    profit_margin: float = 0.10
) -> float:
    """
    expected_loss: pure premium / expected claims cost
    expense_ratio: percentage of premium consumed by expenses
    profit_margin: target profit as percentage of premium
    """
    denominator = 1.0 - expense_ratio - profit_margin

    if denominator <= 0:
        raise ValueError("Expense ratio + profit margin must be less than 1.")

    return expected_loss / denominator