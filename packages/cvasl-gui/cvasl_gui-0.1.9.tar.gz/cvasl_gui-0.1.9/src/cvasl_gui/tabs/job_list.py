import dash
from dash import dcc, html, Input, Output, State, ctx, MATCH, ALL
import os
import sys
import time
import subprocess
import json
import signal
import traceback

from cvasl_gui.app import app


# Folder where job output files are stored
WORKING_DIR = os.getenv("CVASL_WORKING_DIRECTORY", ".")
INPUT_DIR = os.path.join(WORKING_DIR, 'data')
JOBS_DIR = os.path.join(WORKING_DIR, 'jobs')



def create_job_list():
    return html.Div([
        html.Div(id="job-status"),
        dcc.Loading(
            id="loading-1",
            type="circle",
            children=html.Div(id="loading-output-job-status")
        ),
        dcc.Interval(id="interval-check", interval=3000, n_intervals=0),
        dcc.Download(id="download-data")
    ])

def run_job(job_arguments: dict, job_id: str, is_harmonization: bool = True):
    """Function to start the harmonization job"""

    # Create a unique folder for the job
    job_folder = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    # Set the intermediate results path to the job's directory
    if "intermediate_results_path" in job_arguments["parameters"]:
        job_arguments["parameters"]["intermediate_results_path"] = job_folder

    # Save job arguments
    with open(os.path.join(job_folder, "job_arguments.json"), "w") as f:
        json.dump(job_arguments, f)

    # Start the job
    print("Starting job", job_id)
    if is_harmonization:
        script_path = os.path.join(os.path.dirname(__file__), "..", "jobs", "harmonization_job.py")
    else:
        script_path = os.path.join(os.path.dirname(__file__), "..", "jobs", "prediction_job.py")
    
    # Start process with output redirected to files
    try:
        print(f"Running script: {script_path} with job ID: {job_id}")
        
        # Create output files for stdout and stderr
        stdout_file = os.path.join(job_folder, "stdout.log")
        stderr_file = os.path.join(job_folder, "stderr.log")
        
        with open(stdout_file, "w") as stdout_f, open(stderr_file, "w") as stderr_f:
            process = subprocess.Popen(
                [sys.executable, script_path, job_id],
                stdout=stdout_f,
                stderr=stderr_f,
                text=True
            )
        print(f"Started process with PID: {process.pid}")
        
        # Give the process a moment to start and check for immediate failures
        time.sleep(1)
        poll_result = process.poll()

        print(f"Process poll result: {poll_result}")
        
        if poll_result is not None and poll_result != 0:
            # Process has already exited with non-zero code - this indicates a startup error
            error_msg = f"Process failed to start (exit code {poll_result})\n"
            
            # Read stderr and stdout from files if they exist
            if os.path.exists(stderr_file):
                with open(stderr_file, "r") as f:
                    stderr_content = f.read()
                    if stderr_content:
                        error_msg += f"Error output:\n{stderr_content}\n"
            
            if os.path.exists(stdout_file):
                with open(stdout_file, "r") as f:
                    stdout_content = f.read()
                    if stdout_content:
                        error_msg += f"Standard output:\n{stdout_content}\n"
            
            # Write error to log file
            error_log_path = os.path.join(job_folder, "error.log")
            with open(error_log_path, "w") as f:
                f.write(error_msg)
            
            # Write failed status
            status_file = os.path.join(job_folder, "job_status")
            with open(status_file, "w") as f:
                f.write("failed")
            
            print(f"Job {job_id} failed to start: {error_msg}")
        elif poll_result == 0:
            # Process completed successfully very quickly
            print(f"Job {job_id} completed successfully")
            
        # Save job details (so it can be monitored)
        job_details = {
            "id": job_id,
            "process": process.pid,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "startup_error": poll_result is not None
        }
        with open(os.path.join(job_folder, "job_details.json"), "w") as f:
            json.dump(job_details, f)
            
    except Exception as e:
        # Handle case where subprocess.Popen itself fails
        error_msg = f"Failed to create subprocess: {str(e)}\n{traceback.format_exc()}"
        
        # Write error to log file
        error_log_path = os.path.join(job_folder, "error.log")
        with open(error_log_path, "w") as f:
            f.write(error_msg)
        
        # Write failed status
        status_file = os.path.join(job_folder, "job_status")
        with open(status_file, "w") as f:
            f.write("failed")
        
        print(f"Job {job_id} failed to start: {error_msg}")
        
        # Save job details indicating failure
        job_details = {
            "id": job_id,
            "process": None,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "startup_error": True
        }
        with open(os.path.join(job_folder, "job_details.json"), "w") as f:
            json.dump(job_details, f)



def check_job_status():
    """Check if jobs are still running and return their details"""
    job_data = []
    job_dirs = sorted(os.listdir(JOBS_DIR), reverse=True)

    for job_dir in job_dirs:
        job_details_file = os.path.join(JOBS_DIR, job_dir, "job_details.json")
        job_arguments_file = os.path.join(JOBS_DIR, job_dir, "job_arguments.json")
        if os.path.exists(job_details_file):
            # Load the job details
            with open(job_details_file) as f:
                details = json.load(f)

            # Load current status
            status_file = os.path.join(JOBS_DIR, job_dir, "job_status")
            if os.path.exists(status_file):
                with open(status_file) as f:
                    details["status"] = f.read().strip()
            else:
                # No status file yet, determine status based on process state
                process_id = details.get("process")
                if process_id and is_process_running(process_id):
                    details["status"] = "running"
                else:
                    # Process not running and no status file - check for early exit
                    error_log_file = os.path.join(JOBS_DIR, job_dir, "error.log")
                    if os.path.exists(error_log_file):
                        details["status"] = "failed"
                    elif details.get("startup_error", False):
                        details["status"] = "failed"
                    else:
                        details["status"] = "unknown"

            # Check if process is still running
            process_id = details.get("process")
            details["running"] = is_process_running(process_id) if process_id else False

            # Load error log if it exists
            error_log_file = os.path.join(JOBS_DIR, job_dir, "error.log")
            if os.path.exists(error_log_file):
                with open(error_log_file) as f:
                    details["error_log"] = f.read()

            # Load job arguments
            if os.path.exists(job_arguments_file):
                with open(job_arguments_file) as f:
                    job_arguments = json.load(f)
                    details["arguments"] = job_arguments

            job_data.append(details)

    return job_data

def get_job_status(job_id):
    """Return the job status"""
    status = "running"

    status_file = os.path.join(JOBS_DIR, job_id, "job_status")
    if os.path.exists(status_file):
        with open(status_file) as f:
            status = f.read()

    return status

def cancel_job(job_id):
    """Terminate a running job"""
    job_details_file = os.path.join(JOBS_DIR, job_id, "job_details.json")
    if os.path.exists(job_details_file):
        with open(job_details_file) as f:
            details = json.load(f)

        process_id = details.get("process")
        if os.path.exists(f"/proc/{process_id}"):
            os.kill(process_id, signal.SIGTERM)  # Send termination signal
            details["status"] = "cancelled"
            with open(job_details_file, "w") as f:
                json.dump(details, f)

def remove_job(job_id):
    """Delete job folder"""
    job_folder = os.path.join(JOBS_DIR, job_id)
    if os.path.exists(job_folder):
        for root, dirs, files in os.walk(job_folder, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(job_folder)

def is_process_running(pid):
    """Check if a process is running"""
    if pid is None:
        return False
    try:
        result = subprocess.run(["ps", "-p", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0  # Return True if process is found
    except Exception as e:
        print(f"Error checking process: {e}")
        return False


@app.callback(
    Output("job-status", "children"),
    Input("interval-check", "n_intervals"),
    Input({"type": "cancel-job", "index": ALL}, "n_clicks"),
    Input({"type": "remove-job", "index": ALL}, "n_clicks"),
    State({"type": "cancel-job", "index": ALL}, "id"),
    State({"type": "remove-job", "index": ALL}, "id")
)
def start_or_monitor_job(n_intervals, cancel_clicks, remove_clicks, cancel_ids, remove_ids):
    """Starts a new job, updates job status table, handles job cancellations and removals"""

    triggered_id = ctx.triggered_id

    # Handle job cancellation
    if triggered_id and isinstance(triggered_id, dict) and triggered_id["type"] == "cancel-job":
        cancel_job(triggered_id["index"])

    # Handle job removal
    if triggered_id and isinstance(triggered_id, dict) and triggered_id["type"] == "remove-job":
        remove_job(triggered_id["index"])

    # Monitor job output
    job_data = check_job_status()

    table_header = html.Tr([
        html.Th("Start time"),
        html.Th("Type"),
        html.Th("Algorithm / Model"),
        html.Th("Arguments"),
        html.Th("Status"),
        html.Th("Actions")
    ])

    # On select: download, remove

    table_rows = []
    for job in job_data:
        # Determine job type and algorithm/model
        job_args = job.get("arguments", {})
        job_type = job_args.get("type", "harmonization" if "algorithm" in job_args else "prediction")
        
        # Get algorithm/model from parameters
        if job_type == "harmonization":
            algorithm = job_args.get("algorithm", "Unknown")
        elif job_type == "prediction":
            algorithm = job_args.get("model_name", "Unknown")
        else:
            algorithm = "N/A"
        
        # Create status cell with error details if available
        status_content = job.get("status", "")
        if job.get("error_log") and job.get("status") == "failed":
            # Show a collapsible error details
            status_content = html.Div([
                html.Span("failed", style={"color": "red"}),
                html.Details([
                    html.Summary("Show error details", style={"cursor": "pointer", "marginTop": "5px", "fontSize": "12px", "color": "#6c757d"}),
                    html.Pre(job["error_log"], style={
                        "background": "#f8f9fa",
                        "padding": "10px",
                        "border": "1px solid #dee2e6",
                        "borderRadius": "4px",
                        "maxHeight": "300px",
                        "overflow": "auto",
                        "whiteSpace": "pre-wrap",
                        "fontSize": "12px",
                        "marginTop": "5px",
                        "color": "#212529"
                    })
                ])
            ])
        elif job.get("status") == "failed":
            status_content = html.Span("failed", style={"color": "red"})
        elif job.get("status") == "completed":
            status_content = html.Span("completed", style={"color": "green"})
        elif job.get("running"):
            status_content = html.Span("running", style={"color": "blue"})
        
        # Create actions cell
        actions = []
        if job.get("status", "") in ("completed", "failed"):
            actions.append(html.Button("Download", id={"type": "download-output", "index": job["id"]}, n_clicks=0, style={"margin-right": "5px"}))
        if job.get("running", False):
            actions.append(html.Button("Cancel", id={"type": "cancel-job", "index": job["id"]}, n_clicks=0, style={"margin-right": "5px"}))
        if not job.get("running", False):
            actions.append(html.Button("Remove", id={"type": "remove-job", "index": job["id"]}, n_clicks=0, style={"margin-right": "5px"}))
        
        # Create inputs cell with collapsible arguments
        input_paths = job_args.get("input_paths", [])
        inputs_display = html.Div([
            html.Div(", ".join([os.path.basename(p) for p in input_paths]) if input_paths else "N/A"),
            html.Details([
                html.Summary("Show all arguments", style={"cursor": "pointer", "marginTop": "5px", "fontSize": "12px", "color": "#6c757d"}),
                html.Pre(json.dumps(job_args, indent=2), style={
                    "background": "#f8f9fa",
                    "padding": "10px",
                    "border": "1px solid #dee2e6",
                    "borderRadius": "4px",
                    "maxHeight": "300px",
                    "overflow": "auto",
                    "whiteSpace": "pre-wrap",
                    "fontSize": "12px",
                    "marginTop": "5px",
                    "color": "#212529"
                })
            ])
        ])
        
        table_rows.append(html.Tr([
            html.Td(job.get("start_time", "")),
            html.Td(job_type.capitalize()),
            html.Td(algorithm),
            html.Td(inputs_display),
            html.Td(status_content),
            html.Td(actions)
        ]))

    table_style = {
        "width": "100%",
        "border-collapse": "collapse",
        "font-size": "18px",
        "box-shadow": "0 1px 3px rgba(0,0,0,0.1)"
    }
    
    return html.Table(
        [table_header] + table_rows,
        style=table_style,
        className="job-table"
    )


@app.callback(
    Output("download-data", "data"),
    Input({"type": "download-output", "index": ALL}, "n_clicks"),
    State({"type": "download-output", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def func(n_clicks, ids):
    if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
        return dash.no_update  # Prevent unnecessary execution

    triggered_id = ctx.triggered_id
    if triggered_id["type"] == "download-output":

        # Ensure the button was actually clicked this time
        job_id = triggered_id["index"]
        index = [id["index"] for id in ids].index(job_id)
        if n_clicks[index] > 0:
            path = os.path.join(JOBS_DIR, job_id, "output.zip")
            return dcc.send_file(path)

    return dash.no_update  # Avoid unwanted triggers
