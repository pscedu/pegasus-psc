#!/usr/bin/env bash

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#preprocess thROY
python3 create_csv_mlm_only.py --name preprocessed_data_train --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/train/meta.txt --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt   --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/train

tar cvzf ${ENTRY_LOCATION}/csv_train.tgz --directory=${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/ train