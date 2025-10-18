import os
import numpy as np
from ase import Atoms
from ase.data import covalent_radii
from aegon.libutils import align
#------------------------------------------------------------------------------------------
def tag(poscarlist):
    if not isinstance(poscarlist, list):
        poscarlist = [poscarlist]
    moleculeout = []
    for atoms in poscarlist:
        force = hasattr(atoms, "forces")
        numbers = list(set(atoms.get_atomic_numbers()))
        tagdict = {zi: itag for itag, zi in enumerate(sorted(numbers))}
        enumerate_molecule = atoms.copy()
        for iatom in enumerate_molecule:
            iatom.tag = tagdict[iatom.number]
        if force:
            enumerate_molecule.arrays['forces'] = atoms.arrays['forces']
        moleculeout.append(enumerate_molecule)
    return moleculeout
#------------------------------------------------------------------------------------------
def order_and_tag(poscarlist):
    if not isinstance(poscarlist, list):
        poscarlist = [poscarlist]
    outlist = []
    for atoms in poscarlist:
        numbers = atoms.get_atomic_numbers()
        symbols = atoms.get_chemical_symbols()
        positions = atoms.get_positions()
        forces = atoms.arrays['forces'] if 'forces' in atoms.arrays else None
        idx = np.argsort(numbers)
        sorted_numbers = [numbers[i] for i in idx]
        sorted_symbols = [symbols[i] for i in idx]
        sorted_positions = [positions[i] for i in idx]
        if forces is not None:
            sorted_forces = [forces[i] for i in idx]
        sorted_atoms = Atoms(symbols=sorted_symbols,
                             positions=sorted_positions,
                             cell=atoms.cell,
                             pbc=atoms.pbc)
        unique_numbers = sorted(set(sorted_numbers))
        tagdict = {zi: itag for itag, zi in enumerate(unique_numbers)}
        sorted_atoms.set_tags([tagdict[zi] for zi in sorted_numbers])
        if forces is not None:
            sorted_atoms.set_array("forces", np.array(sorted_forces))
        outlist.append(sorted_atoms)
    return outlist
# ------------------------------------------------------------------------------------------
def make_matrix(mol, latsp=5.0):
    mol_centered = mol.copy()
    mol_centered.translate(-mol_centered.get_center_of_mass())
    pos = mol_centered.get_positions()
    radii = [covalent_radii[z] for z in mol_centered.get_atomic_numbers()]
    extent = np.max(np.abs(pos) + np.array(radii)[:, None], axis=0) * 2.0 + latsp
    return np.diag(extent)
# ------------------------------------------------------------------------------------------
def molecule2poscar(atomslist, latsp=5.0, do_align=False):
    if not isinstance(atomslist, list):
        atomslist = [atomslist]
    outlist = []
    for mol in atomslist:
        mol_copy = mol.copy()
        if do_align: align(mol_copy)
        mol_copy.translate(-mol_copy.get_center_of_mass())
        matrix = make_matrix(mol_copy, latsp)
        shift = 0.5 * np.diag(matrix)
        mol_copy.translate(shift)
        mol_copy.set_cell(matrix)
        mol_copy.set_pbc([True, True, True])
        outlist.append(mol_copy)
    return order_and_tag(outlist)
# ------------------------------------------------------------------------------------------
def readposcars(filename):
    if not os.path.isfile(filename):
        print("The file %s does not exist." %(filename))
        exit()
    contcarfile=open(filename,'r')
    poscarout=[]
    for line in contcarfile:
        header=line.split()
        name=header[0]
        energy=float(header[1]) if len(header)>1 else 0.0
        line=contcarfile.readline()
        if str(line.split()[0])=='0.00000000E+00': break
        #-----------------------------------
        scale=float(line.split()[0])
        line=contcarfile.readline()
        a1x, a1y, a1z=map(float,line.split())
        line=contcarfile.readline()
        a2x, a2y, a2z=map(float,line.split())
        line=contcarfile.readline()
        a3x, a3y, a3z=map(float,line.split())
        lattice_vectors=np.array([[a1x, a1y, a1z],[a2x, a2y, a2z],[a3x, a3y, a3z]])*scale
        #-----------------------------------
        line=contcarfile.readline()
        elements=line.split()
        line=contcarfile.readline()
        ocupnumchar=line.split()
        ocupnuminte=list(map(int, ocupnumchar))
        #-----------------------------------
        natom=sum(ocupnuminte)
        liste,kk=[],0
        for ii in ocupnuminte:
            for jj in range(ii):
                liste.append(elements[kk])
            kk=kk+1
        #-----------------------------------
        line=contcarfile.readline()
        sd=0
        if 'Selective dynamics' in line:
            line=contcarfile.readline()
            sd=1
        symbols=[]
        positions=[]
        if 'Direct' in line:
            for iatom in range(natom):
                line=contcarfile.readline()
                vecxyz=line.split()
                s=liste[iatom]
                symbols.append(s)
                xd=float(vecxyz[0])
                yd=float(vecxyz[1])
                zd=float(vecxyz[2])
                direct_coords = np.array([xd, yd, zd])
                cart_coords = np.dot(direct_coords, lattice_vectors)
                positions.append(cart_coords)
        if 'Cartesian' in line:
            for iatom in range(natom):
                s=liste[iatom]
                symbols.append(s)
                line=contcarfile.readline()
                cart_coords =np.array(line.split()[0:3])
                positions.append(cart_coords)
        positions=np.array(positions)
        iposcar = Atoms(symbols=symbols, positions=positions, cell=lattice_vectors, pbc=True)
        iposcar.info['i']=name
        iposcar.info['e']=energy
        poscarout.extend([iposcar])
    contcarfile.close()
    return poscarout
#------------------------------------------------------------------------------------------
def writeposcars(poscarlist, file, opt='D'):
    with open(file, "w") as f:
        for atoms in poscarlist:
            print("%s %12.8f" % (atoms.info['i'], atoms.info['e']), file=f)
            print('1.0', file=f)
            matrix = atoms.cell.array
            for vec in matrix:
                print("%20.16f %20.16f %20.16f" % tuple(vec), file=f)
            element_count = {}
            for sym in atoms.symbols:
                element_count[sym] = element_count.get(sym, 0) + 1
            print(' '.join(element_count.keys()), file=f)
            print(' '.join(str(v) for v in element_count.values()), file=f)
            if opt == 'C':
                print('Cartesian', file=f)
                count = {}
                for atom in atoms:
                    sym = atom.symbol
                    count[sym] = count.get(sym, 0) + 1
                    x, y, z = atom.position
                    print("%20.16f %20.16f %20.16f   !%s%d" %
                          (x, y, z, sym, count[sym]), file=f)
            elif opt == 'D':
                print('Direct', file=f)
                count = {}
                for atom in atoms:
                    sym = atom.symbol
                    count[sym] = count.get(sym, 0) + 1
                    frac = np.linalg.solve(matrix.T, atom.position)
                    print("%20.16f %20.16f %20.16f   !%s%d" %(frac[0], frac[1], frac[2], sym, count[sym]), file=f)
#------------------------------------------------------------------------------------------
def conventional(atoms, tol=0.0):
    dup_tol = 1e-5
    lattice = atoms.cell.array
    frac_coords = atoms.get_scaled_positions(wrap=False)
    symbols = atoms.get_chemical_symbols()
    new_symbols = []
    new_positions = []
    shifts = np.array(np.meshgrid([-1, 0, 1],[-1, 0, 1],[-1, 0, 1])).T.reshape(-1, 3)
    for icoord, sym in zip(frac_coords, symbols):
        for shift in shifts:
            fcoord = icoord + shift
            if np.all((fcoord >= -tol) & (fcoord <= 1.0 + tol)):
                pos = fcoord @ lattice
                if any(np.allclose(pos, p, atol=dup_tol) and s == sym
                       for p, s in zip(new_positions, new_symbols)):
                    continue
                new_symbols.append(sym)
                new_positions.append(pos)
    poscarout = Atoms(symbols=new_symbols, positions=new_positions, cell=lattice, pbc=True)
    return poscarout
#------------------------------------------------------------------------------------------
