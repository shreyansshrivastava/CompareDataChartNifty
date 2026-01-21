import databaseConnection
cur = databaseConnection.conn.cursor()
def checkTable():

    cur.execute("""SELECT EXISTS (
            SELECT 1
            FROM pg_tables
            WHERE schemaname = 'public' AND tablename = 'nifty_15min_images'
        );""")
    q1 = cur.fetchone()[0]
    if q1:
        print("Table present")
    else:
        cur.execute("""CREATE TABLE IF NOT EXISTS nifty_15min_images (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    candle_date DATE,
    interval VARCHAR(100),
    image BYTEA,
    close_price BYTEA
);""")
        print("Table create")
#cur.execute("""Drop table datacamp_courses;""")
    databaseConnection.conn.commit()

