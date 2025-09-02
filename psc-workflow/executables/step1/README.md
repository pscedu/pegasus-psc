Step 1 (on Neocortex): Pre-training RoBERTa

Using the Cerebras model zoo, we’re pre-training a RoBERTa transformer on a dataset of material strings (or a similar dataset).

Files in step1.zip:
    * Batch script: `run_pretrain.sh`
    * Python files: `prepare_tokenization.py`, `create_csv_mlm_only.py`, `run_roberta.py`

Notes:
    * The batch script currently only supports training mode (not evaluation).
    * Paths/directories need to be updated in both the script and the provided .yaml file.