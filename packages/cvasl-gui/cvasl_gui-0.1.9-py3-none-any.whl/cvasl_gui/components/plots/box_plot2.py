from dash import html, dcc, Input, Output, ctx
import pandas as pd
from cvasl_gui.app import app
import plotly.express as px
from cvasl_gui import data_store


layout = html.Div([
    html.Div([
        html.Label("Column to plot"),
        dcc.Dropdown(
            id='box-y-axis2',
            placeholder="Select a column"
        ),
        html.Label("Group by"),
        dcc.Dropdown(
            id='box-group-by2',
            placeholder="Select a column"
        )
    ], style={'flex': '1', 'padding': '10px'}),

    html.Div([
        dcc.Graph(id='box-plot2')
    ], style={'flex': '2', 'padding': '10px'})
], style={'display': 'flex', 'width': '100%'})


@app.callback(
    Output('box-y-axis2', 'options'),
    Output('box-y-axis2', 'value'),
    Output('box-group-by2', 'options'),
    Output('box-group-by2', 'value'),
    Input({'type': 'data-table', 'index': 'prediction-training'}, 'data'),
    Input({'type': 'data-table', 'index': 'prediction-testing'}, 'data'),
)
def update_box_dropdowns(data, data2):
    df = data_store.all_data['prediction-training']
    if not hasattr(data_store, 'all_data') or df is None:
        return [], None, [], None
    columns = [{'label': col, 'value': col} for col in df.columns]
    default_y_axis = 'Age' if 'Age' in df.columns else None
    default_group_by = 'Site' if 'Site' in df.columns else None
    return columns, default_y_axis, columns, default_group_by


@app.callback(
    Output('box-plot2', 'figure'),
    Input('box-y-axis2', 'value'),
    Input('box-group-by2', 'value')
)
def update_box_plot(y_axis, group_by):
    if not y_axis:
        return {}
    df1 = data_store.all_data['prediction-training']
    df2 = data_store.all_data['prediction-testing']
    data = pd.concat([df1, df2], ignore_index=True)
    fig = px.box(data, y=y_axis, color=group_by, facet_col='label')
    return fig
