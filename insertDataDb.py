import psycopg2

import databaseConnection
from databaseConnection import conn

cur = databaseConnection.conn.cursor()
def insertData(candle_date, interval,close_price, image):
   cur.execute(
        "INSERT INTO nifty_15min_images (trade_date, interval,close_price, image) VALUES (%s, %s, %s,%s)",
        (candle_date, interval,close_price, psycopg2.Binary(image))
    )

print("Inserted DB")


print("Candlestick image stored in database")