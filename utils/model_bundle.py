from pathlib import Path
import joblib

from utils.paths import user_data_dir
from utils.data_loader import load_frequency_data, load_severity_data
from models.frequency_model import train_frequency_model
from models.severity_model import train_severity_model


ARTIFACT_DIR = user_data_dir() / "artifacts"
FREQ_MODEL_PATH = ARTIFACT_DIR / "freq_model.pkl"
SEV_MODEL_PATH = ARTIFACT_DIR / "sev_model.pkl"


class ModelBundle:
    def __init__(self):
        self.freq_artifact = None
        self.sev_artifact = None

    def _artifacts_are_compatible(self):
        if self.freq_artifact is None or self.sev_artifact is None:
            return False

        required_keys = {"model", "columns", "category_levels"}

        return (
            required_keys.issubset(self.freq_artifact.keys()) and
            required_keys.issubset(self.sev_artifact.keys())
        )

    def load_models(self, force_retrain: bool = False):
        ARTIFACT_DIR.mkdir(exist_ok=True)

        if not force_retrain and FREQ_MODEL_PATH.exists() and SEV_MODEL_PATH.exists():
            self.freq_artifact = joblib.load(FREQ_MODEL_PATH)
            self.sev_artifact = joblib.load(SEV_MODEL_PATH)

            if self._artifacts_are_compatible():
                return

        freq_data = load_frequency_data()
        sev_data = load_severity_data()

        self.freq_artifact = train_frequency_model(freq_data)
        self.sev_artifact = train_severity_model(freq_data, sev_data)

        joblib.dump(self.freq_artifact, FREQ_MODEL_PATH)
        joblib.dump(self.sev_artifact, SEV_MODEL_PATH)

    def retrain_from_dataframes(self, freq_df, sev_df):
        if freq_df is None or freq_df.empty:
            raise ValueError("Frequency retraining dataframe is empty.")

        if "ClaimNb" not in freq_df.columns or freq_df["ClaimNb"].sum() <= 0:
            raise ValueError("Frequency retraining dataframe contains no claims.")

        if sev_df is None or sev_df.empty:
            raise ValueError("Severity retraining dataframe is empty.")

        ARTIFACT_DIR.mkdir(exist_ok=True)

        self.freq_artifact = train_frequency_model(freq_df)
        self.sev_artifact = train_severity_model(freq_df, sev_df)

        joblib.dump(self.freq_artifact, FREQ_MODEL_PATH)
        joblib.dump(self.sev_artifact, SEV_MODEL_PATH)

    def is_ready(self):
        return self.freq_artifact is not None and self.sev_artifact is not None

    @property
    def freq_model(self):
        return self.freq_artifact["model"]

    @property
    def sev_model(self):
        return self.sev_artifact["model"]

    @property
    def freq_columns(self):
        return self.freq_artifact["columns"]

    @property
    def sev_columns(self):
        return self.sev_artifact["columns"]

    @property
    def freq_category_levels(self):
        return self.freq_artifact["category_levels"]

    @property
    def sev_category_levels(self):
        return self.sev_artifact["category_levels"]