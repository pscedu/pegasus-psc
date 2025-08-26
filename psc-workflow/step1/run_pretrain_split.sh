#!/usr/bin/bash
#SBATCH --gres=cs:cerebras:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=14
#SBATCH --time=12:00:00
#SBATCH -J RoBERTa
#SBATCH --output=slurm_%j_OCELOT_slicesplus_lr=0.000005.out

#fill in GRANT_ID with the ACCESS/PSC grant number and then your PSC username
PROJECT=/ocean/projects/sys890003p/spagaria
#have this be the directory where you are launching the job from 
ENTRY_LOCATION=$PROJECT/project1/dana

#bind locations and the cerebras container
BIND_LOCATIONS=/local1/cerebras/data,/local2/cerebras/data,/local3/cerebras/data,/local4/cerebras/data,/ocean/neocortex/cerebras/data,${PROJECT},/ocean/projects/cis250115p/spagaria
CEREBRAS_CONTAINER=/ocean/neocortex/cerebras/cbcore_latest.sif

#break up the text file
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python prepare_tokenization_split.py --text_file ./encoding/crystal_materials_string_OCELOT --output_dir ./pretrain_OCELOT/pretrain_MS_0.0001/pretraining

#preprocess thROY
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python create_csv_mlm_only.py --metadata_files ./pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train/meta.txt --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train --vocab_file ./tokenizer/materials_string_OCELOT.txt --output_dir ./pretrain_OCELOT/pretrain_MS_0.0001/csvs/train --name preprocessed_data_train
#csvs from tokenization VAL dDOF
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python create_csv_mlm_only.py --metadata_files ./pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val/meta.txt --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val --vocab_file ./tokenizer/materials_string_OCELOT.txt --output_dir ./pretrain_OCELOT/pretrain_MS_0.0001/csvs/val --name preprocessed_data_val
#csvs from tokenization TEST data
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python create_csv_mlm_only.py --metadata_files ./pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test/meta.txt --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test --vocab_file ./tokenizer/materials_string_OCELOT.txt --output_dir ./pretrain_OCELOT/pretrain_MS_0.0001/csvs/test --name preprocessed_data_test

#run the pre-training on RoBERTa
srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python-pt run_roberta.py --mode train --model_dir ./pretrain_OCELOT/pretrain_MS_0.0001/model_pretrain --params ./roberta_params_OCELOT_MS.yaml --cs_ip ${CS_IP_ADDR}

# srun --kill-on-bad-exit singularity exec --bind ${BIND_LOCATIONS} ${CEREBRAS_CONTAINER} python-pt run_roberta.py --mode eval --model_dir ./pretrain_OCELOT_slicesplus/pretrain_slices_plus_0.0001/model_pretrain --params ./roberta_params_3.yaml --cs_ip ${CS_IP_ADDR}


