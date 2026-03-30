import tkinter as tk

from persistence.database import init_db
from utils.model_bundle import ModelBundle
from utils.data_loader import load_frequency_data
from utils.logger import logger
from gui.app import PricingApp


def main():
    logger.log("Starting application")

    init_db()
    logger.log("Database initialized")

    freq_data = load_frequency_data()
    logger.log("Frequency data loaded")

    model_bundle = ModelBundle()
    logger.log("Loading models...")

    model_bundle.load_models(force_retrain=False)

    logger.log("Models ready")

    root = tk.Tk()
    app = PricingApp(root, model_bundle, freq_data)
    logger.log("GUI initialized")

    root.mainloop()


if __name__ == "__main__":
    main()