# Cerebras ModelZoo Training Workflow

This Pegasus workflow validates, compiles and trains the model
using Tensor Flow as part of a single worklfow setup to run on Neocortex.


[Running Jobs on Neocortex](https://portal.neocortex.psc.edu/docs/running-jobs.html) 


## Container
All the jobs are run via a Cerebras provided singularity container that is 
available on the shared filesystem.


## Setting up the input data for the workflow 


 ```
 $  ./executables/prepare_inputs.sh 
 Cloning the modelzoo repository into ./input
 Cloning into 'modelzoo'...
 ...
 HEAD is now at 886a438... R_1.6.0
  Tarring up the git checkout to /jet/home/vahi/work/cerebras-modelzoo/input/modelzoo-raw.tgz
 ```
 The workflow also requires additional inputs to be placed in the input directory.
 These are the inputs on which you do the training 

 * modelzoo/modelzoo/fc_mnist/tf/tfds/mnist/3.0.1/dataset_info.json
 * modelzoo/modelzoo/fc_mnist/tf/tfds/mnist/3.0.1/features.json
 * modelzoo/modelzoo/fc_mnist/tf/tfds/mnist/3.0.1/mnist-test.tfrecord-00000-of-00001
 * modelzoo/modelzoo/fc_mnist/tf/tfds/mnist/3.0.1/mnist-train.tfrecord-00000-of-00001

 These are checked into the input directory for the example workflow.

## Workflow

The Pegasus workflow starts with a tar file containing the Git checkout of 
the modelzoo repo, and iterates on it

![Pegasus Cerebras ModelZoo PyTorch Training Example Workflow ](./images/workflow.png)

### Running the workflow

You can run the workflow from neocortex login node as follow

```
$./cerebras-modelzoo-tf.py --project $SALLOC_ACCOUNT
```
