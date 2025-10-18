import time
import numpy as np
from joblib import Parallel, delayed
from scipy.optimize import minimize
from numba import jit
#------------------------------------------------------------------------------------------
cutoff=18.0
method='L-BFGS-B'
gtol=1e-6
#------------------------------------------------------------------------------------------
#PHILOSOPHICAL MAGAZINE LETTERS, 1990, VOL. 61, No. 3, 139-146
SUTTON_CHEN_PARAMS = {
    'Ni': {'n': 9,  'm': 6, 'epsilon': 1.0, 'af': 3.52, 'c': 39.432},
    'Cu': {'n': 9,  'm': 6, 'epsilon': 1.0, 'af': 3.61, 'c': 39.432},
    'Rh': {'n': 12, 'm': 6, 'epsilon': 1.0, 'af': 3.80, 'c': 144.41},
    'Pd': {'n': 12, 'm': 7, 'epsilon': 1.0, 'af': 3.89, 'c': 108.27},
    'Ag': {'n': 12, 'm': 6, 'epsilon': 1.0, 'af': 4.09, 'c': 144.41},
    'Ir': {'n': 14, 'm': 6, 'epsilon': 1.0, 'af': 3.84, 'c': 334.94},
    'Pt': {'n': 10, 'm': 8, 'epsilon': 1.0, 'af': 3.92, 'c': 34.408},
    'Au': {'n': 10, 'm': 8, 'epsilon': 1.0, 'af': 4.08, 'c': 34.408},
    'Pb': {'n': 10, 'm': 7, 'epsilon': 1.0, 'af': 4.95, 'c': 45.778},
    'Al': {'n': 7,  'm': 6, 'epsilon': 1.0, 'af': 4.05, 'c': 16.399}
}
#------------------------------------------------------------------------------------------
@jit(nopython=True)
def opt_sc_metal(positions, n, m, epsilon, af, c):
    """Calcula energía Sutton-Chen (optimizada con Numba)"""
    N = len(positions)
    energy = 0.0
    for i in range(N):
        s1i = 0.0
        s2i = 0.0
        for j in range(N):
            if i != j:
                rij = positions[i] - positions[j]
                r = np.linalg.norm(rij)
                if r < cutoff:
                    var0 = af / r
                    s1i += var0 ** n
                    s2i += var0 ** m
        sqrtrho = np.sqrt(s2i)
        ei = epsilon * (0.5 * s1i - c * sqrtrho)
        energy += ei
    return energy
#------------------------------------------------------------------------------------------
@jit(nopython=True)
def opt_sc_forces(positions, n, m, epsilon, af, c):
    N = len(positions)
    forces = np.zeros_like(positions)

    s2i_array = np.zeros(N)
    for i in range(N):
        s2i = 0.0
        for j in range(N):
            if i != j:
                rij = positions[i] - positions[j]
                r = np.linalg.norm(rij)
                if r < cutoff:
                    var0 = af / r
                    s2i += var0 ** m
        s2i_array[i] = s2i
    
    for i in range(N):
        for j in range(i + 1, N):
            rij = positions[i] - positions[j]
            r = np.linalg.norm(rij)
            if r < cutoff:
                var0 = af / r
                var0_n = var0 ** n
                var0_m = var0 ** m
                f_rep = epsilon * n * var0_n / r
                sqrt_rho_i = np.sqrt(s2i_array[i])
                sqrt_rho_j = np.sqrt(s2i_array[j])
                f_dens_i = epsilon * c * m * var0_m / (2.0 * sqrt_rho_i * r)
                f_dens_j = epsilon * c * m * var0_m / (2.0 * sqrt_rho_j * r)
                f_scalar = f_rep + f_dens_i + f_dens_j
                fij = f_scalar * (rij / r)
                forces[i] += fij
                forces[j] -= fij
    return forces
#------------------------------------------------------------------------------------------
def sutton_chen_energy(atoms, metal_type):
    params = SUTTON_CHEN_PARAMS[metal_type]
    positions = atoms.get_positions()
    return opt_sc_metal(
        positions, 
        params['n'], 
        params['m'], 
        params['epsilon'], 
        params['af'], 
        params['c'], 
        cutoff
    )
#------------------------------------------------------------------------------------------
def sutton_chen_forces(atoms, metal_type):
    """Wrapper para fuerzas Sutton-Chen con objetos ASE"""
    params = SUTTON_CHEN_PARAMS[metal_type]
    positions = atoms.get_positions()
    return opt_sc_forces(
        positions, 
        params['n'], 
        params['m'], 
        params['epsilon'], 
        params['af'], 
        params['c'], 
        cutoff
    )
#------------------------------------------------------------------------------------------
def opt_sc(atoms, metal_type='Cu'):
    params = SUTTON_CHEN_PARAMS[metal_type]
    af = params['af']
    n = params['n']
    m = params['m']
    epsilon = params['epsilon']
    c = params['c']
    
    cluster = atoms.copy()
    x0 = cluster.get_positions()
    
    def objective(x):
        positions = x.reshape(-1, 3)
        return opt_sc_metal(positions, n, m, epsilon, af, c)
    def gradient(x):
        positions = x.reshape(-1, 3)
        forces = opt_sc_forces(positions, n, m, epsilon, af, c)
        return -forces.reshape(-1)  # Gradiente = -Fuerzas
    
    result = minimize(
        fun=objective,
        x0=x0.reshape(-1),
        jac=gradient,
        method=method,
        options={'disp': False, 'gtol': gtol}
    )
    
    opt_positions = result.x.reshape(-1, 3)
    energy_opt = result.fun
    
    cluster_opt = atoms.copy()
    cluster_opt.set_positions(opt_positions)
    cluster_opt.info['e'] = energy_opt
    cluster_opt.info['c'] = 1
    return cluster_opt
#------------------------------------------------------------------------------------------
def parallel_opt_SC(mol_list, metal_type='Cu', n_jobs=-1):
    start_time = time.time()
    n1=len(mol_list)
    if not isinstance(mol_list, list): mol_list = [mol_list]
    results = Parallel(n_jobs=n_jobs)(delayed(opt_sc)(mol, metal_type) for mol in mol_list)
    n2=len(results)
    end_time = time.time()
    print("Local OPT parallel at %.2f s [%d -> %d]" % (end_time-start_time, n1, n2))
    return results
#------------------------------------------------------------------------------------------
#if __name__ == "__main__":
#    from aegon.libutils import readxyzs, writexyzs
#    scnet = readxyzs('SuttonChen003to080Cu.xyz')
#    for imol in scnet:
#        n=len(imol)
#        energy_true= imol.info['e']
#        imol=opt_sc(imol, metal_type='Cu')
#        energy_sc= imol.info['e']
#        print("#%s E_x = %f E_T= %f" %(str(n).zfill(3), energy_sc, energy_true))
#    #print('Parallel optimization of all clusters')
#    #all_optimized = parallel_opt_SC(scnet, metal_type='Cu', n_jobs=14)
#    #writexyzs(all_optimized, 'all_optimized_clusters.xyz')
