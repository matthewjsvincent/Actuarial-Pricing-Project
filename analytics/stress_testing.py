import random

def run_stress_scenarios(base_expected_loss: float):
    scenarios = {
        "best_case": {
            "frequency_multiplier": 0.90,
            "severity_multiplier": 0.90,
        },
        "base_case": {
            "frequency_multiplier": 1.00,
            "severity_multiplier": 1.00,
        },
        "adverse_case": {
            "frequency_multiplier": 1.10,
            "severity_multiplier": 1.20,
        },
        "worst_case": {
            "frequency_multiplier": 1.25,
            "severity_multiplier": 1.40,
        },
    }

    results = {}

    for name, params in scenarios.items():
        shocked_loss = (
            base_expected_loss
            * params["frequency_multiplier"]
            * params["severity_multiplier"]
        )
        results[name] = shocked_loss

    return results

def random_stress_test(base_expected_loss: float, n_sims: int = 1000):
    results = []

    for _ in range(n_sims):
        freq_shock = random.uniform(0.85, 1.30)
        sev_shock = random.uniform(0.85, 1.50)

        stressed_loss = base_expected_loss * freq_shock * sev_shock
        results.append(stressed_loss)

    return results