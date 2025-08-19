import argparse
import os

def split_up_textfile(text_file, data_path):
	cwd = os.getcwd()
	smiles = []
	with open(text_file, 'r') as f:
		for line in f:
			smiles.append(line.split('\n')[0])
	f.close()

	data_path = os.path.abspath(data_path)
	if not os.path.isdir(data_path):
		os.mkdir(data_path)

	os.chdir(data_path)

	num_smiles = len(smiles)
	num_chunks = int(num_smiles / 1000)

	smiles_list = []

	i = 0

	for chunk in range(num_chunks):
		smiles_list.append(smiles[i: i+1000])
		i += 1000

	for i, chunk in enumerate(smiles_list):
		with open('smiles_{}.txt'.format(i), 'w') as f:
			for smile in chunk:
				f.write(smile)
				f.write('\n')
		f.close()
	os.chdir(cwd)

def write_meta(data_path):
	cwd = os.getcwd()
	data_path = os.path.abspath(data_path)
	data_list = os.listdir(data_path)

	os.chdir(data_path)

	with open('meta.txt', 'w') as f:
		for dat in data_list:
			f.write(os.path.join(data_path, dat))
			f.write('\n')
	f.close()
	os.chdir(cwd)

parser = argparse.ArgumentParser()
parser.add_argument('--text_file')
parser.add_argument('--output_dir')
args = parser.parse_args()
split_up_textfile('{}.txt'.format(args.text_file), args.output_dir)
write_meta(args.output_dir)
