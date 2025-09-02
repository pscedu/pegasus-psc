#!/usr/bin/env bash
#SBATCH -t 5:00:00

ENTRY_LOCATION=/ocean/projects/sys890003p/spagaria/project1/dana

tar xvzf merged_dataset_ocelot.tgz

python3 create_regression_csv.py --data_dir Merged_Dataset/OCELOT --encoding materials_string --outdir regression_OCELOT/ms_OCELOT --train_val_split 0.8

tar cvzf ${ENTRY_LOCATION}/regression_OCELOT__ms_OCELOT.tgz --directory=${ENTRY_LOCATION}/ regression_OCELOT/ms_OCELOT