import time
import numpy as np
from joblib import Parallel, delayed
from scipy.optimize import minimize
from numba import jit
#------------------------------------------------------------------------------------------
epsilon=1.0
sigma = 3.0 / np.power(2.0, 1.0/6.0)
cutoff=18.0
method='L-BFGS-B'
gtol=1e-6
#------------------------------------------------------------------------------------------
@jit(nopython=True)
def lj_energy(positions):
    N = len(positions)
    energy = 0.0
    for i in range(N):
        for j in range(i + 1, N):
            rij = positions[i] - positions[j]
            r = np.linalg.norm(rij)
            if r < cutoff:
                sr6 = (sigma / r) ** 6
                energy += 4.0 * epsilon * sr6 * (sr6 - 1.0)
    return energy
#------------------------------------------------------------------------------------------
@jit(nopython=True)
def lj_forces(positions):
    N = len(positions)
    forces = np.zeros_like(positions)
    for i in range(N):
        for j in range(i + 1, N):
            rij = positions[i] - positions[j]
            r = np.linalg.norm(rij)
            if r < cutoff:
                sr6 = (sigma / r) ** 6
                f_scalar = 24.0 * epsilon * sr6 * (2.0 * sr6 - 1.0) / r
                fij = f_scalar * (rij / r)
                forces[i] += fij
                forces[j] -= fij
    return forces
#------------------------------------------------------------------------------------------
def opt_lj(atoms):
    cluster = atoms.copy()
    x0 = cluster.get_positions()
    def objective(x):
        positions = x.reshape(-1, 3)
        return lj_energy(positions)
    def gradient(x):
        positions = x.reshape(-1, 3)
        forces = lj_forces(positions)
        return -forces.reshape(-1)
    result = minimize(
        fun=objective,
        x0=x0.reshape(-1),
        jac=gradient,
        method=method,
        options={'disp': False, 'gtol': gtol}
    )
    opt_positions = result.x.reshape(-1, 3)
    energy_scipy = result.fun
    cluster_opt = atoms.copy()
    cluster_opt.set_positions(opt_positions)
    cluster_opt.info['e'] = energy_scipy
    cluster_opt.info['c'] = 1
    return cluster_opt
#------------------------------------------------------------------------------------------
def parallel_opt_LJ(mol_list, n_jobs=-1):
    start_time = time.time()
    n1=len(mol_list)
    if not isinstance(mol_list, list): mol_list = [mol_list]
    results = Parallel(n_jobs=n_jobs)(delayed(opt_lj)(mol) for mol in mol_list)
    n2=len(results)
    end_time = time.time()
    print("Local OPT parallel at %.2f s [%d -> %d]" % (end_time-start_time, n1, n2))
    return results
#------------------------------------------------------------------------------------------
#if __name__ == "__main__":
#    from aegon.libutils import readxyzs
#    lj_clusters=readxyzs('Wales003to150.xyz')
#    for imol in lj_clusters:
#        n=len(imol)
#        energy_true= imol.info['e']
#        imol=opt_lj(imol)
#        energy_lj= imol.info['e']
#        print("#%s E_x = %13.8f E_True= %13.8f" %(str(n).zfill(3), energy_lj, energy_true))
