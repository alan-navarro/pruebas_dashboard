import pandas as pd
import psycopg2
import numpy as np
from datetime import datetime as dt 
from datetime import date
from app import app
from dateutil.relativedelta import relativedelta
import datetime
from apps.db.db_conn import DbConn

class UninstallModel:

    def __init__(self):
        print("initializing DbConn class")

    def get_data(self,start_date,end_date):
        conn = DbConn().get_connection()
        # connection to SQL:
        data_dates_df = pd.read_sql("select plan_name, TO_CHAR(created_at, 'yyyy-mm-dd') as installed,TO_CHAR(uninstall_date, 'yyyy-mm-dd') as uninstalled,TO_CHAR(reinstall_date, 'yyyy-mm-dd') as reinstalled from sites where created_at between '"+start_date+"' and '"+end_date+"' ",conn)
        print(data_dates_df)

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
        
        installs_fillna = installs_df.copy().fillna(0)
        final_df_installs = installs_fillna.drop(columns = ["cancelled","fraudulent","frozen"])

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

        
        final_df_uninstalls["event_date"] = pd.to_datetime(final_df_uninstalls["event_date"])
        final_df_uninstalls.set_index("event_date", inplace = True)
        print(final_df_uninstalls)

        return final_df_uninstalls
