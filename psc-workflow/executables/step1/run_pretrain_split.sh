#!/usr/bin/bash
#SBATCH --gres=cs:cerebras:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=14
#SBATCH --time=12:00:00
#SBATCH -J RoBERTa
#SBATCH --output=slurm_%j_OCELOT_slicesplus_lr=0.000005.out

#have this be the directory where you are launching the job from
ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

mkdir -p pretrain_OCELOT/pretrain_MS_0.0001/pretraining
git clone https://github.com/Cerebras/modelzoo.git
git checkout R_1.6.1
MODELZOO_PATH=$(readlink -f modelzoo)

prepare_tokenization_split.py
create_csv_mlm_only.py train
create_csv_mlm_only.py val
create_csv_mlm_only.py test
[Neocortex] run_roberta.py  }
create_regression_csv.py    } => run_regression.py => run_inference.py => End

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#break up the text file
python3 prepare_tokenization_split.py
  INPUT
    --text_file ${ENTRY_LOCATION}/encoding/crystal_materials_string_OCELOT.txt
  OUTPUT
    --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#preprocess thROY
python3 create_csv_mlm_only.py
  ARGUMENT
    --name preprocessed_data_train (prefix)
    --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train
  INPUT
    --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train/meta.txt
    --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt
  OUTPUT
    --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/train

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#csvs from tokenization VAL dDOF
python3 create_csv_mlm_only.py
  ARGUMENT
    --name preprocessed_data_val
    --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val
  INPUT
    --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val/meta.txt
    --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt
  OUTPUT
    --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/val

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#csvs from tokenization TEST data
python3 create_csv_mlm_only.py
  ARGUMENT
    --name preprocessed_data_test
    --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test
  INPUT
    --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test/meta.txt
    --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt
  OUTPUT
    --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/test

# TODO: This substep will run on Neocortex
#run the pre-training on RoBERTa
python-pt run_roberta.py
  ARGUMENT
    --mode train
  INPUT
    --params ${ENTRY_LOCATION}/roberta_params_OCELOT_MS.yaml --cs_ip ${CS_IP_ADDR}
  OUTPUT
    --model_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/model_pretrain

tar cvzf ${ENTRY_LOCATION}/pretrain_MS_0_0001.tgz ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001