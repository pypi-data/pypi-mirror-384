import numpy as np
from scipy.optimize import fsolve
import warnings
from numba import njit
from .ReactionSys import ReactionSys

# This function solves the system of n equations of n monomeric proteins
# k_on is the dimerization rate matrix (numpy 2Darray, n x n)
# k_off is the dissociation rate matrix (numpy 2Darray, n x n)
# production is the production rate vector (numpy 1Darray, n)
# mono_degradation_rate is the monomer degradation rate vector (numpy 1Darray, n)
# dimer_degradation_rate is the dimer degradation rate vector (numpy 2Darray, n x n)
# Returns the steady-state concentration vector (numpy 1Darray, n)
def _MonoSolve(k_on: np.ndarray, k_off: np.ndarray, production: np.ndarray, mono_degradation_rate: np.ndarray, dimer_degradation_rate: np.ndarray, init_iterations: int) -> np.ndarray:

    numerator = dimer_degradation_rate * k_on
    coefficients = np.divide(numerator, np.add(k_off, dimer_degradation_rate))

    # homodimerization terms should be corrected with a factor of 2
    np.fill_diagonal(coefficients, np.diag(coefficients) * 2)

    def equations(concentrations):
        ans = np.sum(np.multiply(coefficients, concentrations[:, np.newaxis]), axis=0) * concentrations + mono_degradation_rate * concentrations - production
        return ans

    # considering no hetrodimerization, take the analytical solution of each monomer as the initial guess:
    # initial_guess = DecoupledGuess(coefficients, production, mono_degradation_rate)
    initial_guess = SequentialGuess(coefficients, production, mono_degradation_rate, iterations=init_iterations)
    # initial_guess = np.ones(len(production))
    # print ("Initial guess:", initial_guess)
    with warnings.catch_warnings():
        warnings.filterwarnings('error', category=RuntimeWarning)
        try:
            steady_state = fsolve(equations, initial_guess)
        except RuntimeWarning as e:
            raise RuntimeError("fsolve failed to converge: " + str(e))

    return steady_state

# wrapper function
def MonoSolve(reaction_sys: ReactionSys, init_iterations:int =100) -> np.ndarray:
    return _MonoSolve(reaction_sys.k_on, reaction_sys.k_off, reaction_sys.production, reaction_sys.mono_degradation, reaction_sys.dimer_degradation, init_iterations)

# analytical solution of each monomer as the initial guess
def DecoupledGuess(coefficients, production, mono_degradation_rate):
    """
    Analytical solution of each monomer as the initial guess.
    Assumes no heterodimerization.
    """
    diag_coeff = np.diag(coefficients)
    initial_guess = np.empty_like(production, dtype=float)

    mask = diag_coeff > 0
    # Only compute where diag_coeff > 0
    sqrt_term = np.sqrt(mono_degradation_rate[mask]**2 + 4 * diag_coeff[mask] * production[mask])
    initial_guess[mask] = (-mono_degradation_rate[mask] + sqrt_term) / (2 * diag_coeff[mask])
    # For diag_coeff == 0, use production / mono_degradation_rate
    initial_guess[~mask] = production[~mask] / mono_degradation_rate[~mask]

    return initial_guess

# iterative update of the analytical solution as the initial guess
@njit
def sequential_guess_numba(coefficients, production, mono_degradation_rate, diag_coeff, mask, mask_eye, init_guess, iterations):
    for _ in range(iterations):
        b = np.sum(coefficients * init_guess * mask_eye, axis=1) + mono_degradation_rate
        sqrt_term = np.sqrt(b**2 + 4 * diag_coeff * production)
        for i in range(len(init_guess)):
            if mask[i]:
                init_guess[i] = (-b[i] + sqrt_term[i]) / (2 * diag_coeff[i])
            else:
                init_guess[i] = production[i] / b[i]
    return init_guess

# iterative update of the analytical solution as the initial guess
def SequentialGuess(coefficients, production, mono_degradation_rate, iterations=10):
    """
    Iterative update of the analytical solution as the initial guess.
    """
    init_guess = DecoupledGuess(coefficients, production, mono_degradation_rate)
    diag_coeff = np.diag(coefficients)
    mask = diag_coeff > 0
    mask_eye = ~np.eye(len(init_guess), dtype=bool)
    # Call the numba-accelerated function
    return sequential_guess_numba(coefficients, production, mono_degradation_rate, diag_coeff, mask, mask_eye, init_guess, iterations)

def DimerSolve(mono_conc: np.ndarray,reaction_sys: ReactionSys) -> np.ndarray:
    dimer_conc = np.zeros(len(reaction_sys.dimers))
    for i, (a, b) in enumerate(reaction_sys.dimers):
        dimer_conc[i] = reaction_sys.k_on[a, b] * mono_conc[a] * mono_conc[b] / (reaction_sys.k_off[a, b] + reaction_sys.dimer_degradation[a, b])
    return dimer_conc

# Example usage:
if __name__ == "__main__":
    reaction_sys = ReactionSys('ExampleReaction.json')
    steady_state_concentrations = MonoSolve(reaction_sys)
    print("Steady-state concentrations:", steady_state_concentrations)
    dimer_concentrations = DimerSolve(steady_state_concentrations, reaction_sys)
    print("Dimer concentrations:", dimer_concentrations)