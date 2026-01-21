import psycopg2

conn = psycopg2.connect(
    database = "postgres",
    user = "postgres",
    host = "localhost",
    port = 5432,
    password = "password"
)