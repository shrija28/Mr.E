import psycopg2, sqlite3

pg_conn = psycopg2.connect("postgresql://postgres:shrijasanil%402005@localhost:5432/smartkcet_db")
c = pg_conn.cursor()
c.execute("UPDATE exams SET is_published = TRUE")
pg_conn.commit()

sq_conn = sqlite3.connect("backend/smartkcet.db")
c2 = sq_conn.cursor()
c2.execute("UPDATE exams SET is_published = TRUE")
sq_conn.commit()

print("[OK] ALL EXAMS PUBLISHED IN BOTH DATABASES!")
