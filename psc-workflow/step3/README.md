Step 3 (on Bridges-2): Optional Model Evaluation

Evaluate the model on unseen data (e.g., the Huang-Massa dataset) in later testing phases.

Files in step3.zip:
    * Batch script: `run_inference.sh`

Notes:
    * This script takes `checkpoint_path` and `outfile` as command-line arguments.
    * `checkpoint_path` should point to the trained model from step 2.
    * `outfile` will be a JSON file containing model predictions and true labels.