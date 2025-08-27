#!/usr/bin/bash
#SBATCH -p GPU-shared
#SBATCH -N 1
#SBATCH --gpus=v100-32:1
#SBATCH -t 2:00:00
#SBATCH -J Inference
#SBATCH -A sys890003p
#SBATCH --output=inference_%j.out

module load anaconda3/2022.10
#put the path to your conda environment here
conda activate /ocean/projects/sys890003p/spagaria/project1/envs

python run_inference.py --checkpoint_path /ocean/projects/sys890003p/spagaria/project1/dana/regression_OCELOT/ms_OCELOT/checkpoint_2100.mdl --outfile inference_MS_OCELOT


#the checkpoint path is the path to the best checkpoint of your trained regression model
#the outfile is the name of the output file where the predictions will be stored