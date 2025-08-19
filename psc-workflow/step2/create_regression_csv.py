import argparse
from ase.io import read
import csv
import os
from pymatgen.io.ase import AseAtomsAdaptor as AAA 
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer as SGA 
import random
# from robocrys import StructureCondenser, StructureDescriber
from slices.core import SLICES 
from tqdm import tqdm 
import warnings
warnings.filterwarnings("ignore")

def get_slices(struct):
	backend = SLICES()
	slices = backend.structure2SLICES(struct)
	return slices 

def get_material_string(struct):
	try:
		primitive_struct = struct.get_primitive_structure()
		spg_info = primitive_struct.get_space_group_info(symprec=0.1)
		spg = spg_info[0]
		lattice = primitive_struct.lattice 
		a, b, c = lattice.abc 
		alpha, beta, gamma = lattice.angles
		sga = SGA(primitive_struct, symprec=0.1)
		symm_dict = sga.get_symmetry_dataset()
		wyckoff = symm_dict['wyckoffs']
		site_symmetry = symm_dict['site_symmetry_symbols']
		materials_string = spg + ' ' + str(a) + ' ' + str(b) + ' ' + str(c) + ' ' + str(alpha) + ' ' + str(beta) + ' ' + str(gamma) + ' '

		for idx, wyck in enumerate(wyckoff):
			site_sym = site_symmetry[idx]
			wyckoff_pos = site_sym + wyck 
			materials_string += wyckoff_pos
			materials_string += ' '
		return materials_string
    except Exception as e:
		print(f"Error processing structure: {e}")
		return "Unknown"

# def get_robocrys(struct):
# 	condenser = StructureCondenser()
# 	describer = StructureDescriber()
# 	condensed_structure = condenser.condense_structure(struct)
# 	description = describer.describe(condensed_structure)
# 	return description

def write_tsv(training, keys, results):
	if training:
		tsv_file = 'train.tsv'
	else:
		tsv_file = 'dev.tsv'
	with open(tsv_file, 'w') as f:
		writer = csv.writer(f, delimiter='\t', lineterminator='\n')
		writer.writerow(['sentence', 'label'])
		for key in keys:
			writer.writerow([key, results[key]])
	f.close()

parser = argparse.ArgumentParser()
parser.add_argument('--data_dir')
parser.add_argument('--encoding')
parser.add_argument('--train_val_split', type=float)
parser.add_argument('--outdir')
parser.add_argument('--target_file', default='targets')
args = parser.parse_args()

root_dir = os.path.abspath(args.data_dir)
target_file = os.path.join(root_dir, '{}.csv'.format(args.target_file))

results = {}

with open(target_file, 'r') as f:
	reader = csv.reader(f)
	for row in reader:
		struct_id = row[0]
		label = float(row[1])
		cif_path = os.path.join(root_dir, '{}.cif'.format(struct_id))
		s = read(cif_path)
		pym_struct = AAA.get_structure(s)
		if args.encoding == 'materials_string':
			encoding = get_material_string(pym_struct)
		elif args.encoding == 'slices':
			encoding = get_slices(pym_struct)
		# elif args.encoding == 'robocrys':
		# 	encoding = get_robocrys(pym_struct)
		results[encoding] = label

random.seed(42)
total_keys = list(results.keys())
total_examples = len(total_keys)
train_examples = int(total_examples * args.train_val_split)
train_keys = random.sample(total_keys, train_examples)
val_keys = [key for key in total_keys if key not in train_keys]

os.chdir(args.outdir)

write_tsv(True, train_keys, results)
write_tsv(False, val_keys, results)
