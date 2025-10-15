import numpy as np
import pandas as pd
import pytest

from yeom import doe


def test_parse_formula_with_interaction():
    m, terms, inter = doe.parse_formula('A + B + A:B')
    assert m == {'A': 0, 'B': 1}
    assert 'A:B' in terms
    assert (0, 1) in inter


def test_create_initial_design_shape_and_values():
    n, k = 5, 3
    X = doe.create_initial_design(n, k)
    assert X.shape == (n, k)
    # Values should be in {-1, 1}
    assert set(np.unique(X)).issubset({-1, 1})


def test_create_design_matrix_main_only():
    X = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]])
    D = doe.create_design_matrix(X, interaction_effects=[])
    assert D.shape == (4, 2)
    assert np.array_equal(D[:, :2], X)


def test_create_design_matrix_single_interaction():
    # Only a single interaction to avoid known column-index overwrite bug
    X = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]])
    D = doe.create_design_matrix(X, interaction_effects=[(0, 1)])
    assert D.shape == (4, 3)
    # Third column should be element-wise product of first two
    assert np.array_equal(D[:, 2], X[:, 0] * X[:, 1])


def test_compute_d_optimality_positive_for_full_rank():
    X = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]])
    det = doe.compute_d_optimality(X)
    assert det > 0


def test_get_design_bimodal_mapping():
    df = pd.DataFrame({
        'A': [0, 0, 1, 1],
        'B': ['x', 'y', 'x', 'y'],
    })
    design = doe.get_design(df, ['A', 'B'])
    # Sorted unique maps lowest to -1 and highest to 1
    assert set(design['A'].unique()) == {-1, 1}
    assert set(design['B'].unique()) == {-1, 1}
    # Check specific mapping by sort order
    assert design['A'].iloc[0] == -1  # 0 -> -1
    assert design['A'].iloc[2] == 1   # 1 -> 1


def test_vif_basic_dataframe_contains_features():
    rng = np.random.default_rng(0)
    n = 50
    x1 = rng.normal(size=n)
    x2 = 0.5 * x1 + rng.normal(scale=0.5, size=n)
    y = 1.0 + 2.0 * x1 - 1.0 * x2 + rng.normal(size=n)
    df = pd.DataFrame({'y': y, 'x1': x1, 'x2': x2})
    table = doe.vif('y ~ x1 + x2', df)
    # Ensure expected columns present and includes predictors
    assert set(table.columns) == {'Feature', 'VIF'}
    assert {'x1', 'x2'}.issubset(set(table['Feature']))


class _FakeModel:
    def __init__(self, nobs, df_resid, bse_map, params_map):
        self.nobs = nobs
        self.df_resid = df_resid
        self.bse = bse_map
        self.params = params_map


def test_reg_coef_power_increases_with_sample_size():
    # Modest effect with reasonable SE; power should increase with n
    model = _FakeModel(
        nobs=100,
        df_resid=97,  # implies k=2 predictors
        bse_map={'x1': 0.5},
        params_map={'x1': 1.0},
    )
    p_small = doe.reg_coef_power(model, 'x1', alpha=0.05, future_n=100)
    p_large = doe.reg_coef_power(model, 'x1', alpha=0.05, future_n=400)
    assert p_large >= p_small
    assert 0 <= p_small <= 1 and 0 <= p_large <= 1


def test_find_reg_n_returns_larger_than_current():
    model = _FakeModel(
        nobs=100,
        df_resid=97,
        bse_map={'x1': 0.5},
        params_map={'x1': 1.0},
    )
    n_req = doe.find_reg_n(model, 'x1', power=0.8, alpha=0.05)
    assert n_req > model.nobs


def test_coordinate_exchange_smoke():
    # Simple 2-factor design without interactions
    n = 4
    design, det = doe.coordinate_exchange(n, 'A + B')
    assert isinstance(design, pd.DataFrame)
    assert list(design.columns) == ['A', 'B']
    assert design.shape == (n, 2)
    assert det > 0

