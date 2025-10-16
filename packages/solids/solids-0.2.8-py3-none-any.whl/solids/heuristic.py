import os
from aegon.libutils import sort_by_energy, cutter_energy, rename
from aegon.libposcar import writeposcars
from aegon.libstdio import read_main_input
from aegon.libroulette import get_roulette_wheel_selection
from solids.libdiscmbtrcrystals import descriptor_comparison_calculated, descriptor_comparison_calculated_vs_pool, remove_similar_by_energy
from solids.libtools import display_mol_info
from solids.libmakextal import random_crystal_generator
from solids.libcrossover import crossover
from solids.libmutants import make_mutants
from solids.calc import code
import random
ndigit1=3
ndigit2=4
pformat='C'
#-------------------------------------------------------------------------------
def mainAlgorithm(inputfile='INPUT.txt'):
	#Reading variables
	df = read_main_input(inputfile)
	composition = df.get_comp(key='COMPOSITION')
	atomlist=composition.atoms
	nameid=composition.name
	#General parameters
	algorithm=df.get_str(key='algorithm', default='genetic')
	nformulaunits=df.get_int(key='formula_units', default=1)
	nof_initpop=df.get_int(key='nof_initpop', default=10)
	tol_similarity=df.get_float(key='tol_similarity', default=0.95)
	cutoff_energy=df.get_float(key='cutoff_energy', default=5.0)
	cutoff_population=df.get_int(key='cutoff_population', default=8)
	calculator=df.get_str(key='calculator', default='ANI1ccx')
	nof_parcalcs=df.get_int(key='nof_parcalcs', default=2)	
	#Parameters for genetic algorithm
	nof_matings=df.get_int(key='nof_matings', default=5)
	nof_strains=df.get_int(key='nof_strains', default=5)
	nof_xchange=df.get_int(key='nof_xchange', default=5)
	nof_generations=df.get_int(key='nof_generations', default=3)
	nof_repeats=df.get_int(key='nof_repeats', default=2)
	nof_stagnant=df.get_int(key='nof_stagnant', default=3)
	nof_processes=df.get_int(key='nof_processes', default=1)
	#Parameters for stochastic algorithm
	nof_stages=df.get_int(key='nof_stages', default=1)
	#Main Algorithm
	if algorithm == 'evolutive':
		#Welcome
		print('------- Evolutive Algorithm for Crystal Structure Prediction -------')
		print('Chemical Formula        = %s'    %(nameid))
		print('Number of Formula units = %s'    %(nformulaunits))
		print('\nEVOLUTIVE PARAMETERS:')
		print('Initial Population      = %d'    %(nof_initpop))
		print('Number of matings       = %d'    %(nof_matings))
		print('Number of strains       = %d'    %(nof_strains))
		print('Number of xchange       = %d'    %(nof_xchange))
		print('\nDISCRIMINATION PARAMETERS:')
		print('Tol for similarity      = %4.2f' %(tol_similarity))
		print('Energy Cut-off          = %.2f'  %(cutoff_energy))
		print('Max population size     = %d'    %(cutoff_population))
		print('\nSTOP CRITERION:')
		print('Max generations         = %d'    %(nof_generations))
		print('Max repeated isomers    = %d'    %(nof_repeats))
		print('Max stagnant cycles     = %d'    %(nof_stagnant))
		print()
		print('Theory Level            = %s'    %(calculator))
		#Main Algorithm
		print('---------------------------GENERATION 0---------------------------')
		print('Construction of the initial population (nof_initpop=%d)\n' %(nof_initpop))
		gen0Rand = random_crystal_generator(inputfile)
		rename(gen0Rand, 'random_'+str(0).zfill(ndigit1), ndigit2)
		print('\nOptimization at %s:' %(calculator))
		if calculator=='EMT':
			cd = code(gen0Rand)
			gen0Opt = cd.set_EMT()
		elif calculator=='GULP':
			cd = code(gen0Rand)
			block_gulp = df.get_block(key='GULP')
			path_exe = df.get_str(key='path_exe', default=None)
			gen0Opt = cd.set_GULP(block_gulp=block_gulp, gulp_path=path_exe, nproc=nof_processes, base_name='stage')
			os.system('rm -rf stageproc*')
		elif calculator=='VASP':
			cd = code(gen0Rand)
			block_vasp = df.get_block(key='VASP')
			gen0Opt = cd.set_VASP(block_vasp=block_vasp, NparCalcs=nof_parcalcs, base_name='gen'+str(0).zfill(ndigit1))
			os.system('rm -rf gen000_0*')

		print('\n---------------------------Niching---------------------------\n')
		print('Max population size=%d; Energy Cut-off=%.2f; Tolerance for similarity=%4.2f\n' %(cutoff_population,cutoff_energy,tol_similarity))
		gen0Cut = cutter_energy(gen0Opt, cutoff_energy)
		gen0CutSort = sort_by_energy(gen0Cut, 1)
		gen0Nich = descriptor_comparison_calculated(gen0CutSort, tol_similarity)
		genClean = gen0Nich[:cutoff_population]
		print('\n---------------------------GLOBAL SUMMARY---------------------------\n')
		display_mol_info(genClean)
		namesi=[imol.info['i'] for imol in genClean][:nof_repeats]
		count=0
		writeposcars(genClean, 'summary.vasp', pformat)
		for igen in range(nof_generations):
			print("\n---------------------------GENERATION %d---------------------------\n" %(igen+1))
			print('Construction of crossovers ...\n')
			list_p=get_roulette_wheel_selection(genClean, nof_matings)
			list_m=get_roulette_wheel_selection(genClean, nof_matings)
			cross_atoms = []
			for i in range(nof_matings):
				atomsA, atomsB = random.choice(list_p), random.choice(list_m)
				lock = 0
				while atomsA.info['i'] == atomsB.info['i']:
					atomsB = random.choice(list_m)
					lock += 1
					if lock > 10:
						break
				cross = crossover(atomsA, atomsB)
				if cross:
					print('mating_'+str(igen+1).zfill(4)+'_'+str(i+1).zfill(4)+' ---> '+list_p[i].info['i']+'_x_'+list_m[i].info['i'])
					cross_atoms.extend([cross])
			rename(cross_atoms, 'mating_'+str(igen+1).zfill(ndigit1), ndigit2)
			print('\nConstruction of mutants ...\n')
			list_x = get_roulette_wheel_selection(genClean, nof_strains+nof_xchange)
			strain_atoms, exchange_atoms = make_mutants(list_x, nof_strains, nof_xchange,igen=igen)
			allMutants = strain_atoms + exchange_atoms
			rename(allMutants, 'mutant_'+str(igen+1).zfill(ndigit1), ndigit2)
			gen_i = cross_atoms + strain_atoms + exchange_atoms
			print('\nOptimization at %s:' %(calculator))
			if calculator=='EMT':
				cd = code(gen_i)
				gen_iOpt = cd.set_EMT()
			elif calculator=='GULP':
				cd = code(gen_i)
				block_gulp=df.get_block(key='GULP')
				path_exe=df.get_str(key='path_exe', default=None)
				gen_iOpt = cd.set_GULP(block_gulp=block_gulp, gulp_path=path_exe, nproc=nof_processes, base_name='stage')
				os.system('rm -rf stageproc*')
			elif calculator=='VASP':
				cd = code(gen_i)
				block_vasp = df.get_block(key='VASP')
				gen_iOpt = cd.set_VASP(block_vasp=block_vasp, NparCalcs=nof_parcalcs, base_name='gen'+str(0).zfill(ndigit1))
				os.system('rm -rf gen000_0*')
			print('\n---------------------------NICHING---------------------------')
			print('Max population size=%d; Energy Cut-off=%.2f; Tol for similarity=%4.2f\n' %(cutoff_population,cutoff_energy,tol_similarity))
			gen_iCut = cutter_energy(gen_iOpt, cutoff_energy)
			gen_iCutSort = sort_by_energy(gen_iCut,1)
			gen_iNich = descriptor_comparison_calculated(gen_iCutSort, tol_similarity)
			gen_iClean = descriptor_comparison_calculated_vs_pool(gen_iNich, genClean, tol_similarity)
			gen_iClean = remove_similar_by_energy(gen_iClean, threshold=1e-3)
			print('\n---------------------------GEN. SUMMARY---------------------------')
			display_mol_info(gen_iClean)
			genClean = sort_by_energy(genClean+gen_iClean, 1)
			genClean = genClean[:cutoff_population]
			writeposcars(genClean, 'summary.vasp', pformat)
			print('\n---------------------------GLOBAL SUMMARY---------------------------')
			display_mol_info(genClean)
			namesj = [imol.info['i'] for imol in genClean][:nof_repeats]
			numij = [1 for i, j in zip(namesi,namesj) if i == j]
			count = count+1 if sum(numij) == nof_repeats else 1
			if count == nof_stagnant:
				print("\nEarly termination. Max repeated isomers (%d) reached at the Max stagnant cycles (%d)." %(nof_repeats, nof_stagnant))
				break
			namesi = namesj
		print("\nGlobal optimization complete.")
		return genClean
	else:
		#Welcome
		print('------- Stochastic Algorithm for Crystal Structure Prediction -------')
		print('Chemical Formula        = %s'    %(nameid))
		print('Number of Formula units = %s'    %(nformulaunits))
		print('\nALGORITHM PARAMETERS:')
		print('Initial Population      = %d'    %(nof_initpop))
		print('No. of Optimization Stages = %d'  %(nof_stages))
		print('\nNICHING PARAMETERS:')
		print('Tol for similarity      = %4.2f' %(tol_similarity))
		print('Energy Cut-off          = %.2f'  %(cutoff_energy))
		print('\nHALT CRITERION:')
		print()
		print('Theory Level            = %s'    %(calculator))

		#Main Algorithm
		print('--------------------------- POPULATION GENERATOR ---------------------------')
		print('Construction of the initial population (nof_initpop=%d)\n' %(nof_initpop))
		genClean = random_crystal_generator(inputfile)
		for stage in range(0, nof_stages):
			rename(genClean, 'stage_'+str(stage+1).zfill(ndigit1), ndigit2)
			print('\nOptimization at %s:' %(calculator))
			if calculator=='EMT':
				cd = code(genClean)
				gen0Opt = cd.set_EMT()
			elif calculator=='GULP':
				cd=code(genClean)
				block_gulp = df.get_block(key='GULP')
				path_exe = df.get_str(key='path_exe', default=None)
				gen0Opt = cd.set_GULP(block_gulp=block_gulp, gulp_path=path_exe, nproc=nof_processes, base_name='stage')
				os.system('rm -rf stageproc*')
			elif calculator=='VASP':
				cd=code(genClean)
				block_vasp = df.get_block(key='VASP')
				gen0Opt = cd.set_VASP(block_vasp=block_vasp, NparCalcs=nof_parcalcs, base_name='gen'+str(0).zfill(ndigit1))
				os.system('rm -rf gen000_0*')
			print('\n--------------------------- NICHING ---------------------------')
			print('Max population size=%d; Energy Cut-off=%.2f; Tolerance for similarity=%4.2f\n' %(cutoff_population,cutoff_energy,tol_similarity))
			gen0Cut = cutter_energy(gen0Opt, cutoff_energy)
			gen0CutSort = sort_by_energy(gen0Cut, 1)
			gen0Nich = descriptor_comparison_calculated(gen0CutSort, tol_similarity)
			genClean = gen0Nich[:cutoff_population]
			print('\n---------------------------STAGE %d SUMMARY---------------------------\n'%(stage+1))
			display_mol_info(genClean, pformat)
			writeposcars(genClean,'stage_'+str(stage)+'.vasp',pformat)
		print("\nGlobal optimization complete.")
		return genClean
#-------------------------------------------------------------------------------
