import numpy as np
from scipy.integrate import solve_ivp
import time
from .ReactionSys import ReactionSys
import matplotlib.pyplot as plt

def PnD_ODE_func (t, y, production, degradation, pair_index, k_on, k_off):
    mono_num = len(production)
    dydt = np.zeros_like(y)

    # production and degradation
    for i in range(mono_num):
        dydt[i] = production[i]
    for i in range(len(y)):
        dydt[i] -= degradation[i] * y[i]
    
    # dimerization and dissociation
    for i, (a, b) in enumerate(pair_index):

        dydt[a] -= k_on[i] * y[a] * y[b]
        dydt[b] -= k_on[i] * y[a] * y[b]
        dydt[mono_num + i] += k_on[i] * y[a] * y[b]

        dydt[a] += k_off[i] * y[mono_num + i]
        dydt[b] += k_off[i] * y[mono_num + i]
        dydt[mono_num + i] -= k_off[i] * y[mono_num + i]

    return dydt

def PnD_ODE_solve(reaction_sys: ReactionSys, init_conc=None, t_span=1e6):
    degradation = np.concatenate([reaction_sys.mono_degradation, reaction_sys.dimer_degradation_flat])
    sol = solve_ivp(
        fun=PnD_ODE_func,
        t_span=(0, t_span),
        y0=init_conc if init_conc is not None else np.zeros(len(degradation)),
        args=(reaction_sys.production, degradation, reaction_sys.dimers, reaction_sys.k_on_flat, reaction_sys.k_off_flat),
        method='LSODA',
        rtol=1e-6,
        atol=1e-9
    )
    return sol

def PnD_ODE_plot(sol, reaction_sys: ReactionSys, species: list =None):
    if species is None:
        species = reaction_sys.species_name
    time_points = sol.t
    plt.figure()
    for i in range(len(species)):
        index = reaction_sys.species_name2index[species[i]]
        if index > len(reaction_sys.monomers) - 1:
            plt.plot(sol.t, sol.y[index], label=species[i], linestyle='--') # dashed line for dimers
        else:
            plt.plot(sol.t, sol.y[index], label=species[i]) # solid line for monomers

    plt.xscale('linear')
    plt.yscale('log')
    plt.xlabel('Time')
    plt.ylabel('Concentration')
    plt.legend()
    plt.title('Dynamics of Monomers and Dimers')

# Example usage:
if __name__ == "__main__":
    reaction_sys = ReactionSys('ExampleReaction.json')
    time_start = time.time()

    sol = PnD_ODE_solve(reaction_sys)
    time_end = time.time()
    print(f"Solved in {time_end - time_start:.2f} seconds")
    steady_state_concentrations = sol.y[:, -1]
    print("Steady-state concentrations:", steady_state_concentrations)
    print("Monomer concentrations:", steady_state_concentrations[:len(reaction_sys.monomers)])
    print("Dimer concentrations:", steady_state_concentrations[len(reaction_sys.monomers):])

    # plot dynamics of the system
    PnD_ODE_plot(sol, reaction_sys, species=['A+B', 'A', 'B', 'B+C'])
    plt.show()