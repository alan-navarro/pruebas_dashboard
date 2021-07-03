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
copy1 = data_dates_df.copy()
pivot1=copy1.pivot_table(values=["installs_count"], index=["installed"], columns="plan_name",aggfunc=[np.sum]).fillna(0).reset_index() 
copy2 = data_dates_df.copy()
pivot2=copy2.pivot_table(values=["uninstalls_count"], index=["uninstalled"], columns="plan_name",aggfunc=[np.sum]).fillna(0).reset_index()

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
#---------------------------------------- DATE PICKER
final_df_installs["event_date"] = pd.to_datetime(final_df_installs["event_date"])
final_df_installs.set_index("event_date", inplace= True)
final_df_uninstalls["event_date"] = pd.to_datetime(final_df_uninstalls["event_date"])
final_df_uninstalls.set_index("event_date", inplace= True)

# print(final_df_installs,bp,final_df_uninstalls,bp)
# print(bp,cff_merge,bp,final_cff,bp,filter_uninstalls,bp,final_df_uninstalls)

chosen_dates = final_df_uninstalls.loc["2021-05-01":"2021-05-13"]
chosen_dates_reset = chosen_dates.reset_index()
x_row = chosen_dates_reset["event_date"]
df_columns = chosen_dates_reset.iloc[:, 1:]
y_columns = list(df_columns)

# fig_installs = px.bar(chosen_dates_reset, 
# x=x_row, y=y_columns,labels={
#                     "value": "Events",
#                     "variable": "Installations per plan:",
#                     "event_date": "Created at"}
# )

# fig_installs.show()
print(chosen_dates,bp,chosen_dates_reset,bp,x_row,bp,y_columns)
#-----------------------------------
# FUNCIONAL
# Versus data:

# sum_installs = pd.Series(index=final_df_installs.columns, dtype = 'int64')
# for i, idx in enumerate(final_df_installs.columns, 1):
#     sum_installs[idx] = final_df_installs.iloc[:,:i].all(axis=1).sum()

# sum_uninstalls = pd.Series(index=final_df_uninstalls.columns, dtype = 'int64')
# for i, idx in enumerate(final_df_uninstalls.columns, 1):
#     sum_uninstalls[idx] = final_df_uninstalls.iloc[:,:i].all(axis=1).sum()

# sum_uninstalls = sum_uninstalls*-1


# date_range = chosen_dates_reset["event_date"]
# versus_fig = go.Figure()
# versus_fig.add_trace(go.Bar(x=date_range, y=sum_installs,
#                 base=0,
#                 marker_color='crimson',
#                 name='Installs'))
# versus_fig.add_trace(go.Bar(x=date_range, y=sum_uninstalls,
#                 base=0,
#                 marker_color='lightslategrey',
#                 name='Uninstalls'
#                 ))
# versus_fig.show()
