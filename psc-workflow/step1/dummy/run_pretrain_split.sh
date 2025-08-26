#!/usr/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=14
#SBATCH --time=0-00:01:00
#SBATCH -J RoBERTa-dummy

python3 prepare_tokenization.py
python3 create_csv_mlm_only.py
python3 run_roberta.py
