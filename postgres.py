#!/usr/bin/env python

import psycopg2

conn = psycopg2.connect(database = "packages_production",
                        user = "postgres",
                        host = 'localhost',
                        password = 'password',
                        port = 5432)

cur = conn.cursor()
cur.execute('SELECT count(*) FROM packages;')
rows = cur.fetchone()
conn.commit()
conn.close()
print(rows[0])
