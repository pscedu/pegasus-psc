#!/usr/bin/bash
#SBATCH -p GPU-shared
#SBATCH -N 1
#SBATCH --gpus=v100-32:1
#SBATCH -t 24:00:00
#SBATCH -J Inference
#SBATCH -A sys890003p

module load anaconda3/2022.10
#put the path to your conda environment here
conda activate /ocean/projects/sys890003p/spagaria/project1/envs

python run_inference.py --checkpoint_path ./materials_string_regression/checkpoint_15000.mdl --outfile materials_string_inference
