#!/usr/bin/env bash

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#csvs from tokenization TEST data
python3 create_csv_mlm_only.py --name preprocessed_data_test --input_files_prefix ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test --metadata_files ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining/test/meta.txt --vocab_file ${ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/test

tar cvzf csv_test.tgz --directory=${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/csvs/ test