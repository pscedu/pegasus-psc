import argparse
import os
import random

def split_up_textfile(text_file, output_dir, chunk_size=1000, seed=42):
    # Read all lines
    with open(text_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # Shuffle with seed
    random.seed(seed)
    random.shuffle(lines)

    # Split 80:10:10
    total = len(lines)
    n_train = int(0.8 * total)
    n_val = int(0.1 * total)

    splits = {
        "train": lines[:n_train],
        "val": lines[n_train:n_train + n_val],
        "test": lines[n_train + n_val:]
    }

    for split_name, data in splits.items():
        split_dir = os.path.join(output_dir, split_name)
        os.makedirs(split_dir, exist_ok=True)

        # Chunk into files
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            filename = f"smiles_{i//chunk_size}.txt"
            with open(os.path.join(split_dir, filename), 'w') as f:
                for line in chunk:
                    f.write(line + "\n")

        # Write corresponding meta.txt
        with open(os.path.join(split_dir, 'meta.txt'), 'w') as meta:
            for i in range(0, len(data), chunk_size):
                filename = os.path.abspath(os.path.join(split_dir, f"smiles_{i//chunk_size}.txt"))
                meta.write(filename + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--text_file', required=True, help="Input raw text file")
    parser.add_argument('--output_dir', required=True, help="Directory to write split and chunked files")
    parser.add_argument('--chunk_size', type=int, default=1000, help="Number of lines per chunk file")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for shuffling")
    args = parser.parse_args()

    split_up_textfile(args.text_file, args.output_dir, args.chunk_size, args.seed)

if __name__ == "__main__":
    main()
