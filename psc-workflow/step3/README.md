Step 3 (on Bridges-2): Optional Model Evaluation

Evaluate the model on unseen data (e.g., the Huang-Massa dataset) in later testing phases.

Files in step3.zip:
    * Batch script: `run_inference.sh`

Notes:
    * This script takes `checkpoint_path` and `outfile` as command-line arguments.
    * `checkpoint_path` should point to the trained model from step 2.
    * `outfile` will be a JSON file containing model predictions and true labels.

Step 3: For this step adding both scripts but if it is to evaluate on unseen data, inference mode is recommended
If evaluation mode, I created a new script called run_regression_eval.sh uses the script attached in Step 2 "run_regression.py".
For evaluating on unseen data use: inference mode, there is run_inference.sh that uses run_inference.py