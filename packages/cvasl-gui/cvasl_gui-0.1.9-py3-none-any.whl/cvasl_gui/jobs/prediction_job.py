import sys
import os
import traceback
import zipfile
import json
import numpy as np
import pandas as pd

from cvasl.prediction import PredictBrainAge
from cvasl.dataset import MRIdataset, encode_cat_features

from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, ElasticNetCV
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR

# Monkey patch to fix the DataFrame ambiguity bug
def _fixed_store_fold_predictions(self, fold_index, y_test, y_pred, y_val, y_pred_val, test_index):
    """Fixed version of _store_fold_predictions that handles DataFrame ambiguity properly."""
    import pandas as pd
    
    # Ensure arrays are properly flattened only if needed
    y_test_flat = y_test.flatten() if hasattr(y_test, 'flatten') else y_test
    y_pred_flat = y_pred.flatten() if hasattr(y_pred, 'flatten') else y_pred
    
    predictions_data = pd.DataFrame({'y_test': y_test_flat, 'y_pred': y_pred_flat})
    predictions_data[self.patient_identifier] = self.data[self.patient_identifier].values[test_index]
    predictions_data['site'] = self.data[self.site_indicator].values[test_index]
    predictions_data['fold'] = fold_index
    
    predictions_data_val = None
    if y_val is not None and y_pred_val is not None and self.data_validation is not None:
        y_val_flat = y_val.flatten() if hasattr(y_val, 'flatten') else y_val
        y_pred_val_flat = y_pred_val.flatten() if hasattr(y_pred_val, 'flatten') else y_pred_val
        
        predictions_data_val = pd.DataFrame({'y_test': y_val_flat, 'y_pred': y_pred_val_flat})
        predictions_data_val[self.patient_identifier] = self.data_validation[self.patient_identifier].values
        predictions_data_val['site'] = self.data_validation[self.site_indicator].values
        predictions_data_val['fold'] = fold_index
    
    return predictions_data, predictions_data_val

# Apply the monkey patch
PredictBrainAge._store_fold_predictions = _fixed_store_fold_predictions


# Argument is the job id (input and parameters(?) are inside the job folder)

WORKING_DIR = os.getenv("CVASL_WORKING_DIRECTORY", ".")
INPUT_DIR = os.path.join(WORKING_DIR, 'data')
JOBS_DIR = os.path.join(WORKING_DIR, 'jobs')

prediction_models = {
  "extratrees": {
    "label": "Extra Trees Regressor",
    "class": ExtraTreesRegressor,
    "parameters": {
        "n_estimators": 100,
        "random_state": np.random.randint(0,100000),
        "criterion": 'absolute_error',
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": 'log2',
        "bootstrap": False,
        "n_jobs": -1,
        "warm_start": True
    }
  },
  "gradientboosting": {
    "label": "Gradient Boosting Regressor",
    "class": GradientBoostingRegressor,
    "parameters": {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 3,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "subsample": 1.0,
        "random_state": np.random.randint(0, 100000),
        "loss": 'squared_error'
    }
  },
  "linearregression": {
    "label": "Linear Regression",
    "class": LinearRegression,
    "parameters": {
        "fit_intercept": True,
        "n_jobs": -1
    }
  },
  "elasticnetcv": {
    "label": "Elastic Net CV",
    "class": ElasticNetCV,
    "parameters": {
        "l1_ratio": [0.1, 0.5, 0.7, 0.9, 0.95, 0.99, 1],
        "alphas": None,  # Automatically determined
        "cv": 5,
        "max_iter": 1000,
        "tol": 0.0001,
        "random_state": np.random.randint(0, 100000),
        "n_jobs": -1
    }
  },
  "decisiontree": {
    "label": "Decision Tree Regressor", 
    "class": DecisionTreeRegressor,
    "parameters": {
        "max_depth": None,  # No limit
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": None,  # Use all features
        "random_state": np.random.randint(0, 100000),
        "splitter": 'best'
    }
  },
  "svr": {
    "label": "Support Vector Regression",
    "class": SVR,
    "parameters": {
        "kernel": 'rbf',
        "C": 1.0,
        "epsilon": 0.1,
        "gamma": 'scale',
        "tol": 0.001,
        "cache_size": 200,
        "max_iter": -1  # No limit
    }
  }
}

def write_job_status(job_id: str, status: str) -> None:
    """ Write the status of the job to a file (for use in the GUI)
    """
    status_path = os.path.join(JOBS_DIR, job_id, "job_status")
    with open(status_path, "w") as f:
        f.write(status)


def zip_job_output(job_id):
    """Create a ZIP file for job output if not already zipped"""
    output_folder = os.path.join(JOBS_DIR, job_id, 'output')
    zip_path = os.path.join(JOBS_DIR, job_id, 'output.zip')

    if not os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(output_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, arcname=os.path.relpath(file_path, output_folder))


def run_prediction() -> None:
    """Run the prediction process"""
    
    print("=" * 80)
    print("STARTING PREDICTION JOB")
    print("=" * 80)

    # Load job arguments
    print("\n[1/10] Loading job arguments...")
    job_arguments_path = os.path.join(JOBS_DIR, job_id, "job_arguments.json")
    with open(job_arguments_path) as f:
        job_arguments = json.load(f)
    print(f"   ✓ Job arguments loaded from: {job_arguments_path}")

    model_name = job_arguments["model_name"]
    train_paths = job_arguments["train_paths"]
    train_names = [ os.path.splitext(os.path.basename(path))[0] for path in train_paths ]
    train_sites = job_arguments["train_sites"]
    validation_paths = job_arguments["validation_paths"]
    validation_names = [ os.path.splitext(os.path.basename(path))[0] for path in validation_paths ]
    validation_sites = job_arguments["validation_sites"]
    prediction_features = job_arguments["prediction_features"]
    prediction_features = [x.lower() for x in prediction_features]
    prediction_parameters = job_arguments["parameters"]
    
    label = job_arguments["label"]
    if label is None or label == "":
        label = "predicted"

    print(f"   Model: {model_name}")
    print(f"   Training datasets: {len(train_paths)}")
    print(f"   Validation datasets: {len(validation_paths)}")
    print(f"   Features: {prediction_features}")

    # Load the training datasets into pandas dataframes and concatenate them
    print("\n[2/10] Loading and concatenating training data...")
    train_dfs = [pd.read_csv(path) for path in train_paths]
    train_dfs = pd.concat(train_dfs, ignore_index=True)
    print(f"   ✓ Loaded {len(train_dfs)} training samples")
    
    print("\n[3/10] Loading and concatenating validation data...")
    validation_dfs = [pd.read_csv(path) for path in validation_paths]
    validation_dfs = pd.concat(validation_dfs, ignore_index=True)
    print(f"   ✓ Loaded {len(validation_dfs)} validation samples")

    # Prepare train datasets
    print("\n[4/10] Preparing training datasets...")
    mri_datasets_train = [MRIdataset(input_path, input_site, "participant_id", features_to_drop=[])
                          for input_site, input_path in zip(train_sites, train_paths) ]
    print(f"   ✓ Created {len(mri_datasets_train)} MRIdataset objects")
    
    print("\n[5/10] Preprocessing training datasets...")
    for i, mri_dataset in enumerate(mri_datasets_train):
        print(f"   Processing dataset {i+1}/{len(mri_datasets_train)}...")
        mri_dataset.preprocess()
    print("   ✓ Preprocessing complete")
    
    print("\n[6/10] Encoding categorical features for training data...")
    features_to_map = ['sex']
    encode_cat_features(mri_datasets_train, features_to_map)
    print("   ✓ Categorical features encoded")

    # Prepare test/validation datasets
    print("\n[7/10] Preparing validation datasets...")
    mri_datasets_validation = [MRIdataset(input_path, input_site, "participant_id", features_to_drop=[])
                               for input_site, input_path in zip(validation_sites, validation_paths) ]
    print(f"   ✓ Created {len(mri_datasets_validation)} validation MRIdataset objects")
    
    for i, mri_dataset in enumerate(mri_datasets_validation):
        print(f"   Processing validation dataset {i+1}/{len(mri_datasets_validation)}...")
        mri_dataset.preprocess()
    print("   ✓ Validation preprocessing complete")
    
    features_to_map = ['sex']
    encode_cat_features(mri_datasets_validation, features_to_map)
    print("   ✓ Validation categorical features encoded")

    # Instantiate the model
    print(f"\n[8/10] Instantiating model: {model_name}...")
    model_class = prediction_models.get(model_name).get("class")
    print(f"   Model class: {model_class.__name__}")
    print(f"   Parameters: {prediction_parameters}")
    model = model_class(**prediction_parameters)
    print("   ✓ Model instantiated successfully")

    # Try to avoid the DataFrame ambiguity error by handling validation datasets carefully
    validation_datasets = mri_datasets_validation if mri_datasets_validation else None
    
    # Instantiate the predictor
    print("\n[9/10] Creating PredictBrainAge predictor...")
    predicter = PredictBrainAge(model_name=model_name, model_file_name=model_name, model=model,
                                datasets=mri_datasets_train, datasets_validation=validation_datasets, features=prediction_features,
                                target='age', cat_category='sex', cont_category='age', n_bins=2, splits=1, test_size_p=0.05, random_state=42)
    print("   ✓ Predictor created successfully")

    # Perform training and prediction
    print("\n[10/10] Running prediction (this may take a while)...")
    print("   Training model and making predictions...")
    sys.stdout.flush()  # Force output to be written
    
    metrics_df, metrics_df_val, predictions_df, predictions_df_val, models = predicter.predict()
    
    print("   ✓ Prediction complete!")

    # Some final processing & Write output
    print("\nWriting output files...")
    output_folder = os.path.join(JOBS_DIR, job_id, 'output')
    os.makedirs(output_folder, exist_ok=True)
    print(f"   Output folder: {output_folder}")
    
    # Save metrics
    if metrics_df is not None:
        metrics_path = os.path.join(output_folder, f"metrics_train_{label}.csv")
        metrics_df.to_csv(metrics_path, index=False)
        print(f"   ✓ Saved training metrics: {metrics_path}")
    if metrics_df_val is not None:
        metrics_val_path = os.path.join(output_folder, f"metrics_validation_{label}.csv")
        metrics_df_val.to_csv(metrics_val_path, index=False)
        print(f"   ✓ Saved validation metrics: {metrics_val_path}")
    
    # Process and save predictions
    if predictions_df is not None:
        # Add age_gap calculation if both age columns exist
        df = predictions_df.copy()
        if 'y_pred' in df.columns and 'y_test' in df.columns:
            df['age_gap'] = df['y_pred'] - df['y_test']
            df['age_predicted'] = df['y_pred']
            df['age'] = df['y_test']
        df['label'] = label
        pred_path = os.path.join(output_folder, f"predictions_train_{label}.csv")
        df.to_csv(pred_path, index=False)
        print(f"   ✓ Saved training predictions: {pred_path}")
    
    if predictions_df_val is not None:
        # Add age_gap calculation if both age columns exist
        df = predictions_df_val.copy()
        if 'y_pred' in df.columns and 'y_test' in df.columns:
            df['age_gap'] = df['y_pred'] - df['y_test']
            df['age_predicted'] = df['y_pred']
            df['age'] = df['y_test']
        df['label'] = label
        pred_val_path = os.path.join(output_folder, f"predictions_validation_{label}.csv")
        df.to_csv(pred_val_path, index=False)
        print(f"   ✓ Saved validation predictions: {pred_val_path}")
    
    print("\n" + "=" * 80)
    print("PREDICTION JOB COMPLETED SUCCESSFULLY")
    print("=" * 80)


def get_column_case_insensitive(df, colname):
    match = [c for c in df.columns if c.lower() == colname.lower()]
    if not match:
        raise KeyError(f"Column '{colname}' not found.")
    return df[match[0]]


def process(job_id: str) -> None:
    print(f"\n{'='*80}")
    print(f"INITIALIZING JOB: {job_id}")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    write_job_status(job_id, "running")

    try:
        run_prediction()
        
        print("\nCreating output archive...")
        sys.stdout.flush()

        # Zip the output
        zip_job_output(job_id)
        print("✓ Output archive created successfully")
        sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n\nJob interrupted by user")
        sys.stdout.flush()
        write_job_status(job_id, "cancelled")
        with open(os.path.join(JOBS_DIR, job_id, "error.log"), "w") as f:
            f.write("Job cancelled by user\n")
        return
        
    except Exception as e:
        print(f"\n\n{'='*80}")
        print("ERROR: Job failed with exception")
        print(f"{'='*80}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        print(f"{'='*80}\n")
        sys.stdout.flush()
        sys.stderr.flush()
        
        write_job_status(job_id, "failed")
        with open(os.path.join(JOBS_DIR, job_id, "error.log"), "w") as f:
            f.write(f"Exception type: {type(e).__name__}\n")
            f.write(f"Exception message: {str(e)}\n\n")
            f.write("Full traceback:\n")
            f.write(traceback.format_exc())
        return
    
    write_job_status(job_id, "completed")
    print(f"\n{'='*80}")
    print(f"JOB COMPLETED: {job_id}")
    print(f"{'='*80}\n")
    sys.stdout.flush()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("ERROR: No job ID provided")
        print("Usage: python prediction_job.py <job_id>")
        sys.exit(1)
    
    job_id = sys.argv[1]
    process(job_id)
