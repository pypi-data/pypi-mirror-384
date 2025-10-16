from aegon.libutils import sort_by_energy
from aegon.libroulette import get_fitness
#-------------------------------------------------------------------------------
def display_mol_info(moleculein, flagsum=1):
    if len(moleculein)==0:
        print("\n------------ALL MOLECULES DISCRIMINATED. SOLIDS FINISH.------------")
    molzz=sort_by_energy(moleculein, 1)
    for ii, imol in enumerate(molzz):
        deltae=imol.info['e'] - molzz[0].info['e']
        jj=str(ii+1).zfill(5)
        if flagsum == 1:
            fitness=get_fitness(moleculein)
            print("#%s %-12s %.6f eV (%.6f eV) (f=%.2f)" %(jj, imol.info['i'], imol.info['e'], deltae, fitness[ii]))
        else:
            print("#%s %-12s %.6f eV (%.6f eV)" %(jj, imol.info['i'], imol.info['e'], deltae))
#-------------------------------------------------------------------------------
def sorting_atoms(atoms_in):
    from ase import Atoms
    atomsOut = atoms_in.copy()
    atomsOutsym = atomsOut.get_chemical_symbols()
    sorted_indices = sorted(range(len(atomsOutsym)), key=lambda i: atomsOutsym[i])
    atomsOut = atomsOut[sorted_indices]
    return atomsOut