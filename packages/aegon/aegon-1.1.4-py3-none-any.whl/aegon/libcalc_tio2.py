import numpy as np
from scipy.optimize import minimize
from joblib import Parallel, delayed
from ase import Atoms
#------------------------------------------------------------------------------------------
# POTENTIAL PARAMETERS AND CHARGES
parameters = {
    'charges': {'Ti': 2.196, 'O': -1.098},
    'buckingham': {
        ('Ti', 'Ti'): (31120.1, 0.1540, 5.25),
        ('O', 'O'): (11782.7, 0.2340, 30.22),
        ('O', 'Ti'): (16957.5, 0.1940, 12.59)
    },
    'lennard_jones': {
        ('Ti', 'Ti'): (1.0, 0.0),
        ('O', 'O'): (1.0, 0.0),
        ('O', 'Ti'): (1.0, 0.0)
    }
}
COULOMB_K = 14.39964546866782058  # eV·A
#------------------------------------------------------------------------------------------
def buckingham_coulomb_energy_forces(positions, symbols, parameters):
    n = len(positions)
    energy = 0.0
    forces = np.zeros_like(positions)
    charges = np.array([parameters['charges'][s] for s in symbols])
    for i in range(n):
        pos_i = positions[i]
        charge_i = charges[i]
        symbol_i = symbols[i]
        for j in range(i + 1, n):
            r_vec = pos_i - positions[j]
            r_sq = np.dot(r_vec, r_vec)
            r = np.sqrt(r_sq)
            inv_r = 1.0 / r
            r_hat = r_vec * inv_r
            
            # Precompute common powers of r
            inv_r2 = inv_r * inv_r
            inv_r6 = inv_r2 * inv_r2 * inv_r2
            inv_r7 = inv_r6 * inv_r
            inv_r12 = inv_r6 * inv_r6
            inv_r13 = inv_r12 * inv_r
            
            # Get pair parameters
            pair_key = (min(symbol_i, symbols[j]), max(symbol_i, symbols[j]))
            A, rho, C = parameters['buckingham'][pair_key]
            A_lj, _ = parameters['lennard_jones'][pair_key]
            
            # Coulomb interaction
            coulomb_energy = COULOMB_K * charge_i * charges[j] * inv_r
            coulomb_force = coulomb_energy * inv_r
            
            # Buckingham interaction
            exp_factor = np.exp(-r / rho)
            buck_energy = A * exp_factor - C * inv_r6
            buck_force = (A / rho) * exp_factor - 6 * C * inv_r7
            
            # Lennard-Jones repulsive interaction
            lj_energy = A_lj * inv_r12
            lj_force = 12.0 * A_lj * inv_r13
            
            # Sum contributions
            energy += coulomb_energy + buck_energy + lj_energy
            force_scalar = coulomb_force + buck_force + lj_force
            
            forces[i] += force_scalar * r_hat
            forces[j] -= force_scalar * r_hat
            
    return energy, forces
#------------------------------------------------------------------------------------------
def energy_forces_wrapper(x, symbols, parameters):
    positions = x.reshape(-1, 3)
    energy, forces = buckingham_coulomb_energy_forces(positions, symbols, parameters)
    return energy, -forces.reshape(-1)
#------------------------------------------------------------------------------------------
def optimize_TiO2(atoms, gtol=1e-6):
    symbols = atoms.get_chemical_symbols()
    x0 = atoms.positions.reshape(-1)
    result = minimize(
        fun=energy_forces_wrapper,
        x0=x0,
        args=(symbols, parameters),
        jac=True,
        method='BFGS',
        options={'gtol': gtol, 'disp': False, 'maxiter': 500}
    )
    opt_positions = result.x.reshape(-1, 3)
    energy_final, _ = buckingham_coulomb_energy_forces(
        opt_positions, symbols, parameters
    )
    atoms_opt = atoms.copy()
    atoms_opt.set_positions(opt_positions)
    atoms_opt.info['e'] = energy_final
    atoms_opt.info['i'] = atoms.info['i']
    return atoms_opt
#------------------------------------------------------------------------------------------
def optimize_TiO2_parallel(mol_list, n_jobs=1):
    return Parallel(n_jobs=n_jobs)(delayed(optimize_TiO2)(mol) for mol in mol_list)
#------------------------------------------------------------------------------------------
def example():
    import time
    from ase.io import read
    from aegon.libutils import writexyzs, rename, sort_by_energy
    clusters = read("stage1.xyz", index=":")
    print('PARALLEL OPTIMIZATION')
    rename(clusters, 'X', 3)
    for i in range(3):
        start_time = time.time()
        clusters = optimize_TiO2_parallel(clusters, n_jobs=10)
        #clusters = sort_by_energy(clusters, 1)
        end_time = time.time()
        print("Total time = %.2f" % (end_time-start_time))
    writexyzs(clusters, 'optimizados.xyz')
#example()
