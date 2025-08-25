import argparse
from ase.io import read
import csv
import os
from pymatgen.io.ase import AseAtomsAdaptor as AAA
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer as SGA
import random
from slices.core import SLICES
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

def get_slices(struct):
    backend = SLICES()
    return backend.structure2SLICES(struct)

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
        materials_string = f"{spg} {a} {b} {c} {alpha} {beta} {gamma} "
        for idx, wyck in enumerate(wyckoff):
            site_sym = site_symmetry[idx]
            materials_string += site_sym + wyck + " "
        return materials_string
    except Exception as e:
        print(f"Error processing structure: {e}")
        return "Unknown"

def write_tsv(training, keys, results):
    tsv_file = 'train.tsv' if training else 'dev.tsv'
    with open(tsv_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(['sentence', 'label'])
        for key in keys:
            writer.writerow([key, results[key]])

def parse_target_line(line):
    """
    Returns (struct_id:str, label:float) or (None, None) if not parseable.
    Accepts either:
      - 'ID<TAB>value'
      - 'ID,value'
      - 'ID  value' (whitespace)
    Skips headers (when second token isn't a float).
    """
    s = line.strip()
    if not s:
        return None, None

    # Decide delimiter per line
    if ',' in s:
        parts = s.split(',', 1)
    elif '\t' in s:
        parts = s.split('\t', 1)
    else:
        parts = s.split(None, 1)  # any whitespace

    if len(parts) != 2:
        return None, None

    struct_id = parts[0].strip()
    val_str = parts[1].strip()

    # Some CSVs may have trailing comments; strip them
    # e.g., "2.718 # note"
    val_str = val_str.split('#', 1)[0].strip()

    try:
        label = float(val_str)
    except Exception:
        # likely a header line like "id,label"
        return None, None

    return struct_id, label

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', required=True)
    parser.add_argument('--encoding', choices=['materials_string', 'slices'], required=True)
    parser.add_argument('--train_val_split', type=float, required=True)
    parser.add_argument('--outdir', required=True)
    parser.add_argument('--target_file', default='targets')  # without .csv
    args = parser.parse_args()

    root_dir = os.path.abspath(args.data_dir)
    target_path = os.path.join(root_dir, f"{args.target_file}.csv")

    results = {}  # mapping: encoding_text -> label
    collisions = 0

    with open(target_path, 'r') as f:
        for raw in f:
            struct_id, label = parse_target_line(raw)
            if struct_id is None:
                continue

            cif_path = os.path.join(root_dir, f"{struct_id}.cif")
            if not os.path.exists(cif_path):
                print(f"[{struct_id}] SKIPPED: CIF not found -> {cif_path}")
                continue

            try:
                s = read(cif_path, index=0)
                pym_struct = AAA.get_structure(s)

                if args.encoding == 'materials_string':
                    encoding = get_material_string(pym_struct)
                else:  # 'slices'
                    encoding = get_slices(pym_struct)

                if encoding in results:
                    collisions += 1  # same encoding produced by another struct; last wins
                results[encoding] = label
            except Exception as e:
                print(f"[{struct_id}] SKIPPED: {e}")
                continue

    if collisions:
        print(f"[WARN] {collisions} encodings collided (later entries overwrote earlier ones).")

    random.seed(42)
    total_keys = list(results.keys())
    total_examples = len(total_keys)
    train_examples = int(total_examples * args.train_val_split)
    train_keys = random.sample(total_keys, train_examples)
    val_keys = [key for key in total_keys if key not in train_keys]

    os.makedirs(args.outdir, exist_ok=True)
    os.chdir(args.outdir)

    write_tsv(True, train_keys, results)
    write_tsv(False, val_keys, results)

    print(f"[INFO] Output directory: {os.path.abspath(args.outdir)}")
    print(f"[INFO] Train rows: {len(train_keys)} | Dev rows: {len(val_keys)} | Total: {total_examples}")
    print("[DONE] TSV generation complete. Job finished successfully.")

if __name__ == "__main__":
    main()
