#!/usr/bin/bash
#SBATCH --gres=cs:cerebras:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=14
#SBATCH --time=4:00:00
#SBATCH -J RoBERTa

#fill in GRANT_ID with the ACCESS/PSC grant number and then your PSC username
PROJECT=/ocean/projects/sys890003p/spagaria
#have this be the directory where you are launching the job from 
ENTRY_LOCATION=$PROJECT/project1/dana

#bind locations and the cerebras container
BIND_LOCATIONS=/local1/cerebras/data,/local2/cerebras/data,/local3/cerebras/data,/local4/cerebras/data,/ocean/neocortex/cerebras/data,${PROJECT},/ocean/projects/cis250115p/spagaria
CEREBRAS_CONTAINER=/ocean/neocortex/cerebras/cbcore_latest.sif

#break up the text file
python prepare_tokenization.py --text_file ./encoding/crystal_slices_Final --output_dir ./pretraining_trial
#preprocess the data
python create_csv_mlm_only.py --metadata_files ./pretraining_trial/meta.txt --input_files_prefix ${ENTRY_LOCATION}/pretraining_trial --vocab_file ./slices_vocab_Final.txt --output_dir ./slices_csvfiles
#run the pre-training on RoBERTa
python-pt run_roberta.py --mode train --model_dir ./model_pretrain_slices --params ./roberta_params.yaml --cs_ip ${CS_IP_ADDR}
