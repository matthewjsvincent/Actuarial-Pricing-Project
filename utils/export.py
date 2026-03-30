import pandas as pd
from persistence.database import get_all_quotes
from utils.paths import user_data_dir


EXPORT_COLUMNS = [
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


def export_quotes_to_csv(file_path=None):
    if file_path is None:
        file_path = user_data_dir() / "quotes_export.csv"

    rows = get_all_quotes()

    if not rows:
        df = pd.DataFrame(columns=EXPORT_COLUMNS)
    else:
        df = pd.DataFrame(rows, columns=EXPORT_COLUMNS)

    df.to_csv(file_path, index=False)

    return str(file_path)