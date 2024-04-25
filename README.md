# Cerebras ModelZoo Training Workflow

This repository contains example Pegasus workflows that execute on the Cerebras machine at PSC called Neocortex. The examples are for some of the models in the [modelzoo](https://portal.neocortex.psc.edu/docs/modelzoo.html) that Cerebras has made availble for users to run. 

The workflows in this repository validate, compiles and trains the model.

At the moment we have example workflows for 

* Tensor Flow
* PyTorch 

The workflow is based on the example at 
[Running Jobs on Neocortex](https://portal.neocortex.psc.edu/docs/running-jobs.html) .


## Dependencies

1. Install [HTCondor](https://htcondor.readthedocs.io/en/latest/getting-htcondor/)
2. Install [Pegasus WMS](https://pegasus.isi.edu/documentation/user-guide/installation.html)

You can also refer to the overview on [deployment options](https://pegasus.isi.edu/docs/5.0.8dev/user-guide/deployment-scenarios.html#hpc-clusters-system-install) 
and select what works best for your setup.

## Container
All the jobs are run via a Cerebras provided singularity container that is 
available on the shared filesystem.
