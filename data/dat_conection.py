import os
from mysql.connector import Error
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

class DBConfigMySQL:
    def __init__(self):
        self.DB_HOST = "38.105.232.116"
        self.DB_PORT = "3306"
        self.DB_USER = "super_scraper"
        self.DB_PASSWORD = "@!2025GPaByPeGH!"
        self.DB_NAME = "CRSLG_DB"
        self.connection = None

    def connect(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.DB_HOST,
                    database=self.DB_NAME,
                    user=self.DB_USER,
                    password=self.DB_PASSWORD,
                    #charset=self.db,
                    port=self.DB_PORT,
                )
                return self.connection
        except Error as e:
            self.connection = None

    def disconnect(self):
        if self.connection is not None and self.connection.is_connected():
            self.connection.close()



