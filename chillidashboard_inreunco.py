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


conn = psycopg2.connect("host='{}' port={} dbname='{}' user={} password={}".format("analytics.cfvcy3yvsg8c.us-east-1.rds.amazonaws.com", "5432", "postgres", "postgres", "WzqtzGV6KkWtAl7y1l90"))
bp = "\n"*3
# connection to SQL:
data_dates_df = pd.read_sql("select plan_name, TO_CHAR(created_at, 'yyyy-mm-dd') as installed,TO_CHAR(uninstall_date, 'yyyy-mm-dd') as uninstalled,TO_CHAR(reinstall_date, 'yyyy-mm-dd') as reinstalled from sites",conn)

# conversion of dates to numbers:
data_dates_df["installs_count"] = np.where(data_dates_df['installed'].isnull(),0,1)
data_dates_df["uninstalls_count"] = np.where(data_dates_df['uninstalled'].isnull(),0,1)
# tablas dinamicas:
pivot1=data_dates_df.pivot_table(values=["installs_count"], index=["installed"], columns="plan_name",aggfunc=[np.sum]).fillna(0).reset_index() 
pivot2=data_dates_df.pivot_table(values=["uninstalls_count"], index=["uninstalled"], columns="plan_name",aggfunc=[np.sum]).fillna(0).reset_index()

# installs_df:
installs_df = pd.DataFrame(pivot1.to_records())
installs_df.drop(columns = ["index"], inplace = True)
installs_df.rename(columns = {"('installed', '', '')": 'event_date'}, inplace = True)
installs_df.columns = [hdr.replace("('sum', 'installs_count', '", "").replace("')", "") \
                     for hdr in installs_df.columns]

final_df_installs = installs_df.copy().fillna(0)
final_df_installs.drop(columns = ["cancelled","fraudulent","frozen"], inplace = True)

# uninstalls_df: 
uninstalls_df = pd.DataFrame(pivot2.to_records())
uninstalls_df.drop(columns = ["index"], inplace = True)
uninstalls_df.rename(columns = {"('uninstalled', '', '')": 'event_date'}, inplace = True)
uninstalls_df.columns = [hdr.replace("('sum', 'uninstalls_count', '", "").replace("')", "") \
                     for hdr in uninstalls_df.columns]

copy_installs_df = installs_df.copy()
copy_uninstalls_df = uninstalls_df.copy()
cancel_frozen_fraud_df1 = copy_installs_df[["event_date","cancelled","fraudulent","frozen"]]
cancel_frozen_fraud_df2 = copy_uninstalls_df[["event_date","cancelled","fraudulent","frozen"]]
    
cff_merge = cancel_frozen_fraud_df1.merge(cancel_frozen_fraud_df2,how="left",on=["event_date"]).fillna(0)
cff_merge["cancelled"] = cff_merge["cancelled_x"] + cff_merge["cancelled_y"]
cff_merge["fraudulent"] = cff_merge["fraudulent_x"] + cff_merge["fraudulent_y"]
cff_merge["frozen"] = cff_merge["frozen_x"] + cff_merge["frozen_y"]
final_cff = cff_merge[["event_date","cancelled","fraudulent","frozen"]]
filter_uninstalls = copy_uninstalls_df.drop(columns = ["cancelled","fraudulent","frozen"])
        
final_df_uninstalls = filter_uninstalls.merge(final_cff,how="right",on=["event_date"]).fillna(0)

#----------------------------------------
# Versus data:
sum_installs = pd.Series(index=final_df_installs.columns, dtype = 'int64')
for i, idx in enumerate(final_df_installs.columns, 1):
    sum_installs[idx] = final_df_installs.iloc[:,:i].all(axis=1).sum()

sum_uninstalls = pd.Series(index=final_df_uninstalls.columns, dtype = 'int64')
for i, idx in enumerate(final_df_uninstalls.columns, 1):
    sum_uninstalls[idx] = final_df_uninstalls.iloc[:,:i].all(axis=1).sum()

sum_uninstalls = sum_uninstalls*-1
##--------------------------------------------------------------------------------------------------------------------------------
### CALENDAR Y GRAPH -> INSTALLS
final_df_installs["event_date"] = pd.to_datetime(final_df_installs["event_date"])
final_df_installs.set_index("event_date", inplace= True)
final_df_uninstalls["event_date"] = pd.to_datetime(final_df_uninstalls["event_date"])
final_df_uninstalls.set_index("event_date", inplace= True)

past_month = relativedelta(months=1)
current_date = datetime.date.today()
starting_date = current_date - past_month

app = dash.Dash(suppress_callback_exceptions=True)

app.layout=html.Div([

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
    chosen_dates = final_df_installs[start_date:end_date]
    chosen_dates_reset = chosen_dates.reset_index()
    x_row = chosen_dates_reset["event_date"]
    df_columns = chosen_dates_reset.iloc[:, 1:15]
    y_columns = list(df_columns)

    fig_installs = px.bar(chosen_dates_reset, 
    x=x_row, y=y_columns,labels={
                        "value": "events",
                        "variable": "installations per plan:",
                        "event_date": "created at"}
    )

    
    return fig_installs

@app.callback(
    dash.dependencies.Output('uninstalls_graph', 'figure'),
    [dash.dependencies.Input('picker-range-in-un', 'start_date'),
     dash.dependencies.Input('picker-range-in-un', 'end_date')]
)

def update_graph_uninstalls (start_date, end_date):
    chosen_dates = final_df_uninstalls[start_date:end_date] #logs
    chosen_dates_reset = chosen_dates.reset_index()
    x_row = chosen_dates_reset["event_date"]
    df_columns = chosen_dates_reset.iloc[:, 1:15]
    y_columns = list(df_columns)

    fig_uninstalls = px.bar(chosen_dates_reset, 
    x=x_row, y=y_columns,labels={
                        "value": "events",
                        "variable": "uninstallations per plan:",
                        "event_date": "uninstalled at"}
    )

    
    return fig_uninstalls

@app.callback(
    dash.dependencies.Output('versus', 'figure'),
    [dash.dependencies.Input('picker-range-in-un', 'start_date'),
     dash.dependencies.Input('picker-range-in-un', 'end_date')]
)

def update_graph_versus (start_date, end_date):
    chosen_dates1 = final_df_installs[start_date:end_date]
    chosen_dates2 = final_df_uninstalls[start_date:end_date]
    chosen_dates_reset1 = chosen_dates1.reset_index()
    chosen_dates_reset2 = chosen_dates2.reset_index()

    sum_installs = pd.Series(index=chosen_dates_reset1.columns)
    for i, idx in enumerate(chosen_dates_reset1.columns, 1):
        sum_installs[idx] = chosen_dates_reset1.iloc[:,:i].all(axis=1).sum()

    sum_uninstalls = pd.Series(index=chosen_dates_reset2.columns)
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

   

if __name__ == '__main__':
    app.run_server(debug=True)