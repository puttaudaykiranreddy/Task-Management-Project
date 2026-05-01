import os

with open('app.py', 'r') as f:
    app_code = f.read()

app_code = app_code.replace('%s', '?')
app_code = app_code.replace('cursor(dictionary=True)', 'cursor()')
app_code = app_code.replace('import mysql.connector', '')
app_code = app_code.replace('except mysql.connector.Error', 'except Exception')

# Remove mysql-connector-python from requirements
with open('requirements.txt', 'r') as f:
    reqs = f.read()
reqs = reqs.replace('mysql-connector-python==8.2.0', '')
with open('requirements.txt', 'w') as f:
    f.write(reqs)

with open('app.py', 'w') as f:
    f.write(app_code)

db_code = '''import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error connecting to SQLite: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, role TEXT DEFAULT 'Member', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, title TEXT NOT NULL, description TEXT,
        status TEXT DEFAULT 'To Do', assigned_to INTEGER, due_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE, FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL)""")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
'''

with open('db.py', 'w') as f:
    f.write(db_code)
