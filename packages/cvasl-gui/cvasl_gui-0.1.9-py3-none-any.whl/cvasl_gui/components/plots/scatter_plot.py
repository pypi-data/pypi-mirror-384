from dash import html, dcc, Input, Output
from cvasl_gui.app import app
import plotly.express as px
from cvasl_gui import data_store


layout = html.Div([
    html.Div([
        html.Label("X-axis"),
        dcc.Dropdown(
            id='scatter-x-axis',
            placeholder="Select a column"
        ),
        html.Label("Y-axis"),
        dcc.Dropdown(
            id='scatter-y-axis',
            placeholder="Select a column"
        ),
        html.Label("Group by"),
        dcc.Dropdown(
            id='scatter-group-by',
            placeholder="Select a column"
        )
    ], style={'flex': '1', 'padding': '10px'}),
    
    html.Div([
      dcc.Graph(id='scatter-plot')
    ], style={'flex': '2', 'padding': '10px'})
], style={'display': 'flex', 'width': '100%'})


@app.callback(
    Output('scatter-x-axis', 'options'),
    Output('scatter-x-axis', 'value'),
    Output('scatter-y-axis', 'options'),
    Output('scatter-y-axis', 'value'),
    Output('scatter-group-by', 'options'),
    Output('scatter-group-by', 'value'),
    Input({'type': 'data-table', 'index': 'harmonization'}, 'data')
)
def update_scatter_dropdowns(data):
    df = data_store.all_data['harmonization']
    if not hasattr(data_store, 'all_data') or df is None:
        return [], None, [], None, [], None

    columns = [{'label': col, 'value': col} for col in df.columns]
    default_x_column = 'Age' if 'Age' in df.columns else None
    default_y_column = df.columns[5] if len(df.columns) > 5 else None
    default_group_column = 'Site' if 'Site' in df.columns else None
    return columns, default_x_column, columns, default_y_column, columns, default_group_column


@app.callback(
    Output('scatter-plot', 'figure'),
    Input('scatter-x-axis', 'value'),
    Input('scatter-y-axis', 'value'),
    Input('scatter-group-by', 'value')
)
def update_scatter_plot(x_axis, y_axis, group_by):
    if not x_axis or not y_axis:
        return {}
    data = data_store.all_data['harmonization']
    fig = px.scatter(data, x=x_axis, y=y_axis, color=group_by, facet_col='label', trendline='ols')
    return fig
