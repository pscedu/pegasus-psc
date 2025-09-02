#!/usr/bin/env bash

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

tar xvzf csv_train.tgz
tar xvzf csv_test.tgz
tar xvzf csv_val.tgz

# TODO: This substep will run on Neocortex
#run the pre-training on RoBERTa
python-pt run_roberta.py --mode train --cs_ip ${CS_IP_ADDR} --params ${ENTRY_LOCATION}/roberta_params_OCELOT_MS.yaml --model_dir ${ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/model_pretrain

tar cvzf ${ENTRY_LOCATION}/pretrain_OCELOT__pretrain_MS_0_0001__model_pretrain.tgz --directory=${ENTRY_LOCATION}/ pretrain_OCELOT/pretrain_MS_0.0001/model_pretrain