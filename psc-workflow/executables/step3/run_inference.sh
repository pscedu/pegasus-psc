#!/usr/bin/env bash
#SBATCH -p GPU-shared
#SBATCH --gpus=v100-32:1

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

# TODO: Run after the "run_regression.py" substep has finished.
python run_inference.py --checkpoint_path ${ENTRY_LOCATION}/regression_OCELOT/ms_OCELOT/checkpoint_2100.mdl --outfile inference_MS_OCELOT.json