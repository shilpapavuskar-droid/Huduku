import mysql.connector as connector

def connect_sql():
    return connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="rootpass",
        database="regiondb"
    )