import sqlite3

conn = sqlite3.connect('smartkcet.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT;")
    conn.commit()
    print("Column added successfully.")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
