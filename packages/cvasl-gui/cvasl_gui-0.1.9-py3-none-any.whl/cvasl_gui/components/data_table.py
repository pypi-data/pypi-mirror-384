import pandas as pd
from dash import Input, Output, dash_table, MATCH, ctx
from dash.exceptions import PreventUpdate
from cvasl_gui.app import app
from cvasl_gui import data_store


def create_data_table(instance_id):
    return dash_table.DataTable(
        id={'type': 'data-table', 'index': instance_id},
        columns=[
            {'name': 'participant_id', 'id': 'participant_id', 'type': 'text'},
            {'name': 'ID', 'id': 'ID', 'type': 'text'},
            {'name': 'Age', 'id': 'Age', 'type': 'numeric'},
            {'name': 'Sex', 'id': 'Sex', 'type': 'text'},
            {'name': 'Site', 'id': 'Site', 'type': 'text'}
        ],
        data=[],
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        page_action='native',
        page_size=20,
        style_table={'overflowX': 'auto'}
    )

@app.callback(
    Output({'type': 'data-table', 'index': MATCH}, 'data'),
    Output({'type': 'data-table', 'index': MATCH}, 'columns'),
    Input({'type': 'file-contents-container', 'index': MATCH}, 'children')
)
def update_table(data):
    if data is None:
        raise PreventUpdate
    if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
        raise PreventUpdate

    ctx_index = ctx.triggered_id['index']
    df = data_store.all_data[ctx_index]
    columns = [{'name': col, 'id': col} for col in df.columns]
    return df.to_dict('records'), columns
