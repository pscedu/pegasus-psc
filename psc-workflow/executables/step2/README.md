Step 2 (on Bridges-2): Regression Head for Transfer Learning

We attach a regression head to the pre-trained model to predict molecular volume.

Files in step2.zip:
    * Batch script: `run_regression.sh`
    * Supporting files: `create_regression_csv.py`, `regression_params.yaml`

Notes:
    * Again, directory paths will need to be adjusted in the script and the YAML config.


creating the regression data using run_regression_data.sh script which also uses create_regression_csv.py file.
Then we move to the main REGRESSION STEP which requires run_regression.sh script which also requires run_regression.py and regression_params.yaml