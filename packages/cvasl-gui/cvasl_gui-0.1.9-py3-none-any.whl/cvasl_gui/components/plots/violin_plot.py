from dash import html, dcc, Input, Output
from cvasl_gui.app import app
import plotly.express as px
from cvasl_gui import data_store


layout = html.Div([
    html.Div([
        html.Label("Column to plot"),
        dcc.Dropdown(
            id='violin-y-axis',
            placeholder="Select a column"
        ),
        html.Label("Group by"),
        dcc.Dropdown(
            id='violin-group-by',
            placeholder="Select a column"
        )
    ], style={'flex': '1', 'padding': '10px'}),

    html.Div([
        dcc.Graph(id='violin-plot')
    ], style={'flex': '2', 'padding': '10px'}),

], style={'display': 'flex', 'width': '100%'})


@app.callback(
    Output('violin-y-axis', 'options'),
    Output('violin-y-axis', 'value'),
    Output('violin-group-by', 'options'),
    Output('violin-group-by', 'value'),
    Input({'type': 'data-table', 'index': 'harmonization'}, 'data')
)
def update_violin_dropdowns(data):
    df = data_store.all_data['harmonization']
    if not hasattr(data_store, 'all_data') or df is None:
        return [], None, [], None

    columns = [{'label': col, 'value': col} for col in df.columns]
    default_y_axis = 'Age' if 'Age' in df.columns else None
    default_group_by = 'Site' if 'Site' in df.columns else None
    return columns, default_y_axis, columns, default_group_by


@app.callback(
    Output('violin-plot', 'figure'),
    Input('violin-y-axis', 'value'),
    Input('violin-group-by', 'value')
)
def update_violin_plot(y_axis, group_by):
    if not y_axis:
        return {}
    data = data_store.all_data['harmonization']
    fig = px.violin(data, y=y_axis, color=group_by, facet_col='label',
                    box=True, points='outliers') # points can be 'all', 'outliers', or False
    return fig
