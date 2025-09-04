#!/usr/bin/env bash

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#csvs from tokenization VAL dDOF
python3 create_csv_mlm_only.py --name preprocessed_data_val --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/val/meta.txt --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/val

tar cvzf csv_val.tgz --directory=${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/ val