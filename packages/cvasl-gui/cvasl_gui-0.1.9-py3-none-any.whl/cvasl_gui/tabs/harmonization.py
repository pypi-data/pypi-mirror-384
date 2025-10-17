import time
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import os
import threading

from cvasl_gui.app import app
from cvasl_gui.tabs.job_list import run_job, get_job_status
from cvasl_gui import data_store
from cvasl_gui.components.directory_input import create_directory_input
from cvasl_gui.components.data_table import create_data_table
from cvasl_gui.components.feature_compare import create_feature_compare

from cvasl_gui.tabs.parameters import parameters

# Folder where job output files are stored
WORKING_DIR = os.getenv("CVASL_WORKING_DIRECTORY", ".")
INPUT_DIR = os.path.join(WORKING_DIR, 'data')
JOBS_DIR = os.path.join(WORKING_DIR, 'jobs')

ALGORITHM_PARAMS = {
    "neurocombat": {
        "label": "NeuroCombat",
        "parameters": ["features_to_harmonize", "discrete_covariates", "continuous_covariates", "site_indicator", "patient_identifier", "empirical_bayes", "mean_only", "parametric" ]
    },
    "neuroharmonize": {
        "label": "NeuroHarmonize",
        "parameters": ["features_to_harmonize", "covariates", "smooth_terms", "site_indicator", "empirical_bayes" ]
    },
    "covbat": {
        "label": "CovBat",
        "parameters": ["features_to_harmonize", "covariates", "site_indicator", "patient_identifier", "numerical_covariates", "empirical_bayes" ]
    },
    "nestedcombat": {
        "label": "OPNested ComBat",
        "parameters": ["features_to_harmonize", "batch_list_harmonisations", "site_indicator", "discrete_covariates", "continuous_covariates", "intermediate_results_path", "patient_identifier", "return_extended", "use_gmm" ]
    },
    "autocombat": {
        "label": "AutoComBat",
        "parameters": ["data_subset", "features_to_harmonize", "site_indicator", "discrete_covariates", "continuous_covariates", "discrete_cluster_features", "continuous_cluster_features", "metric", "features_reduction", "feature_reduction_dimensions", "empirical_bayes" ]
    },
    "relief": {
        "label": "RELIEF",
        "parameters": ["features_to_harmonize", "covariates", "patient_identifier", "intermediate_results_path" ]
    }
}



def get_dataframe_columns():
    df = data_store.all_data['harmonization']
    if df is None:
        return []
    return df.columns


def create_tab_harmonization():
    return html.Div([
        dbc.Accordion([
            dbc.AccordionItem([create_directory_input('harmonization')],
                title="Select new input data"),
            dbc.AccordionItem([create_data_table('harmonization')],
                title="Inspect data"),
            dbc.AccordionItem([create_feature_compare()],
                title="Feature comparison"),
            dbc.AccordionItem(create_harmonization_parameters(),
                title="Harmonization"),
            dcc.Store(id="harmonization-job-id", data=None),
        ], always_open=True)
    ])


def create_parameter_component(parameter_data, width=3):
    id = parameter_data[0]
    label_text = parameter_data[1]["label"]
    parameter_type = parameter_data[1]["type"]
    description = parameter_data[1].get("description", "")
    default_value = parameter_data[1].get("default", None)

    # Depending on the type, create the appropriate input component
    parameter_control = None
    match parameter_type:
        case "feature-list-multi":
            parameter_control = dcc.Dropdown(id=f"{id}-dropdown", options=[],
                                            multi=True, placeholder="select features...",
                                            value=default_value),
        case "feature-list-single":
            parameter_control = dcc.Dropdown(id=f"{id}-dropdown", options=[],
                                            multi=False, placeholder="select feature...",
                                            value=default_value),
        case "selection":
            options = parameter_data[1].get("options", [])
            parameter_control = dcc.Dropdown(id=f"{id}-dropdown", 
                                            options=[{"label": opt, "value": opt} for opt in options],
                                            multi=False, placeholder="select option...",
                                            value=default_value),
        case "str":
            parameter_control = dbc.Input(id=f"{id}-input", type="text",
                                         placeholder="enter value...",
                                         value=default_value),
        case "int":
            parameter_control = dbc.Input(id=f"{id}-input", type="number",
                                         placeholder="enter integer...",
                                         value=default_value),
        case "bool":
            bool_default = default_value if default_value is not None else False
            parameter_control = dbc.Checkbox(id=f"{id}-checkbox", value=bool_default,
                                             style={"marginTop": "6px"}),

    return dbc.Row([
        dbc.Col(
            html.Div([
                html.Label(
                    label_text,
                    style={"marginTop": "6px", "marginRight": "5px", "marginBottom": "0"}
                ),
                html.Span(
                    "i",
                    id=f"{id}-target",
                    style={
                        "cursor": "pointer",
                        "fontFamily": "serif",
                        "fontWeight": "bold",
                        "fontStyle": "italic",
                        "border": "2px solid #97b0d4",
                        "borderRadius": "50%",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "width": "18px",
                        "height": "18px",
                        "fontSize": "12px",
                        "lineHeight": "1",
                        "textAlign": "center",
                        "color": "#97b0d4",
                        "verticalAlign": "middle"
                    }
                ),
                dbc.Tooltip(
                    description,
                    target=f"{id}-target",
                    placement="right",
                    trigger="hover"
                )
            ], style={"display": "flex", "alignItems": "center", "gap": "5px"}
            ), width=width
        ),
        dbc.Col(parameter_control),
    ], className="mb-3", id=f"row-{id}")



def create_harmonization_parameters():

    return [
        dbc.Row([
            dbc.Col(html.Label("Algorithm", style={"marginTop": "6px"}), width=3),
            dbc.Col(
                dcc.Dropdown(
                    id="algorithm-dropdown",
                    options=[
                        {"label": v["label"], "value": k} for k, v in ALGORITHM_PARAMS.items()
                    ],
                    value="neurocombat",
                    clearable=False,
                ),
            ),
        ], className="mb-3", id="row-algorithm"),

        # Instantiate a parameter component for each parameter,
        # they will be dynamically shown/hidden based on the selected algorithm
        *[create_parameter_component(parameter_data) for parameter_data in parameters.items()],

        dbc.Row([
            dbc.Col(html.Label("Label", style={"marginTop": "6px"}), width=3),
            dbc.Col(dbc.Input(id="label-input", type="text",
                placeholder="Enter label...", value="neurocombat"),
            ),
        ], className="mb-3", id="row-label-input"),

        # Row for button and status
        dbc.Row([
            dbc.Col(html.Label("", style={"marginTop": "6px"}), width=3),
            dbc.Col(
                html.Div([
                    html.Button("Start harmonization", id="start-button", n_clicks=0),
                    html.Span("Status: ", style={"marginLeft": "10px"}),
                    html.Span(id="harmonization-job-status", children="Idle"),
                    dcc.Interval(id="harmonization-status-interval", interval=1000, n_intervals=0, disabled=True)
                ]),
            ),
        ], className="mb-3"),
    ]


@app.callback(
    [ Output(f"row-{id}", "style") for id in parameters.keys() ],
    Input("algorithm-dropdown", "value"),
)
def toggle_rows(algorithm):
    """Show/hide parameter rows based on the selected algorithm and hide property"""
    active_parameters = ALGORITHM_PARAMS.get(algorithm, {}).get("parameters", [])
    
    styles = []
    for param_id in parameters.keys():
        # Check if parameter should be hidden
        should_hide = parameters[param_id].get("hide", False)
        
        # Show if it's active for the algorithm and not marked as hidden
        if param_id in active_parameters and not should_hide:
            styles.append({"display": "flex"})
        else:
            styles.append({"display": "none"})
    
    return styles


@app.callback(
    Output("label-input", "value"),
    Input("algorithm-dropdown", "value"),
)
def update_label_from_algorithm(algorithm):
    """Update the label input to match the selected algorithm name"""
    return algorithm.lower() if algorithm else "harmonized"


#
#  Populate the dropdowns with columns from the data table
#

@app.callback(
    Output("data_subset-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_data_subset_dropdown(data):
    if not data:
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]

@app.callback(
    Output("features_to_harmonize-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_feature_dropdown(data):
    if not data: # Check if data is empty
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]

@app.callback(
    Output("discrete_covariates-dropdown", "options"),
    Output("discrete_covariates-dropdown", "value"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_discrete_covariate_dropdown(data):
    if not data:
        return [], None
    options = [{"label": col, "value": col} for col in data[0].keys()]
    default_value = ["Sex"] if "Sex" in data[0].keys() else None
    return options, default_value

@app.callback(
    Output("continuous_covariates-dropdown", "options"),
    Output("continuous_covariates-dropdown", "value"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_continuous_covariate_dropdown(data):
    if not data:
        return [], None
    options = [{"label": col, "value": col} for col in data[0].keys()]
    default_value = ["Age"] if "Age" in data[0].keys() else None
    return options, default_value

@app.callback(
    Output("site_indicator-dropdown", "options"),
    Output("site_indicator-dropdown", "value"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_site_indicator_dropdown(data):
    if not data:
        return [], None
    options = [{"label": col, "value": col} for col in data[0].keys()]
    default_value = "Site" if "Site" in data[0].keys() else None
    return options, default_value

@app.callback(
    Output("patient_identifier-dropdown", "options"),
    Output("patient_identifier-dropdown", "value"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_patient_identifier_dropdown(data):
    if not data:
        return [], None
    options = [{"label": col, "value": col} for col in data[0].keys()]
    default_value = "participant_id" if "participant_id" in data[0].keys() else None
    return options, default_value

@app.callback(
    Output("covariates-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_covariates_dropdown(data):
    if not data:
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]

@app.callback(
    Output("batch_list_harmonisations-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_batch_list_harmonisations_dropdown(data):
    if not data:
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]

@app.callback(
    Output("numerical_covariates-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_numerical_covariates_dropdown(data):
    if not data:
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]

@app.callback(
    Output("smooth_terms-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_smooth_terms_dropdown(data):
    if not data:
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]

@app.callback(
    Output("discrete_cluster_features-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_discrete_cluster_features_dropdown(data):
    if not data:
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]

@app.callback(
    Output("continuous_cluster_features-dropdown", "options"),
    Input({'type': 'data-table', 'index': 'harmonization'}, "data"),
    prevent_initial_call=True
)
def update_continuous_cluster_features_dropdown(data):
    if not data:
        return []
    return [{"label": col, "value": col} for col in data[0].keys()]


@app.callback(
    Output("harmonization-job-id", "data"),
    Output("harmonization-status-interval", "disabled", allow_duplicate=True),
    Input("start-button", "n_clicks"),
    State("algorithm-dropdown", "value"),
    State("label-input", "value"),
    # Add all parameter controls as State
    State("data_subset-dropdown", "value"),
    State("features_to_harmonize-dropdown", "value"),
    State("batch_list_harmonisations-dropdown", "value"),
    State("covariates-dropdown", "value"),
    State("discrete_covariates-dropdown", "value"),
    State("continuous_covariates-dropdown", "value"),
    State("numerical_covariates-dropdown", "value"),
    State("smooth_terms-dropdown", "value"),
    State("discrete_cluster_features-dropdown", "value"),
    State("continuous_cluster_features-dropdown", "value"),
    State("metric-dropdown", "value"),
    State("features_reduction-dropdown", "value"),
    State("feature_reduction_dimensions-input", "value"),
    State("empirical_bayes-checkbox", "value"),
    State("mean_only-checkbox", "value"),
    State("parametric-checkbox", "value"),
    State("return_extended-checkbox", "value"),
    State("use_gmm-checkbox", "value"),
    State("site_indicator-dropdown", "value"),
    State("patient_identifier-dropdown", "value"),
    State("intermediate_results_path-input", "value"),
    prevent_initial_call=True
)
def start_job(n_clicks, algorithm, label, 
              data_subset, features_to_harmonize, batch_list_harmonisations, covariates,
              discrete_covariates, continuous_covariates, numerical_covariates, smooth_terms,
              discrete_cluster_features, continuous_cluster_features, metric, features_reduction,
              feature_reduction_dimensions, empirical_bayes, mean_only, parametric, 
              return_extended, use_gmm, site_indicator, patient_identifier, intermediate_results_path):
    
    if not features_to_harmonize:
        return dash.no_update, True
    
    # Map parameter names to their values
    param_values = {
        "data_subset": data_subset,
        "features_to_harmonize": features_to_harmonize,
        "batch_list_harmonisations": batch_list_harmonisations,
        "covariates": covariates,
        "discrete_covariates": discrete_covariates,
        "continuous_covariates": continuous_covariates,
        "numerical_covariates": numerical_covariates,
        "smooth_terms": smooth_terms,
        "discrete_cluster_features": discrete_cluster_features,
        "continuous_cluster_features": continuous_cluster_features,
        "metric": metric,
        "features_reduction": features_reduction,
        "feature_reduction_dimensions": feature_reduction_dimensions,
        "empirical_bayes": empirical_bayes,
        "mean_only": mean_only,
        "parametric": parametric,
        "return_extended": return_extended,
        "use_gmm": use_gmm,
        "site_indicator": site_indicator,
        "patient_identifier": patient_identifier,
        "intermediate_results_path": intermediate_results_path,
    }

    if algorithm == "autocombat":
        # Create a data_subset that consists of the features, covariates and site indicators concatenated
        combined_subset = set(features_to_harmonize or []) | set(discrete_covariates or []) | \
                set(continuous_covariates or []) | set(discrete_cluster_features or []) | \
                set(continuous_cluster_features or []) | set([site_indicator] if site_indicator else [])
        param_values["data_subset"] = list(combined_subset)

    # Get active parameters for the selected algorithm
    algorithm_parameters = ALGORITHM_PARAMS.get(algorithm, {}).get("parameters", [])

    # Build parameters dict with only active parameters that have values
    job_parameters = {}
    for param in algorithm_parameters:
        if param in param_values:
            value = param_values[param]
            param_type = parameters[param].get("type")
            if param_type == "feature-list-multi" and value is None:
                value = []
            if value is None:
                continue  # Skip parameters without a value
            # Beyond this point, None is considered a valid value
            if param_type == "selection" and value == "None":
                value = None
            job_parameters[param] = value

    job_arguments = {
        "type": "harmonization",
        "algorithm": algorithm,
        "input_paths": data_store.input_files['harmonization'],
        "input_sites": data_store.input_sites['harmonization'],
        "parameters": job_parameters,
        "label": label,
    }

    # Generate job_id and start the job in a separate thread
    job_id = str(int(time.time())) + "_" + algorithm
    threading.Thread(target=run_job, args=(job_arguments, job_id, True), daemon=True).start()

    return job_id, False  # enable the interval


@app.callback(
    Output("harmonization-job-status", "children"),
    Output("harmonization-status-interval", "disabled", allow_duplicate=True),
    Input("harmonization-status-interval", "n_intervals"),
    State("harmonization-job-id", "data"),
    prevent_initial_call=True,
)
def update_job_status(n, job_id):
    if not job_id:
        return "", True

    status = get_job_status(job_id)

    if status.lower() in ("completed", "failed", "cancelled"):
        return status, True  # Stop interval
    return status, False
