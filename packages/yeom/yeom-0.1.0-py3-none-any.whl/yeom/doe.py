import numpy as np
import pandas as pd
from patsy import dmatrices
from scipy import stats
from scipy.optimize import brenth
from statsmodels.stats.outliers_influence import variance_inflation_factor


def vif(formula, data):
    """Calculate Variance Inflation Factor (VIF) for each feature in the dataset.
    Args:
        formula (str): The formula specifying the model.
        data (pd.DataFrame): The dataset containing the variables.
    Returns:
        pd.DataFrame: A DataFrame containing the VIF for each feature.
    """
    y, X = dmatrices(formula, data, return_type='dataframe')
    table = pd.DataFrame({
        'Feature': X.columns,
        'VIF': [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    })
    return table


def reg_coef_power(
    model,
    variable,
    alpha: float,
    future_n: float = None,
) -> float:
    """Compute power for a regression coefficient given a future sample size.

    Args:
        model: Fitted statsmodels result with `nobs`, `df_resid`, `bse`, `params`.
        variable: Parameter name for which to compute power.
        alpha: Two-sided significance level.
        future_n: Optional future sample size; defaults to current `nobs`.

    Returns:
        Statistical power for detecting the specified coefficient.
    """
    # 1) Compute number of predictors (k = n - df_resid - 1)
    num_predictors = model.nobs - model.df_resid - 1

    # 2) Estimate future degrees of freedom and standard error
    future_n = future_n if future_n is not None else model.nobs
    future_df = future_n - num_predictors - 1
    if future_df <= 0:
        return 0.0  # Not enough degrees of freedom; return zero power
    
    std_error = model.bse[variable]  # Current model standard error
    future_se = std_error * np.sqrt(model.nobs / future_n)

    # 3) Compute noncentrality parameter (nc) using future SE
    coefficient = model.params[variable]  # Estimated coefficient
    nc = abs(coefficient / future_se)

    # 4) Critical value of the t distribution
    tcrit = stats.t.ppf(1 - alpha / 2, df=future_df)

    # 5) Two-sided power under the noncentral t distribution
    power = stats.nct.sf(tcrit, df=future_df, nc=nc) + \
            stats.nct.cdf(-tcrit, df=future_df, nc=nc)
    return power


def find_reg_n(
        model,
        variable: str,
        power: float = 0.8,
        alpha: float = 0.05
) -> float:
    def _eval_n(n):
        return reg_coef_power(model, variable, alpha, future_n=n) - power
    return brenth(_eval_n, a=model.nobs, b=1e6)


def compute_d_optimality(design_matrix):
    # Compute information matrix X'X and its determinant
    information_matrix = np.dot(design_matrix.T, design_matrix)
    det = np.linalg.det(information_matrix)
    return det


def create_initial_design(n, k):
    """Create a random initial n x k design matrix with entries in {-1, 1}."""
    X = np.random.choice([-1, 1], size=(n, k))
    return X


def parse_formula(formula):
    # 1) Parse the formula string into all terms and interaction terms
    all_terms = [term.strip() for term in formula.split('+')]
    main_effects = [term for term in all_terms if ':' not in term]
    term_list = main_effects.copy()

    # 2) Map main-effect names to column indices
    main_effects_map = {name: i for i, name in enumerate(main_effects)}
    # 3) Extract interaction effects as index tuples
    interaction_effects = []
    for term in all_terms:
        if ':' in term:
            factors = term.split(':')
            indices = [main_effects_map[factor.strip()] for factor in factors]
            interaction_effects.append(tuple(indices))
            term_list.append(term.strip())

    return main_effects_map, term_list, interaction_effects


def create_design_matrix(X: np.ndarray, interaction_effects: list) -> pd.DataFrame:
    """Build a design matrix including main and specified interaction effects.

    Args:
        X: n x p array of main-effect runs with entries in {-1, 1}.
        interaction_effects: List of tuples of main-effect indices specifying
            pairwise interactions to include.

    Returns:
        DataFrame of shape n x (p + number_of_interactions) with integer entries.
    """
    n = X.shape[0]  # number of runs
    k = X.shape[1] + len(interaction_effects)
    D = np.zeros((n, k), dtype=int)  # initialize result matrix
    D[:, :X.shape[1]] = X  # place main effects first

    # Compute interaction columns as element‑wise products of main effects
    j = X.shape[1]  # start column for interactions
    for idx1, idx2 in interaction_effects:
        # Interaction as element‑wise product of the two factors
        D[:, j] = X[:, idx1] * X[:, idx2]

    return D


def find_single_d_optimal_design(n, formula, prev_design=None):
    # Parse formula and identify main and interaction terms
    main_effects_map, term_list, interaction_effects = parse_formula(formula)
    k = len(main_effects_map)  # number of main effects
    theoretical_max = n ** (k + 1)  # heuristic upper bound for determinant
    X = create_initial_design(n, k)
    
    # Keep previous design rows fixed if provided
    prev_rows = 0
    if prev_design is not None:
        # main effect term list in the order of term_list
        main_term = [term for term in term_list if ':' not in term]
        prev_design = prev_design[main_term].values  # extract only main effects
        prev_rows, _ = prev_design.shape
        X[:prev_rows, :] = prev_design  # fix the given rows
    
    design_matrix = create_design_matrix(X, interaction_effects)  # build design matrix
    max_det = compute_d_optimality(design_matrix)
    for i in range(prev_rows, n):
        for j in range(k):
            X_improv = X.copy()  # preserve original
            X_improv[i, j] = -X[i, j]  # flip the coordinate
            new_design_matrix = create_design_matrix(X_improv, interaction_effects)
            det = compute_d_optimality(new_design_matrix)  # compute D‑optimality

            if det == theoretical_max:
                new_design_matrix = pd.DataFrame(new_design_matrix, columns=term_list, dtype=int)  # finalize as DataFrame
                return new_design_matrix, theoretical_max, 'max'
            elif det > max_det:
                design_matrix = new_design_matrix  # accept improvement
                max_det = det

    design_matrix = pd.DataFrame(design_matrix, columns=term_list, dtype=int)  # finalize as DataFrame
    return design_matrix, max_det, 'converged'


def coordinate_exchange(n, formula, prev_design=None, iterations=1000):
    best_design = None
    best_det = 0
    for _ in range(iterations):
        design, det, result = find_single_d_optimal_design(n, formula, prev_design=prev_design)
        if result == 'max':
            best_design, best_det = design, det
            break
        elif det > best_det:
            best_design = design
            best_det = det
    if best_det == 0:
        raise ValueError('Cannot find a valid design')
    best_design.sort_values(by=list(best_design.columns), inplace=True, ignore_index=True)  # sort DataFrame rows
    return best_design, best_det


def get_design(data_frame, columns):
    df = data_frame[columns]
    design = df.apply(lambda col: col.map({sorted(col.unique())[0]: -1, sorted(col.unique())[1]: 1}))
    return design

