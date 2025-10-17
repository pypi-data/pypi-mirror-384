import dash
from dash import Dash, html, dcc, Input, Output
from cvasl_gui.components.plots import violin_plot
from cvasl_gui.components.plots import box_plot
from cvasl_gui.components.plots import scatter_plot
from cvasl_gui.app import app


def create_feature_compare():
    return html.Div([

        # Plot selection
        html.Div([
            html.Button("Violin Plot", id='btn-violin', n_clicks=0, className='plot-button'),
            html.Button("Box Plot", id='btn-box', n_clicks=0, className='plot-button'),
            html.Button("Scatter Plot", id='btn-scatter', n_clicks=0, className='plot-button'),
        ], style={'display': 'flex', 'gap': '10px', 'justify-content': 'center'}),

        # Plot container
        html.Div([
            html.Div(violin_plot.layout, id='plot-1', style={'display': 'block'}),
            html.Div(box_plot.layout, id='plot-2', style={'display': 'none'}),
            html.Div(scatter_plot.layout, id='plot-3', style={'display': 'none'})
        ], id='plot-container')
    ])


# Callback to toggle visibility based on selected plot
@app.callback(
    [Output(f'plot-{i}', 'style') for i in range(1, 4)],
    [Input('btn-violin', 'n_clicks'),
     Input('btn-box', 'n_clicks'),
     Input('btn-scatter', 'n_clicks')]
)
def display_content(btn_violin, btn_box, btn_scatter):
    # Determine which plot type was selected
    plot_type = get_plot_type()

    # Map buttons to plots
    if plot_type == 'violin':
        return [{'display': 'block'}, {'display': 'none'}, {'display': 'none'}]
    elif plot_type == 'box':
        return [{'display': 'none'}, {'display': 'block'}, {'display': 'none'}]
    elif plot_type == 'scatter':
        return [{'display': 'none'}, {'display': 'none'}, {'display': 'block'}]

    return [{'display': 'block'}, {'display': 'none'}, {'display': 'none'}]  # Fallback


# Callback to update button styles (highlight the selected button)
@app.callback(
    Output('btn-violin', 'className'),
    Output('btn-box', 'className'),
    Output('btn-scatter', 'className'),
    Input('btn-violin', 'n_clicks'),
    Input('btn-box', 'n_clicks'),
    Input('btn-scatter', 'n_clicks')
)
def update_button_styles(btn_violin, btn_box, btn_scatter):
    # Determine which plot type was selected
    plot_type = get_plot_type()

    # Highlight the selected button
    return (
        'plot-button selected' if plot_type == 'violin' else 'plot-button',
        'plot-button selected' if plot_type == 'box' else 'plot-button',
        'plot-button selected' if plot_type == 'scatter' else 'plot-button'
    )


def get_plot_type():
    # Determine which button was clicked most recently
    ctx = dash.callback_context
    if not ctx.triggered:
        return 'violin'  # Default to violin plot
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'btn-violin':
        return 'violin'
    elif button_id == 'btn-box':
        return 'box'
    elif button_id == 'btn-scatter':
        return 'scatter'
    return 'violin'  # Fallback to default
