import os
import sys
import webbrowser
from threading import Timer
from waitress import serve

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc


from cvasl_gui import data_store
from cvasl_gui.app import app
from cvasl_gui.tabs.harmonization import create_tab_harmonization
from cvasl_gui.tabs.prediction import create_tab_prediction
from cvasl_gui.tabs.job_list import create_job_list

data_store.all_data = {
  'harmonization': None,
  'prediction-training': None,
  'prediction-testing': None,
}
data_store.selected_directory = None

app.layout = html.Div(
    id='root',
    children=[html.Div([
        dcc.Tabs(
            id='tabs',
            value='1',
            children=[
                dcc.Tab(
                    label='Harmonize',
                    value='1',
                    style={'backgroundColor': '#f0f0f0'},  # Default tab background
                    selected_style={'backgroundColor': '#e7f1ff', 'fontWeight': 'bold'}  # Active tab style
                ),
                dcc.Tab(
                    label='Predict',
                    value='2',
                    style={'backgroundColor': '#f0f0f0'},  # Default tab background
                    selected_style={'backgroundColor': '#e7f1ff', 'fontWeight': 'bold'}  # Active tab style
                ),
                dcc.Tab(
                    label='Jobs',
                    value='3',
                    style={'backgroundColor': '#f0f0f0'},  # Default tab background
                    selected_style={'backgroundColor': '#e7f1ff', 'fontWeight': 'bold'}  # Active tab style
                ),
            ],
            vertical=False
        ),
        # Load all tab contents here but control visibility through a callback
        html.Div(
            [
                html.Div(create_tab_harmonization(), id='tab-1-content', style={'display': 'none'}),
                html.Div(create_tab_prediction(), id='tab-2-content', style={'display': 'none'}),
                html.Div(create_job_list(), id='tab-3-content', style={'display': 'none'}),
            ],
            id='tab-content-container'
        )
    ], id='main-container')])


# Callback to toggle visibility based on selected tab
@app.callback(
    [Output(f'tab-{i}-content', 'style') for i in range(1, 4)],
    [Input('tabs', 'value')]
)
def display_content(selected_tab):
    # Set 'display' to 'block' for the selected tab and 'none' for others
    return [{'display': 'block' if selected_tab == str(i) else 'none'} for i in range(1, 4)]


def main():
    port = int(os.getenv('CVASL_PORT', 8767))
    # Detect if running as PyInstaller bundle
    is_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
    # Force production mode for PyInstaller builds
    debug_mode = False if is_frozen else os.getenv('CVASL_DEBUG_MODE', 'False') == 'True'
    path = os.getenv('CVASL_PATHNAME_PREFIX', '/')
    host = '127.0.0.1'

    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>CVASL</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta1/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="assets/custom.css">
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
"""

    # Start the server and open the browser
    if debug_mode:
        app.run_server(port=port, debug=True)
    else:
        # Schedule a timer to open the browser
        url = f"http://{host}:{port}{path}"
        #Timer(1, lambda: webbrowser.open(url)).start()
        
        # Start the server using waitress
        print(f"Starting server at {url}")
        serve(app.server, host=host, port=port, threads=8) 


if __name__ == '__main__':
    main()
