import pandas as pd
import numpy as np


FREQ_NUMERIC_COLUMNS = [
    "Exposure",
    "VehAge",
    "DrivAge",
    "BonusMalus",
    "Density",
]

FREQ_CATEGORICAL_COLUMNS = [
    "VehGas",
    "VehBrand",
    "Region",
    "Area",
]

SEV_NUMERIC_COLUMNS = [
    "VehAge",
    "DrivAge",
    "BonusMalus",
    "Density",
]

SEV_CATEGORICAL_COLUMNS = [
    "VehGas",
    "VehBrand",
    "Region",
    "Area",
]


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    return df.dropna()


def extract_category_levels(df: pd.DataFrame, categorical_columns: list[str]) -> dict:
    levels = {}
    for col in categorical_columns:
        levels[col] = sorted(df[col].astype(str).dropna().unique().tolist())
    return levels


def _build_categorical_dummies(
    df: pd.DataFrame,
    categorical_columns: list[str],
    category_levels: dict | None = None
) -> pd.DataFrame:
    dummy_frames = []

    for col in categorical_columns:
        values = df[col].astype(str)

        if category_levels is not None and col in category_levels:
            values = pd.Series(
                pd.Categorical(values, categories=category_levels[col]),
                index=df.index,
                name=col
            )
        else:
            values = pd.Series(values, index=df.index, name=col)

        dummies = pd.get_dummies(
            values,
            prefix=col,
            drop_first=True,
            dtype=float
        )

        # Extra safety: preserve original index
        dummies.index = df.index
        dummy_frames.append(dummies)

    if dummy_frames:
        result = pd.concat(dummy_frames, axis=1)
        result.index = df.index
        return result

    return pd.DataFrame(index=df.index)


def build_frequency_design_matrix(
    df: pd.DataFrame,
    category_levels: dict | None = None
) -> pd.DataFrame:
    df = df.copy()

    numeric_df = df[FREQ_NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")
    numeric_df.index = df.index

    categorical_df = _build_categorical_dummies(
        df,
        FREQ_CATEGORICAL_COLUMNS,
        category_levels=category_levels
    )

    X = pd.concat([numeric_df, categorical_df], axis=1)
    X = X.apply(pd.to_numeric, errors="coerce")
    return X.astype(float)


def build_severity_design_matrix(
    df: pd.DataFrame,
    category_levels: dict | None = None
) -> pd.DataFrame:
    df = df.copy()

    numeric_df = df[SEV_NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")
    numeric_df.index = df.index

    categorical_df = _build_categorical_dummies(
        df,
        SEV_CATEGORICAL_COLUMNS,
        category_levels=category_levels
    )

    X = pd.concat([numeric_df, categorical_df], axis=1)
    X = X.apply(pd.to_numeric, errors="coerce")
    return X.astype(float)


def align_to_training_columns(X: pd.DataFrame, training_columns: list[str]) -> pd.DataFrame:
    X = X.copy()
    X = X.reindex(columns=training_columns, fill_value=0)
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return X.astype(float)