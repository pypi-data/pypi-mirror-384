import numpy as np
import pandas as pd
import pyEDM
import pytest

from edmkit import generate
from edmkit.embedding import lagged_embed
from edmkit.simplex_projection import simplex_projection


@pytest.fixture
def logistic_map(n: int = 200):
    """Generate logistic map time series x."""
    x = np.zeros(n)
    x[0] = 0.1
    # Logistic map
    for i in range(1, n):
        x[i] = 3.8 * x[i - 1] * (1 - x[i - 1])
    return x


@pytest.fixture
def lorenz(n: int = 200):
    """Generate Lorenz attractor time series x."""
    sigma, rho, beta = 10, 28, 8 / 3
    X0 = np.array([1.0, 1.0, 1.0])
    t_max = 30
    dt = t_max / (n * 10)  # Generate enough points before subsampling

    t, X = generate.lorenz(sigma, rho, beta, X0, dt, t_max)
    return X[::10, 0][:n]  # Ensure we get exactly n points


@pytest.fixture
def mackey_glass(n: int = 200):
    """Generate Mackey-Glass time series x."""
    tau, n_exponent = 17, 10
    beta, gamma = 0.2, 0.1
    x0 = 0.9
    t_max = 200
    dt = t_max / n

    t, x = generate.mackey_glass(tau, n_exponent, beta, gamma, x0, dt, t_max)
    return x


@pytest.mark.parametrize(
    "data,E,tau",
    [
        ("logistic_map", 3, 2),
        ("lorenz", 3, 1),
        ("mackey_glass", 4, 2),
    ],
)
def test_simplex_projection(data, E, tau, request):
    """Test simplex projection against pyEDM with various time series data."""
    x = request.getfixturevalue(data)

    # common parameters
    lib_size = 150
    Tp = 2

    # pyEDM
    df = pd.DataFrame({"time": np.arange(len(x)), "value": x})
    lib, pred = f"1 {lib_size}", f"{lib_size + 1} {len(x)}"
    pyedm_result = pyEDM.Simplex(dataFrame=df, lib=lib, pred=pred, E=E, tau=-tau, columns="value", target="value", Tp=Tp, verbose=False)
    pyedm_predictions = pyedm_result["Predictions"].values[Tp:-Tp]  # first Tp values are NaN, last Tp values are not in true x

    # edmkit
    embedding = lagged_embed(x, tau, E)
    shift = tau * (E - 1)  # embedding starts at this index (i.e. embedding[0][0] == x[shift])
    X = embedding[: lib_size - shift]
    Y = embedding[Tp : lib_size - shift + Tp, 0]  # shifted by Tp

    query_points = embedding[lib_size - shift :]
    edmkit_predictions = simplex_projection(X, Y, query_points)[:-Tp]  # last Tp values are not in true x

    ground_truth = x[lib_size + Tp :]
    pyedm_rmse = np.sqrt(np.mean((pyedm_predictions - ground_truth) ** 2))
    edmkit_rmse = np.sqrt(np.mean((edmkit_predictions - ground_truth) ** 2))

    assert np.abs(pyedm_rmse - edmkit_rmse) < 1e-6, f"RMSE: pyEDM {pyedm_rmse}, edmkit {edmkit_rmse}, diff {np.abs(pyedm_rmse - edmkit_rmse)}"
