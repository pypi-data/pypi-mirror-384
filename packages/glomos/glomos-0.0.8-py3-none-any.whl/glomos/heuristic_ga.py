from aegon.libutils import sort_by_energy, cutter_energy, rename
from aegon.libmolgen  import make_molecules_random
from aegon.libcrossover import crossover_deavenho
from aegon.libgcolab import viewmol_ASE
from aegon.libstdio import read_main_input
#from aegon.libcalc_emt import ene_EMT, opt_EMT
from aegon.libcalc_lj import parallel_opt_LJ
from aegon.libroulette import get_fitness, get_roulette_wheel_selection
from aegon.libdiscusr import comparator_usr_serial, molin_sim_molref
#------------------------------------------------------------------------------------------
def display_mol_info(moleculein, flagsum=0, ngen=0):
    if len(moleculein)==0:
        print("\n------------ALL MOLECULES DISCRIMINATED. GLOMOS FINISH.------------")
    if flagsum == 0:
        print("---------------------------GENERATION %d---------------------------" %(ngen))
    else:
        print("--------------------------GLOBAL SUMMARY---------------------------")
    molzz=sort_by_energy(moleculein, 1)
    fitness=get_fitness(moleculein)
    for ii, imol in enumerate(molzz):
        deltae=imol.info['e'] - molzz[0].info['e']
        jj=str(ii+1).zfill(5)
        if flagsum == 0:
            print("#%s %-14s with %13.8f eV (%10.8f)" %(jj, imol.info['i'], imol.info['e'], deltae))
        else:
            print("#%s %-14s with %13.8f eV (%10.8f) (f=%3.2f)" %(jj, imol.info['i'], imol.info['e'], deltae, fitness[ii]))
    if flagsum != 0: print('')
#------------------------------------------------------------------------------------------
def genetic_algorithm(inputfile):
    df = read_main_input(inputfile)
    composition = df.get_comp(key='COMPOSITION')
    atomlist=composition.atoms
    nameid=composition.name
    mono=True if len(composition.elements)==1 else False
    ninitpop=df.get_int(key='nof_initpop', default=10)
    nmatings=df.get_int(key='nof_matings', default=5)
    ngenerations=df.get_int(key='nof_generations', default=5)
    tolsim=df.get_float(key='tol_similarity', default=0.95)
    ecut=df.get_float(key='cutoff_energy', default=10.0)
    npop=df.get_int(key='cutoff_population', default=10)
    nproc=df.get_int(key='nof_processes', default=2)
    print('-------- Global Optimization of Molecular Systems (GLOMOS) --------')
    print('Input file           = %s' %(inputfile))
    print('Option               = Modified Genetic Algorithm')
    print('Composition          = %s' %(nameid))
    print('Initial Population   = %d' %(ninitpop))
    print('Tol for similarity   = %4.2f' %(tolsim))
    print('Energy Cut-off       = %f' %(ecut))
    print('Max population size  = %d\n' %(npop))
    xrand = make_molecules_random(atomlist, ninitpop)
    xrand=rename(xrand,'random_00',4)
    #xopt=[opt_EMT(ix) for ix in xrand]
    xopt=parallel_opt_LJ(xrand, nproc)
    xopt=cutter_energy(xopt, ecut)
    xopt_sort=sort_by_energy(xopt, 1)
    xopt_sort=comparator_usr_serial(xopt_sort, tolsim, mono)
    xopt_sort=xopt_sort[:npop]
    display_mol_info(xopt_sort, flagsum=0, ngen=0)
    print('')
    for igen in range(ngenerations):
        list_p=get_roulette_wheel_selection(xopt_sort, nmatings)
        list_m=get_roulette_wheel_selection(xopt_sort, nmatings)
        atoms_list_out=[]
        for i in range(nmatings):
            cross = crossover_deavenho(list_p[i], list_m[i], atomlist)
            if cross: atoms_list_out.extend([cross])
        atoms_list_out=rename(atoms_list_out,'mating_'+str(igen+1).zfill(2),4)
        #cross_opt=[opt_EMT(ix) for ix in atoms_list_out]
        cross_opt=parallel_opt_LJ(atoms_list_out, nproc)
        cross_opt=cutter_energy(cross_opt, ecut)
        cross_opt=sort_by_energy(cross_opt,1)
        cross_opt=comparator_usr_serial(cross_opt, tolsim, mono)
        display_mol_info(cross_opt, flagsum=0, ngen=igen+1)
        cross_opt=molin_sim_molref(cross_opt, xopt_sort, tolsim, mono)
        xopt_sort=sort_by_energy(xopt_sort+cross_opt, 1)
        xopt_sort=xopt_sort[:npop]
        display_mol_info(xopt_sort, flagsum=1)
    return xopt_sort
#------------------------------------------------------------------------------------------
