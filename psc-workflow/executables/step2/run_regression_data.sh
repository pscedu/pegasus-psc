#!/usr/bin/bash
#SBATCH -p RM-shared
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 5:00:00
#SBATCH -J RegressionData
#SBATCH -A sys890003p
#SBATCH --output=regression_data_%j.out

module load anaconda3/2022.10
#put the path to your conda environment here
# use the conda environment when using slices, ms or slices plus environment
conda activate /jet/home/spagaria/.conda/envs/shreya

# while running robocrys use the following conda environment
# conda activate /jet/home/spagaria/.conda/envs/shreya

python3 create_regression_csv.py --data_dir /ocean/projects/sys890003p/spagaria/project1/dana/Merged_Dataset/OCELOT --encoding materials_string --outdir /ocean/projects/sys890003p/spagaria/project1/dana/regression_OCELOT/ms_OCELOT --train_val_split 0.8