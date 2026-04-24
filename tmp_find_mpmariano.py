import sqlite3
from pathlib import Path

db = Path('db.sqlite3')
print('DB exists', db.exists())
conn = sqlite3.connect(str(db))
cur = conn.cursor()
for table in ['auth_user', 'hello_faculty', 'django_session']:
    try:
        cur.execute(f'PRAGMA table_info({table})')
        cols = [row[1] for row in cur.fetchall()]
        if not cols:
            continue
        q = ' OR '.join([f"{c} LIKE '%mpmariano%'" for c in cols if c.lower() not in ('id',)])
        if not q:
            continue
        cur.execute(f"SELECT '{table}', * FROM {table} WHERE {q}")
        rows = cur.fetchall()
        print(table, 'matches', len(rows))
        for r in rows[:5]:
            print(r)
    except Exception as e:
        print('skip', table, e)
conn.close()
