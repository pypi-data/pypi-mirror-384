from dash import html, dcc, Input, Output, ctx
from cvasl_gui.app import app
import plotly.express as px
from cvasl_gui import data_store


layout = html.Div([
    html.Div([
        html.Label("Column to plot"),
        dcc.Dropdown(
            id='box-y-axis',
            placeholder="Select a column"
        ),
        html.Label("Group by"),
        dcc.Dropdown(
            id='box-group-by',
            placeholder="Select a column"
        )
    ], style={'flex': '1', 'padding': '10px'}),

    html.Div([
        dcc.Graph(id='box-plot')
    ], style={'flex': '2', 'padding': '10px'})
], style={'display': 'flex', 'width': '100%'})


@app.callback(
    Output('box-y-axis', 'options'),
    Output('box-y-axis', 'value'),
    Output('box-group-by', 'options'),
    Output('box-group-by', 'value'),
    Input({'type': 'data-table', 'index': 'harmonization'}, 'data')
)
def update_box_dropdowns(data):
    df = data_store.all_data['harmonization']
    if not hasattr(data_store, 'all_data') or df is None:
        return [], None, [], None
    columns = [{'label': col, 'value': col} for col in df.columns]
    default_y_axis = 'Age' if 'Age' in df.columns else None
    default_group_by = 'Site' if 'Site' in df.columns else None
    return columns, default_y_axis, columns, default_group_by


@app.callback(
    Output('box-plot', 'figure'),
    Input('box-y-axis', 'value'),
    Input('box-group-by', 'value')
)
def update_box_plot(y_axis, group_by):
    if not y_axis:
        return {}
    data = data_store.all_data['harmonization']
    fig = px.box(data, y=y_axis, color=group_by, facet_col='label')
    return fig
