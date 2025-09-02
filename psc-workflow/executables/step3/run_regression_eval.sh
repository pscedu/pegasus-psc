#!/usr/bin/bash
#SBATCH -p GPU-shared
#SBATCH -N 1
#SBATCH --gpus=v100-32:1
#SBATCH -t 3:00:00
#SBATCH -J REG_EVAL
#SBATCH -A sys890003p
#SBATCH --output=regression_eval_%j.out

module load anaconda3/2022.10
conda activate /ocean/projects/sys890003p/spagaria/project1/regression

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana
MODEL_DIR=${ENTRY_LOCATION}/regression_OCELOT/ms_OCELOT    ##make changes here
PARAMS=${ENTRY_LOCATION}/regression_params.yaml    ##make changes here 

cd "${ENTRY_LOCATION}"

# TODO: Skipping for now.
## Loop over checkpoints from 0 to 4000 in steps of 100 [you can make changes here as well as in the loop condition]
#for (( STEP=0; STEP<=3000; STEP+=100 )); do
#
#    CKPT=${MODEL_DIR}/checkpoint_${STEP}.mdl
#    EVAL_OUT=${MODEL_DIR}/eval_inf/eval_${STEP}
#
#    echo "Evaluating ${CKPT}"
#
#    python3 run_regression.py \
#        --mode eval \
#        --model_dir "${EVAL_OUT}" \
#        --params "${PARAMS}" \
#        --checkpoint_path "${CKPT}"
#
#    echo "Done with checkpoint ${STEP}"
#done
