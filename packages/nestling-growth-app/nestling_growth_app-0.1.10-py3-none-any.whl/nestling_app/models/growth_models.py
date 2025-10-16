import numpy as np
from scipy.optimize import curve_fit


# 📌 Growth Models
def logistic(x, a, k, x0):
    return a / (1 + np.exp(-k * (x - x0)))


def gompertz(x, a, b, c):
    return a * np.exp(-b * np.exp(-c * x))


def richards(x, a, k, x0, v):
    return a / (1 + np.exp(-k * (x - x0))) ** (1 / v)


def von_bertalanffy(x, l_inf, k, t0):
    return l_inf * (1 - np.exp(-k * (x - t0)))


def evf(x, a, b, c, d):
    return a * np.exp(-b * np.exp(-c * x)) * (1 - np.exp(-d * x))


# 📌 AIC and BIC Calculation
def calculate_aic_bic(y_true, y_pred, params):
    n = len(y_true)
    residuals = y_true - y_pred
    sse = np.sum(residuals ** 2)
    k = len(params)

    aic = n * np.log(sse / n) + 2 * k
    bic = n * np.log(sse / n) + k * np.log(n)

    return aic, bic


# 📌 Fit Models and Evaluate
def fit_models(x_data, y_data):
    models = {
        "Logistic": (logistic, [max(y_data), 1, np.median(x_data)]),
        "Gompertz": (gompertz, [max(y_data), 1, 0.1]),
        "Richards": (richards, [max(y_data), 1, np.median(x_data), 1]),
        "Von Bertalanffy": (von_bertalanffy, [max(y_data), 0.1, min(x_data)]),
        "Extreme Value Function": (evf, [max(y_data), 1, 0.1, 0.1])
    }

    results = []
    print("📦 Starting model fitting...")

    for model_name, (model_func, initial_params) in models.items():
        try:
            print(f"🔍 Trying model: {model_name}")
            popt, _ = curve_fit(model_func, x_data, y_data, p0=initial_params, maxfev=10000)
            y_pred = model_func(x_data, *popt)
            aic, bic = calculate_aic_bic(y_data, y_pred, popt)

            # Growth rate and inflection point
            if model_name == "Logistic":
                k_value, T_value = popt[1], popt[2]
            elif model_name == "Gompertz":
                k_value, T_value = popt[2], np.log(popt[1]) / popt[2]
            elif model_name == "Richards":
                k_value, T_value = popt[1], popt[2]
            elif model_name == "Von Bertalanffy":
                k_value, T_value = popt[1], popt[2]
            elif model_name == "Extreme Value Function":
                k_value, T_value = popt[2], np.log(popt[1]) / popt[2]
            else:
                k_value, T_value = None, None

            results.append((model_name, popt, aic, bic, k_value, T_value))
            print(f"✅ Success: {model_name} — AIC: {aic:.2f}, k: {k_value:.4f}, T: {T_value:.2f}")

        except Exception as e:
            print(f"❌ Error with {model_name}: {e}")

    if not results:
        print("🚫 No models could be fitted.")
        return None, None

    results.sort(key=lambda x: x[2])
    best_aic = results[0][2]
    results = [(m, p, aic, bic, k, T, aic - best_aic) for (m, p, aic, bic, k, T) in results]

    print(f"🏆 Best model: {results[0][0]} with ΔAIC = 0.0")
    return results[0], results