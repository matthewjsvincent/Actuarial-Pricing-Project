import pandas as pd
from utils.paths import bundled_data_dir


def load_frequency_data():
    return pd.read_csv(bundled_data_dir() / "freMTPL2freq.csv")


def load_severity_data():
    return pd.read_csv(bundled_data_dir() / "freMTPL2sev.csv")