# Cerebras ModelZoo Training Workflow

This Pegasus workflow validates, compiles and trains the model
using Tensor Flow as part of a single worklfow setup to run on Neocortex.


[Running Jobs on Neocortex]([https://datacarpentry.org/wrangling-genomics/05-automation/index.html](https://portal.neocortex.psc.edu/docs/running-jobs.html)) 

## Container
All the jobs are run via a Cerebras provided singularity container that is 
available on the shared filesystem.

## Workflow

The Pegasus workflow starts with a tar file containing the Git checkout of 
the modelzoo repo, and iterates on it

![Pegasus Cerebras ModelZoo Training Example Workflow ](/images/workflow.png)
