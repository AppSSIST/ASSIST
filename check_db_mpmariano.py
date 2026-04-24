import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

print("=== Checking auth_user table ===")
cur.execute("SELECT id, username, email FROM auth_user WHERE email LIKE ? OR username LIKE ?", ('%mpmariano%', '%mpmariano%'))
rows = cur.fetchall()
print(f'Found {len(rows)} user records')
for r in rows:
    print(r)

print("\n=== Checking hello_faculty table ===")
cur.execute("SELECT id, first_name, last_name, email FROM hello_faculty WHERE email LIKE ?", ('%mpmariano%',))
rows = cur.fetchall()
print(f'Found {len(rows)} faculty records')
for r in rows:
    print(r)

conn.close()
