import os
import ast
import pandas as pd
import snowflake.connector


class SnowflakeConn:
    def __init__(self, db_reference, server=None):
        """ Initialize the class
        :param db_reference: Reference name for the DB to be used
        :param server: Dictionary containing the info to connect to the Server
        """

        self.conn_str = None
        self.conn = None
        self.db_reference = db_reference
        self.server = server

        try:
            server_creds = os.environ.get(f"SNOWFLAKE-{self.db_reference.upper()}")
            server_creds = ast.literal_eval(server_creds)
        except Exception as e:
            raise ValueError(f'Snowflake DB reference: {self.db_reference} not found. ERROR: {e}')

        try:
            server_creds = server_creds[self.server.lower()]
        except Exception as e:
            raise ValueError(f'Server: {self.server} not found for Snowflake DB reference: {self.db_reference}. ERROR: {e}')

        if 'server_name' not in server_creds.keys():
            raise ValueError(f"Server name not provided for Snowflake {self.db_reference} on {self.server.upper()} server")
        else:
            self.account = server_creds['server_name']

        if 'db_name' not in server_creds.keys():
            raise ValueError(f"Database name not provided for Snowflake {self.db_reference} on {self.server.upper()} server")
        else:
            self.db_name = server_creds['db_name']

        if 'user_name' not in server_creds.keys():
            raise ValueError(f"User name not provided for Snowflake {self.db_reference} on {self.server.upper()} server")
        else:
            self.user_name = server_creds['user_name']

        if 'pwd' not in server_creds.keys():
            raise ValueError(f"Password not provided for Snowflake {self.db_reference} on {self.server.upper()} server")
        else:
            self.pwd = server_creds['pwd']

        self.connect()

    def connect(self):
        """ Open the connection to Snowflake """
        self.conn = snowflake.connector.connect(
            user=self.user_name,
            password=self.pwd,
            account=self.account,
            database=self.db_name)

    def close(self):
        """ Close the connection to Snowflake """
        self.conn.close()

    def query(self, sql_query):
        """ Read data from Snowflake according to the sql_query
        -----------------------------
        query_str = "SELECT * FROM %s" & table
        con_.query(query_str)
        -----------------------------
        :param sql_query: Query to be sent to Snowflake
        :return: DataFrame gathering the requested data
        """
        cursor = None
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            result = pd.DataFrame(rows, columns=col_names)
            return result
        except Exception as e:
            raise Exception(e)
        finally:
            if cursor:
                cursor.close()
            self.close()
