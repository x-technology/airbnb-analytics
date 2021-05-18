import psycopg2
import os

from dotenv import load_dotenv
load_dotenv()

CONN_STRING = os.getenv("POSTGRES_CONN")


connection = psycopg2.connect(CONN_STRING)

cursor = connection.cursor()

cursor.execute("SELECT * FROM airbnb.listings LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)

cursor.close()
connection.close()