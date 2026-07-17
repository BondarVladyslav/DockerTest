import psycopg2
conn = psycopg2.connect(
    dbname='library_db',
    user='library_user',
    password='1VB1Vlad',
    host='localhost',
    port='5432'
)
print('Connected!')
conn.close()