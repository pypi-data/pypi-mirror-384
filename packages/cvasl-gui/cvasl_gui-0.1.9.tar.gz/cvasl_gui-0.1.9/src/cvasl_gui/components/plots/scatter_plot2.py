from dash import html, dcc, Input, Output
import pandas as pd
from cvasl_gui.app import app
import plotly.express as px
from cvasl_gui import data_store


layout = html.Div([
    html.Div([
        html.Label("X-axis"),
        dcc.Dropdown(
            id='scatter-x-axis2',
            placeholder="Select a column"
        ),
        html.Label("Y-axis"),
        dcc.Dropdown(
            id='scatter-y-axis2',
            placeholder="Select a column"
        ),
        html.Label("Group by"),
        dcc.Dropdown(
            id='scatter-group-by2',
            placeholder="Select a column"
        )
    ], style={'flex': '1', 'padding': '10px'}),
    
    html.Div([
      dcc.Graph(id='scatter-plot2')
    ], style={'flex': '2', 'padding': '10px'})
], style={'display': 'flex', 'width': '100%'})


@app.callback(
    Output('scatter-x-axis2', 'options'),
    Output('scatter-x-axis2', 'value'),
    Output('scatter-y-axis2', 'options'),
    Output('scatter-y-axis2', 'value'),
    Output('scatter-group-by2', 'options'),
    Output('scatter-group-by2', 'value'),
    Input({'type': 'data-table', 'index': 'prediction-training'}, 'data'),
    Input({'type': 'data-table', 'index': 'prediction-testing'}, 'data'),
)
def update_scatter_dropdowns(data, data2):
    df = data_store.all_data['prediction-training']
    if not hasattr(data_store, 'all_data') or df is None:
        return [], None, [], None, [], None

    columns = [{'label': col, 'value': col} for col in df.columns]
    default_x_column = 'Age' if 'Age' in df.columns else None
    default_y_column = df.columns[5] if len(df.columns) > 5 else None
    default_group_column = 'Site' if 'Site' in df.columns else None
    return columns, default_x_column, columns, default_y_column, columns, default_group_column


@app.callback(
    Output('scatter-plot2', 'figure'),
    Input('scatter-x-axis2', 'value'),
    Input('scatter-y-axis2', 'value'),
    Input('scatter-group-by2', 'value')
)
def update_scatter_plot(x_axis, y_axis, group_by):
    if not x_axis or not y_axis:
        return {}
    df1 = data_store.all_data['prediction-training']
    df2 = data_store.all_data['prediction-testing']
    data = pd.concat([df1, df2], ignore_index=True)
    fig = px.scatter(data, x=x_axis, y=y_axis, color=group_by, facet_col='label', trendline='ols')
    return fig
