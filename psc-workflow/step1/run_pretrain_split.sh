#!/usr/bin/bash
#SBATCH --gres=cs:cerebras:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=14
#SBATCH --time=12:00:00
#SBATCH -J RoBERTa
#SBATCH --output=slurm_%j_OCELOT_slicesplus_lr=0.000005.out

#have this be the directory where you are launching the job from
ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

mkdir pretrain_OCELOT
git clone https://github.com/Cerebras/modelzoo.git
git checkout R_1.6.1
MODELZOO_PATH=$(readlink -f modelzoo)

#break up the text file
python3 prepare_tokenization_split.py --text_file ${ENTRY_LOCATION}/encoding/crystal_materials_string_OCELOT.txt --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining

#preprocess thROY
python3 create_csv_mlm_only.py --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train/meta.txt --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/train --name preprocessed_data_train

#csvs from tokenization VAL dDOF
python3 create_csv_mlm_only.py --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val/meta.txt --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/val --name preprocessed_data_val

#csvs from tokenization TEST data
python3 create_csv_mlm_only.py --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test/meta.txt --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/test --name preprocessed_data_test

#run the pre-training on RoBERTa
python-pt run_roberta.py --mode train --model_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/model_pretrain --params ${ENTRY_LOCATION}/roberta_params_OCELOT_MS.yaml --cs_ip ${CS_IP_ADDR}

tar cvzf ${ENTRY_LOCATION}/pretrain_OCELOT.tgz ${ENTRY_LOCATION}/pretrain_OCELOT