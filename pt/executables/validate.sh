#!/bin/bash
set -e

TOP_DIR=`pwd`
STAGE="validate"


MODEL_DIR=`echo "$*" | sed -E 's/^.*--model_dir\s*(\w*)\s*.*\s*/\1/'`
echo "Model Dir passed for the job is $MODEL_DIR"

tar zxf ./modelzoo-raw.tgz

# untar other inputs staged
PREFIX="modelzoo/modelzoo/fc_mnist/pytorch/data/mnist/train/MNIST/raw"
INPUT_DATASETS=("train-images-idx3-ubyte.gz" "train-labels-idx1-ubyte.gz" "t10k-images-idx3-ubyte.gz" "t10k-labels-idx1-ubyte.gz")
for input in ${INPUT_DATASETS[@]}; do
    echo "Uncompressing $input"
    gunzip  ${PREFIX}/$input 
done

cd ${TOP_DIR}/modelzoo           


#YOUR_DATA_DIR=${LOCAL}/cerebras/data
mkdir -p ${TOP_DIR}/cerebras/data
YOUR_DATA_DIR=${TOP_DIR}/cerebras/data    
YOUR_MODEL_ROOT_DIR=${TOP_DIR}/modelzoo/modelzoo
YOUR_ENTRY_SCRIPT_LOCATION=${YOUR_MODEL_ROOT_DIR}/fc_mnist/pytorch

#BIND_LOCATIONS=/local1/cerebras/data,/local2/cerebras/data,/local3/cerebras/data,/local4/cerebras/data,${YOUR_DATA_DIR},${YOUR_MODEL_ROOT_DIR}
#CEREBRAS_CONTAINER=${LOCAL}/cerebras/cbcore_latest.sif
CEREBRAS_CONTAINER=/ocean/neocortex/cerebras/cbcore_latest.sif
cd ${YOUR_ENTRY_SCRIPT_LOCATION}

#srun --ntasks=1 --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python-pt run.py --mode train --validate_only --params configs/params.yaml --model_dir training_example_${SLURM_JOB_ID} 
python-pt run.py "$@"

# copy some auxillary cerebras log files
#CEREBRAS_LOGS=("performance.json" "run_summary.json" "params.yaml")
#for log in ${CEREBRAS_LOGS[@]}; do
#  mv ${MODEL_DIR}/$log ${TOP_DIR}/${STAGE}_${log}
#done

# tar up the validated model
cd ${TOP_DIR}

echo "Tarring up validated model in ${TOP_DIR}"
tar zcf modelzoo-validated.tgz  ./modelzoo
