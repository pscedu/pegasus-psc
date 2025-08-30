#!/usr/bin/env bash
#SBATCH -p GPU-shared
#SBATCH --gpus=v100-32:1

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

tar xvzf merged_dataset_ocelot.tgz
tar xvzf pretrain_OCELOT__pretrain_MS_0_0001__model_pretrain.tgz

# TODO: Run the "create_regression_csv.py" and "run_roberta.py" steps before running this one. The dirs mentioned in the YAML require on that step finishing.
python3 run_regression.py --mode train --is_pretrained_checkpoint --checkpoint_path ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/model_pretrain/checkpoint_3000.mdl --params ${ENTRY_LOCATION}/regression_params.yaml --model_dir ${ENTRY_LOCATION}/regression_OCELOT/ms_OCELOT