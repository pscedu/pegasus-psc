# Intro Notes

## Reference Repository

`https://github.com/pscedu/danaoconnor/tree/main/ShreyaSummerProject`

## For Pegasus Workflow
Across all the directories to be consistent I have used the example of OCELOT dataset with materials_string as the text representation

![Pegasus Workflow Diagram](images/psc-workflow-0-abstract-files.png?raw=true)

## Requirements
    * Encoding folder
    * Tokenizer folder
    * Run pre-regression script for preprocessing the downstream data.

## For Running the Workflow
1. SSH into neocortex (`ssh USERNAME@neocortex.psc.edu`)
2. Generate SSH keys for being able to connect to the secondary cluster:
   1. ssh-keygen -t ed25519 -f ~/.pegasus/wfsshkey -C "SSH Key for Pegasus Workflows $USER"
   2. add wfsshkey.pub to your authorized keys on the secondary cluster: (Copy the contents of `~/.pegasus/wfsshkey.pub` into Bridges-2 using `ssh-copy-id -i ~/.pegasus/wfsshkey.pub USERNAME@bridges2.psc.edu`)
4. Start job on Pegasus partition (`srun --ntasks=1 --account=PROJECT_ID --partition=pegasus --pty bash`)
5. Activate virtual environment (`source ~/_projects/neocortex/pegasus/.venv/bin/activate`)
6. Get the repository files (`git clone https://github.com/pscedu/pegasus-psc.git`)
7. Change into the repository (`cd pegasus-psc/psc-workflow/`)
8. Run the Pegasus workflow (`python3 main.py --project PROJECT_ID`)
9. Check the workflow status (`pegasus-status -l submit/julian/pegasus/psc-workflow/run0001`)
10. For taking at errors (`pegasus-analyzer -l submit/julian/pegasus/psc-workflow/run0001`)
