#!/usr/bin/env bash
echo "Dummy output for $0"

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

mkdir -p pretrain_OCELOT/pretrain_MS_0.0001/pretraining
git clone https://github.com/Cerebras/modelzoo.git
git checkout R_1.6.1
MODELZOO_PATH=$(readlink -f modelzoo)

# TODO: This substep will run on CPU (Neocortex or Bridges-2)
#break up the text file
python3 prepare_tokenization_split.py --text_file ${ENTRY_LOCATION}/encoding/crystal_materials_string_OCELOT.txt --output_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining

tar cvzf ${ENTRY_LOCATION}/pretrain_OCELOT__pretrain_MS_0_0001__pretraining.tgz ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/pretraining