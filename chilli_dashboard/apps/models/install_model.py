import pandas as pd
import psycopg2
import numpy as np
from datetime import datetime as dt 
from datetime import date
from app import app
from dateutil.relativedelta import relativedelta
import datetime
from apps.db.db_conn import DbConn

class InstallModel:

    def __init__(self):
        print("initializing DbConn class")

    def get_data(self,start_date,end_date):
        conn = DbConn().get_connection()


        # connection to SQL:
        data_dates_df = pd.read_sql("select plan_name, TO_CHAR(created_at, 'yyyy-mm-dd') as installed,TO_CHAR(uninstall_date, 'yyyy-mm-dd') as uninstalled,TO_CHAR(reinstall_date, 'yyyy-mm-dd') as reinstalled from sites where created_at between '"+start_date+"' and '"+end_date+"' ",conn)
        # print(data_dates_df)

        # conversion of dates to numbers:
        data_dates_df["installs_count"] = np.where(data_dates_df['installed'].isnull(),0,1)
        data_dates_df["uninstalls_count"] = np.where(data_dates_df['uninstalled'].isnull(),0,1)
        # tablas dinamicas:
        copy1 = data_dates_df.copy()
        pivot1=copy1.pivot_table(values=["installs_count"], index=["installed"], columns="plan_name",aggfunc=[np.sum]).fillna(0).reset_index() 
        
        # installs_df:
        installs_df = pd.DataFrame(pivot1.to_records())
        installs_df = installs_df.drop(columns = ["index"])
        installs_df = installs_df.rename(columns = {"('installed', '', '')": 'event_date'})
        installs_df.columns = [c.replace("('sum', 'installs_count', '", "").replace("')", "") for c in installs_df.columns]

        before_final_df = installs_df.copy().fillna(0)
        final_df_installs = before_final_df.drop(columns = ["cancelled","fraudulent","frozen"])

        final_df_installs["event_date"] = pd.to_datetime(final_df_installs["event_date"])
        final_df_installs = final_df_installs.set_index("event_date")
       
        return final_df_installs