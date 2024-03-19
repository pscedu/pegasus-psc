#!/bin/bash
set -e

TOP_DIR=`pwd`

#echo "Copying modelzoo into ${TOP_DIR}"
#rm -rf ${TOP_DIR}/modelzoo
#git clone https://github.com/Cerebras/modelzoo.git 
#cd ${TOP_DIR}/modelzoo
#git checkout tags/R_1.6.0

tar zxf ./modelzoo-validated.tgz

cd ${TOP_DIR}/modelzoo           
#YOUR_DATA_DIR=${LOCAL}/cerebras/data
YOUR_DATA_DIR=${TOP_DIR}/cerebras/data    
YOUR_MODEL_ROOT_DIR=${TOP_DIR}/modelzoo/modelzoo
YOUR_ENTRY_SCRIPT_LOCATION=${YOUR_MODEL_ROOT_DIR}/fc_mnist/tf
BIND_LOCATIONS=/local1/cerebras/data,/local2/cerebras/data,/local3/cerebras/data,/local4/cerebras/data,${YOUR_DATA_DIR},${YOUR_MODEL_ROOT_DIR}
#CEREBRAS_CONTAINER=${LOCAL}/cerebras/cbcore_latest.sif
CEREBRAS_CONTAINER=/ocean/neocortex/cerebras/cbcore_latest.sif
cd ${YOUR_ENTRY_SCRIPT_LOCATION}

#singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python run.py --mode train --validate_only --model_dir validate
#singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python run.py "$@"
srun --ntasks=1 --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python run.py "$@"

# tar up the compiled model
cd ${TOP_DIR}
echo "Tarring up compiled model in ${TOP_DIR}"
tar zcf modelzoo-compiled.tgz  ./modelzoo
