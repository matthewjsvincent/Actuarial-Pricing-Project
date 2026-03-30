import pandas as pd
from persistence.database import get_all_quotes


QUOTE_COLUMNS = [
    "id",
    "policy_id",
    "customer_name",
    "policy_name",
    "expected_claims",
    "expected_severity",
    "expected_loss",
    "inflated_loss",
    "technical_premium",
    "final_premium",
    "created_at",
]


def get_quotes_dataframe():
    rows = get_all_quotes()

    if not rows:
        return pd.DataFrame(columns=QUOTE_COLUMNS)

    df = pd.DataFrame(rows, columns=QUOTE_COLUMNS)

    numeric_columns = [
        "expected_claims",
        "expected_severity",
        "expected_loss",
        "inflated_loss",
        "technical_premium",
        "final_premium",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_portfolio_summary():
    df = get_quotes_dataframe()

    if df.empty:
        return {
            "count": 0,
            "total_expected_loss": 0.0,
            "total_inflated_loss": 0.0,
            "total_final_premium": 0.0,
            "avg_final_premium": 0.0,
        }

    return {
        "count": int(len(df)),
        "total_expected_loss": float(df["expected_loss"].sum()),
        "total_inflated_loss": float(df["inflated_loss"].sum()),
        "total_final_premium": float(df["final_premium"].sum()),
        "avg_final_premium": float(df["final_premium"].mean()),
    }


def get_average_final_premium_by_customer():
    df = get_quotes_dataframe()

    if df.empty:
        return pd.DataFrame(columns=["customer_name", "final_premium"])

    grouped = (
        df.groupby("customer_name", as_index=False)["final_premium"]
        .mean()
        .sort_values("final_premium", ascending=False)
    )

    return grouped


def get_average_premium_by_customer():
    return None