#!/usr/bin/bash
#SBATCH -p GPU-shared
#SBATCH -N 1
#SBATCH --gpus=v100-32:1
#SBATCH -t 1:00:00
#SBATCH -J Regression
#SBATCH -A sys890003p

module load anaconda3/2022.10
#put the path to your conda environment here
conda activate /ocean/projects/sys890003p/spagaria/project1/envs

python3 run_regression.py --mode train --model_dir /ocean/projects/sys890003p/spagaria/project1/dana/regression_density --params /ocean/projects/sys890003p/spagaria/project1/dana/regression_params.yaml
