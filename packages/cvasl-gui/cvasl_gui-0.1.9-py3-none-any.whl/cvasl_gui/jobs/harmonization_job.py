import sys
import os
import traceback
import zipfile
import json

from cvasl.harmonizers import NeuroCombat, NeuroHarmonize, Covbat, NestedComBat, \
                              AutoCombat, RELIEF
from cvasl.dataset import MRIdataset, encode_cat_features


# Argument is the job id (input and parameters(?) are inside the job folder)

WORKING_DIR = os.getenv("CVASL_WORKING_DIRECTORY", ".")
INPUT_DIR = os.path.join(WORKING_DIR, 'data')
JOBS_DIR = os.path.join(WORKING_DIR, 'jobs')

harmonizers = {
    "neurocombat": NeuroCombat,
    "neuroharmonize": NeuroHarmonize,
    "covbat": Covbat,
    "nestedcombat": NestedComBat,
    "autocombat": AutoCombat,
    "relief": RELIEF
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


def run_harmonization() -> None:
    """Run the harmonization process"""

    # Load job arguments
    job_arguments_path = os.path.join(JOBS_DIR, job_id, "job_arguments.json")
    with open(job_arguments_path) as f:
        job_arguments = json.load(f)

    input_paths = job_arguments["input_paths"]
    input_names = [ os.path.splitext(os.path.basename(path))[0] for path in input_paths ]
    input_sites = job_arguments["input_sites"]

    harmonization_parameters = job_arguments["parameters"]

    label = job_arguments["label"]
    if label is None or label == "":
        label = "harmonized"

    print("Running harmonization")
    print("Input paths:", input_paths)
    print("Parameters:", harmonization_parameters)

    # Create the datasets
    mri_datasets = [MRIdataset(input_path, input_site, "participant_id", features_to_drop=[])
                    for input_site, input_path in zip(input_sites, input_paths) ]
    for mri_dataset in mri_datasets:
        mri_dataset.preprocess()
    features_to_map = ['sex']
    encode_cat_features(mri_datasets, features_to_map)

    # Instantiate the correct harmonizer
    harmonizer_class = harmonizers.get(job_arguments["algorithm"])
    harmonizer = harmonizer_class(**harmonization_parameters)

    # Perform the harmonization
    output = harmonizer.harmonize(mri_datasets)

    # Prepare the output datasets and add the label column
    for dataset in output:
        dataset.prepare_for_export()
    dfs = [dataset.data for dataset in output]
    for df in dfs:
        df['label'] = label

    # Write output
    output_folder = os.path.join(JOBS_DIR, job_id, 'output')
    os.makedirs(output_folder, exist_ok=True)
    for i, df in enumerate(dfs):
        df.to_csv(os.path.join(output_folder, f"{input_names[i]}_{label}.csv"), index=False)


def process(job_id: str) -> None:
    write_job_status(job_id, "running")
    print("Processing job", job_id)

    try:
        run_harmonization()

        # Zip the output
        zip_job_output(job_id)

    except Exception as e:
        write_job_status(job_id, "failed")
        with open(os.path.join(JOBS_DIR, job_id, "error.log"), "w") as f:
            f.write(traceback.format_exc())
        return
    
    write_job_status(job_id, "completed")


if __name__ == '__main__':
    job_id = sys.argv[1]
    process(job_id)
