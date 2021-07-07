import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash
import dash_html_components as html 
import dash_core_components as dcc 
from datetime import datetime as dt 
from datetime import date
from dash.dependencies import Input, Output
import datetime
from dateutil.relativedelta import relativedelta
from app import app
from apps.db.db_conn import DbConn
from apps.models.install_model import InstallModel
from apps.models.uninstall_model import UninstallModel

past_month = relativedelta(months=1)
current_date = datetime.date.today()
starting_date = current_date - past_month

layout=html.Div([

    dcc.DatePickerRange(
        id='picker-range-in-un',  # ID to be used for callback
        calendar_orientation='horizontal',  # vertical or horizontal
        day_size=39,  # size of calendar image. Default is 39
        end_date_placeholder_text="End Day",  # text that appears when no end date chosen
        with_portal=False,  # if True calendar will open in a full screen overlay portal
        first_day_of_week=0,  # Display of calendar when open (0 = Sunday)
        reopen_calendar_on_clear=True, # if false, the calendar will open up automatixally when values are deleted
        is_RTL=False,  # True or False for direction of calendar
        clearable=True,  # whether or not the user can clear the dropdown
        number_of_months_shown=1,  # number of months shown when calendar is open
        min_date_allowed=dt(2005, 1, 1),  # minimum date allowed on the DatePickerRange component
        max_date_allowed=dt(2050, 1, 1),  # maximum date allowed on the DatePickerRange component
        start_date=starting_date, # buscar como poner el dia de hoy para mostrar
        end_date=current_date,
        minimum_nights=0,  # minimum number of days between start and end date

        persistence=True,       # remember the date chosen
        persisted_props=['start_date',"end_date"],
        persistence_type='local',  # session, local, or memory. Default is 'local'

        updatemode='singledate'  # singledate or bothdates. Determines when callback is triggered
),
    html.Div([html.H1('Overall trend', style={"textAlign": "center"}),
	html.Div([html.H2('Installs', style={"textAlign": "center"}),
	html.Div([dcc.Loading(children=[dcc.Graph(id = "installs_graph")])])],style={'width': '48%', 'display': 'inline-block'}),

    html.Div([html.H2('Uninstalls', style={"textAlign": "center"}),
	html.Div([dcc.Loading(children=[dcc.Graph(id = "uninstalls_graph")])])],style={'width': '48%', 'display': 'inline-block'}), 

    html.Div([html.H2('Installs vs. Uninstalls', style={"textAlign": "center"}),
    html.Div([dcc.Loading(children=[dcc.Graph(id = "versus")])])])
					])
])

@app.callback(
    dash.dependencies.Output('installs_graph', 'figure'),
    [dash.dependencies.Input('picker-range-in-un', 'start_date'),
     dash.dependencies.Input('picker-range-in-un', 'end_date')]
)

def update_graph_installs (start_date, end_date):
    chosen_dates_installs = InstallModel().get_data(start_date,end_date)
    chosen_dates_reset_installs = chosen_dates_installs.reset_index()
    x_row_i = chosen_dates_reset_installs["event_date"]
    df_columns_i = chosen_dates_reset_installs.iloc[:, 1:]
    y_columns_i = list(df_columns_i)

    fig_installs = px.bar(chosen_dates_reset_installs, 
    x=x_row_i, y=y_columns_i,labels={
                        "value": "Events",
                        "variable": "Installations per plan:",
                        "event_date": "Created at"}
    )
    
    return fig_installs

@app.callback(
    dash.dependencies.Output('uninstalls_graph', 'figure'),
    [dash.dependencies.Input('picker-range-in-un', 'start_date'),
     dash.dependencies.Input('picker-range-in-un', 'end_date')]
)

def update_graph_uninstalls (start_date, end_date):
    chosen_dates_uninstalls = UninstallModel().get_data(start_date,end_date) #logs
    chosen_dates_reset_uninstalls = chosen_dates_uninstalls.reset_index()
    x_row_u = chosen_dates_reset_uninstalls["event_date"]
    df_columns_u = chosen_dates_reset_uninstalls.iloc[:, 1:]
    y_columns_u = list(df_columns_u)

    fig_uninstalls = px.bar(chosen_dates_reset_uninstalls, 
    x=x_row_u, y=y_columns_u,labels={
                        "value": "Events",
                        "variable": "Uninstallations per plan:",
                        "event_date": "Uninstalled at"}
    )

    return fig_uninstalls

@app.callback(
    dash.dependencies.Output('versus', 'figure'),
    [dash.dependencies.Input('picker-range-in-un', 'start_date'),
     dash.dependencies.Input('picker-range-in-un', 'end_date')]
)

def update_graph_versus (start_date, end_date):
    chosen_dates1 = InstallModel().get_data(start_date,end_date)
    chosen_dates2 = UninstallModel().get_data(start_date,end_date)
    chosen_dates_reset1 = chosen_dates1.reset_index()
    chosen_dates_reset2 = chosen_dates2.reset_index()

    sum_installs = pd.Series(index=chosen_dates_reset1.columns, dtype = 'float64')
    for i, idx in enumerate(chosen_dates_reset1.columns, 1):
        sum_installs[idx] = chosen_dates_reset1.iloc[:,:i].all(axis=1).sum()
    
    sum_uninstalls = pd.Series(index=chosen_dates_reset2.columns, dtype = 'float64')
    for i, idx in enumerate(chosen_dates_reset2.columns, 1):
        sum_uninstalls[idx] = chosen_dates_reset2.iloc[:,:i].all(axis=1).sum()
    
    sum_uninstalls = sum_uninstalls*-1
    date_range = chosen_dates_reset1["event_date"]

    versus_fig = go.Figure()
    versus_fig.add_trace(go.Bar(x=date_range, y=sum_installs,
                    base=0,
                    marker_color='crimson',
                    name='Installs'))
    versus_fig.add_trace(go.Bar(x=date_range, y=sum_uninstalls,
                    base=0,
                    marker_color='lightslategrey',
                    name='Uninstalls'
                    ))
    
    return versus_fig
