#!/bin/bash
set -e

TOP_DIR=`pwd`

STAGE="train"
MODEL_DIR=`echo "$*" | sed -E 's/^.*--model_dir\s*(\w*)\s*.*\s*/\1/'`
echo "Model Dir passed for the job is $MODEL_DIR"

tar zxf ./modelzoo-compiled.tgz

cd ${TOP_DIR}/modelzoo           
#YOUR_DATA_DIR=${LOCAL}/cerebras/data
mkdir -p ${TOP_DIR}/cerebras/data
YOUR_DATA_DIR=${TOP_DIR}/cerebras/data    
YOUR_MODEL_ROOT_DIR=${TOP_DIR}/modelzoo/modelzoo
YOUR_ENTRY_SCRIPT_LOCATION=${YOUR_MODEL_ROOT_DIR}/fc_mnist/tf
BIND_LOCATIONS=/local1/cerebras/data,/local2/cerebras/data,/local3/cerebras/data,/local4/cerebras/data,${YOUR_DATA_DIR},${YOUR_MODEL_ROOT_DIR}
#CEREBRAS_CONTAINER=${LOCAL}/cerebras/cbcore_latest.sif
CEREBRAS_CONTAINER=/ocean/neocortex/cerebras/cbcore_latest.sif
cd ${YOUR_ENTRY_SCRIPT_LOCATION}


set -x
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python run.py "$@" 

# copy some auxillary cerebras log files
CEREBRAS_LOGS=("performance.json" "run_summary.json" "params.yaml")
for log in ${CEREBRAS_LOGS[@]}; do
  mv ${MODEL_DIR}/$log ${TOP_DIR}/${STAGE}_${log}
done

# tar up the checkpoint files
echo "Tarring up generated checkpoints"
(cd ${MODEL_DIR} && tar zcvf ${TOP_DIR}/model-checkpoints.tgz  model.ckpt*)

# tar up the trained model
cd ${TOP_DIR}
echo "Tarring up trained model in ${TOP_DIR}"
tar zcf modelzoo-trained.tgz  ./modelzoo 
