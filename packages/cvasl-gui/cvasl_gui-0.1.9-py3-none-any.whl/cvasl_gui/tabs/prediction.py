import time
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import os
import json
import threading

from cvasl_gui.app import app
from cvasl_gui.tabs.job_list import run_job
from cvasl_gui import data_store
from cvasl_gui.components.directory_input import create_directory_input
from cvasl_gui.components.data_table import create_data_table
from cvasl_gui.components.feature_compare2 import create_feature_compare
from cvasl_gui.tabs.job_list import create_job_list, get_job_status

from cvasl_gui.jobs.prediction_job import prediction_models


# Folder where job output files are stored
WORKING_DIR = os.getenv("CVASL_WORKING_DIRECTORY", ".")
INPUT_DIR = os.path.join(WORKING_DIR, 'data')
JOBS_DIR = os.path.join(WORKING_DIR, 'jobs')


def create_tab_prediction():
    return html.Div([
        dbc.Accordion([
            dbc.AccordionItem([create_directory_input('prediction-training')],
                title="Select training data"),
            dbc.AccordionItem([create_data_table('prediction-training')],
                title="Inspect training data"),
            dbc.AccordionItem([create_directory_input('prediction-testing')],
                title="Select testing data"),
            dbc.AccordionItem([create_data_table('prediction-testing')],
                title="Inspect testing data"),
            dbc.AccordionItem([create_feature_compare()],
                title="Feature comparison"),
            dbc.AccordionItem(create_prediction_parameters(),
                title="Prediction"),
            dcc.Store(id="prediction-job-id", data=None),
        ], always_open=True)
    ])


def get_dataframe_columns():
    df = data_store.all_data['prediction-training']
    if df is None:
        return []
    return df.columns


def create_prediction_parameters():
    return [
        # Row for model selection
        dbc.Row([
            dbc.Col(html.Label("Model:", style={"marginTop": "6px"}), width=3),
            dbc.Col(
                dcc.Dropdown(
                    id="model-dropdown",
                    options=[{"label": v["label"], "value": k} for k, v in prediction_models.items()],
                    value="extratrees",
                    clearable=False,
                ),
            ),
        ], className="mb-3"),

        # Row for main feature selection
        dbc.Row([
            dbc.Col(html.Label("Features:", style={"marginTop": "6px"}), width=3),
            dbc.Col(
                dcc.Dropdown(
                    id="prediction-features-dropdown",
                    options=[{"label": col, "value": col} for col in get_dataframe_columns()],
                    multi=True,
                    placeholder="Select features...",
                ),
            ),
        ], className="mb-3"),

        # Row for label text
        dbc.Row([
            dbc.Col(html.Label("Label:", style={"marginTop": "6px"}), width=3),
            dbc.Col(
                dbc.Input(
                    id="prediction-label-input",
                    type="text",
                    placeholder="Enter label...",
                    value="predicted",
                ),
            ),
        ], className="mb-3"),

        # Row for prediction button and status
        dbc.Row([
            dbc.Col(html.Label("", style={"marginTop": "6px"}), width=3),
            dbc.Col(
                html.Div([
                    html.Button("Run prediction", id="prediction-start-button", n_clicks=0),
                    html.Span("Status: ", style={"marginLeft": "10px"}),
                    html.Span(id="prediction-job-status", children="Idle"),
                    dcc.Interval(id="prediction-status-interval", interval=1000, n_intervals=0, disabled=True)
                ]),
            ),
        ], className="mb-3"),
    ]


# Populate dropdown with columns from the data table
@app.callback(
    Output("prediction-features-dropdown", "options"),
    Output("prediction-features-dropdown", "value"),
    Input({'type': 'data-table', 'index': 'prediction-training'}, "data"),
    prevent_initial_call=True
)
def update_feature_dropdown(data):
    if not data:
        return [], []
    options = [{"label": col, "value": col} for col in data[0].keys()]
    look_for_values = ['aca_b_cbf', 'aca_b_cov', 'csf_vol', 'gm_icvratio', 'gm_vol', 'gmwm_icvratio',
                       'mca_b_cbf', 'mca_b_cov','pca_b_cbf', 'pca_b_cov', 'totalgm_b_cbf','totalgm_b_cov',
                       'wm_vol', 'wmh_count', 'wmhvol_wmvol']
    default_values = [col for col in data[0].keys() if col.lower() in look_for_values]
    return options, default_values


@app.callback(
    Output("prediction-job-id", "data"),
    Output("prediction-status-interval", "disabled", allow_duplicate=True),
    Input("prediction-start-button", "n_clicks"),
    State("model-dropdown", "value"),
    State("prediction-features-dropdown", "value"),
    State("prediction-label-input", "value"),
    prevent_initial_call=True,
)
def start_job(n_clicks, model_name, selected_features, label):
    if not selected_features:
        return dash.no_update, True

    job_arguments = {
        "type": "prediction",
        "model_name": model_name,
        "train_paths": data_store.input_files['prediction-training'],
        "train_sites": data_store.input_sites['prediction-training'],
        "validation_paths": data_store.input_files['prediction-testing'],
        "validation_sites": data_store.input_sites['prediction-testing'],
        "prediction_features": selected_features,
        "parameters": {
            **prediction_models[model_name]["parameters"]
        },
        "label": label,
    }

    # Generate job_id and start the job in a separate thread
    job_id = str(int(time.time())) + "_" + model_name
    threading.Thread(target=run_job, args=(job_arguments, job_id, False), daemon=True).start()

    return job_id, False  # enable the interval


@app.callback(
    Output("prediction-job-status", "children"),
    Output("prediction-status-interval", "disabled", allow_duplicate=True),
    Input("prediction-status-interval", "n_intervals"),
    State("prediction-job-id", "data"),
    prevent_initial_call=True,
)
def update_job_status(n, job_id):
    if not job_id:
        return "", True

    status = get_job_status(job_id)

    if status.lower() in ("completed", "failed", "cancelled"):
        return status, True  # Stop interval
    return status, False
