#! /bin/bash

set -e

TOP_DIR=`pwd`


echo "Cloning the modelzoo repository into ./input"
mkdir -p input
cd input

rm -rf ./modelzoo
rsync -PaL /ocean/neocortex/cerebras/modelzoo ./
chmod u+w -R ./modelzoo

# remove the params.yaml file as we track it as a separate input to the wf
echo "Removing params.yaml from pytorch config dir"
rm ./modelzoo/modelzoo/fc_mnist/pytorch/configs/params.yaml

tarfile=$TOP_DIR/input/modelzoo-raw.tgz
echo "Tarring up the git checkout to $tarfile"
tar zcf $tarfile ./modelzoo
rm -rf modelzoo



