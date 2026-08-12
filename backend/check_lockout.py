import sqlite3
import datetime

try:
    conn = sqlite3.connect('smartkcet.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, failed_login_count, lockout_until FROM users WHERE email = 'admin@smartkcet.com'")
    row = cursor.fetchone()
    if row:
        print(f"User: {row[0]}, Failed log in count: {row[1]}, Lockout until: {row[2]}")
        
        # Reset if locked out
        if row[1] > 0 or row[2]:
            cursor.execute("UPDATE users SET failed_login_count = 0, lockout_until = NULL WHERE email = 'admin@smartkcet.com'")
            conn.commit()
            print("Reset failed_login_count and lockout_until.")
    else:
        print("User not found!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
