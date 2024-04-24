#!/bin/bash
set -e

TOP_DIR=`pwd`

STAGE="compile"

MODEL_DIR=`echo "$*" | sed -E 's/^.*--model_dir\s*(\w*)\s*.*\s*/\1/'`
echo "Model Dir passed for the job is $MODEL_DIR"

tar zxf ./modelzoo-validated.tgz

cd ${TOP_DIR}/modelzoo           
#YOUR_DATA_DIR=${LOCAL}/cerebras/data
YOUR_DATA_DIR=${TOP_DIR}/cerebras/data    
YOUR_MODEL_ROOT_DIR=${TOP_DIR}/modelzoo/modelzoo
YOUR_ENTRY_SCRIPT_LOCATION=${YOUR_MODEL_ROOT_DIR}/fc_mnist/pytorch

CEREBRAS_CONTAINER=/ocean/neocortex/cerebras/cbcore_latest.sif
cd ${YOUR_ENTRY_SCRIPT_LOCATION}

# execute the task
#singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python-pt run.py --mode train --compile_only --params configs/params.yaml --model_dir training_example_${SLURM_JOB_ID}
python-pt run.py "$@"

# copy some auxillary cerebras log files
#CEREBRAS_LOGS=("performance.json" "run_summary.json" "params.yaml")
#for log in ${CEREBRAS_LOGS[@]}; do
#  mv ${MODEL_DIR}/$log ${TOP_DIR}/${STAGE}_${log}
#done


# tar up the compiled model
cd ${TOP_DIR}
echo "Tarring up compiled model in ${TOP_DIR}"
tar zcf modelzoo-compiled.tgz  ./modelzoo
