#!/usr/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=14
#SBATCH --time=0-00:01:00
#SBATCH -J RoBERTa-dummy

srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python3 prepare_tokenization.py
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python3 create_csv_mlm_only.py
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python3 run_roberta.py
