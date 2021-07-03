import psycopg2
import json
import os
#cd $CONDA_PREFIX/etc/conda/activate.d
class DbConn:

	def __init__(self):
	 	print("initializing DbConn class")

	def get_connection(self):
		credentials = self.get_credentials()
		conn_str = "host='{}' port={} dbname='{}' user={} password={}".format(credentials["host"], credentials["port"], credentials["dbname"], credentials["user"], credentials["password"])
		conn = psycopg2.connect(conn_str)
		return conn

	def get_credentials(self):
		db_credentials_str = None#os.environ.get('ANALYTICS_DB_CONN')
		
		if db_credentials_str:
			credentials = json.loads(db_credentials_str)
		else:
			credentials = {
				"host": "analytics.cfvcy3yvsg8c.us-east-1.rds.amazonaws.com",
				"port": "5432",
				"dbname":"postgres",
				"user":"postgres",
				"password":"WzqtzGV6KkWtAl7y1l90"
			}
		return credentials	