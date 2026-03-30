# Actuarial Pricing Application

A Python-based actuarial pricing and portfolio simulation tool designed for learning and experimentation with insurance pricing models, portfolio forecasting, and actuarial workflows.

## 🚀 Overview

This application simulates a full actuarial pricing pipeline, including:

- Customer and policy management
- Frequency and severity modeling (GLM-based)
- Premium calculation (technical + final premium)
- Portfolio forecasting
- Claims simulation
- Year-end roll-forward with snapshot history
- Model retraining dataset generation

It is built with a **Tkinter GUI**, **SQLite database**, and **statistical models using statsmodels**.

---

## 🧠 Key Features

### 📊 Pricing Engine
- Poisson GLM for claim frequency
- Severity modeling
- Expected loss calculation
- Inflation and expense/profit loading
- Final premium output

### 📁 Portfolio Management
- Create and manage customers and policies
- Generate synthetic portfolios
- Search, update, and delete records

### 🔮 Forecasting
- Forecast premiums for the entire active portfolio
- Real-time progress tracking and status updates
- Summary statistics (total premium, averages, etc.)

### 🎲 Simulation
- Simulate annual claims using stochastic processes
- Generate claim counts and loss amounts

### 🔁 Year-End Roll Forward
- Snapshot current portfolio state
- Update active policies in place for the next year
- Preserve historical data for review

### 📚 Retraining Pipeline
- Build datasets from simulated experience
- Retrain frequency and severity models

### 📈 Analytics
- Portfolio summaries
- Premium distributions
- Customer-level insights

---

### 🏗️ Project Structure
Actuarial Pricing Project/
│
├── gui/ # Tkinter UI
├── persistence/ # Database layer (SQLite)
├── pricing/ # Premium calculations
├── models/ # Frequency & severity models
├── simulation/ # Portfolio simulation & roll-forward
├── analytics/ # Reporting and summaries
├── utils/ # Shared utilities
├── data/ # Input datasets
├── app_data/ # Generated DB + artifacts
└── main.py # Application entry point


---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/actuarial-pricing-app.git
cd actuarial-pricing-app

### 2. Create virtual environment

python -m venv .venv
.venv\Scripts\activate   # Windows
# or
source .venv/bin/activate  # Mac/Linux

### 3. Install dependencies

pip install -r requirements.txt

### 4. Running the Application

python main.py

---

This will:

initialize the database
load training data
train or load models
launch the GUI

---

🧪 Intended Use

This project is designed for:

Learning actuarial pricing concepts
Experimenting with GLMs and insurance data
Understanding portfolio lifecycle workflows
Practicing Python application architecture

It is not intended for production insurance use.

🔧 Future Improvements

Planned enhancements include:

Snapshot review / history UI
Improved dashboards and visualizations
Model performance metrics and validation
Service-layer refactoring
Automated tests
API deployment (Flask / FastAPI)

📜 License

This project is licensed under the MIT License. See the LICENSE file for details.

👤 Author

Matthew Vincent

🙌 Acknowledgements
Open-source actuarial datasets (freMTPL2)
Python scientific stack (pandas, numpy, statsmodels)



