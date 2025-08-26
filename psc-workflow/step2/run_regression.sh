#!/usr/bin/bash
#SBATCH -p GPU-shared
#SBATCH -N 1
#SBATCH --gpus=v100-32:1
#SBATCH -t 2:00:00
#SBATCH -J Regression
#SBATCH -A sys890003p
#SBATCH --output=regression_OCELOT_MS_%j.out

module load anaconda3/2022.10
#put the path to your conda environment here
conda activate /ocean/projects/sys890003p/spagaria/project1/regression

python3 run_regression.py --mode train --model_dir /ocean/projects/sys890003p/spagaria/project1/dana/regression_OCELOT/ms_OCELOT --params /ocean/projects/sys890003p/spagaria/project1/dana/regression_params.yaml --checkpoint_path /ocean/projects/sys890003p/spagaria/project1/dana/pretrain_DOF/pretrain_MS_0.0001/model_pretrain/checkpoint_3000.mdl --is_pretrained_checkpoint


# for this file you need:
# 1. the model directory where the step 5 files are stored basically
# 2. the params file - regression_params.yaml
# 3. the checkpoint path - this is the path to the pre-trained model's best checkpoint