import os
from mysql.connector import Error
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

class DBConfigMySQL:
    def __init__(self):
        self.DB_HOST = os.getenv("DB_HOST_TEST","comprafacil.pics")
        self.DB_PORT = os.getenv("DB_PORT_TEST","3306")
        self.DB_USER = os.getenv("DB_USER_TEST","scraper")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD_TEST","AppScraper2024!!")
        self.DB_NAME = os.getenv("DB_NAME_TEST","dev_scp")
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



