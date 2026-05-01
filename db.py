import mysql.connector
from mysql.connector import Error
import os

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQLHOST") or os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost"),
            user=os.getenv("MYSQLUSER") or os.getenv("MYSQL_USER") or os.getenv("DB_USER", "root"),
            password=os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_ROOT_PASSWORD") or os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", ""),
            database=os.getenv("MYSQLDATABASE") or os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME", "team_task_manager"),
            port=os.getenv("MYSQLPORT") or os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306")
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def init_db():
    connection = mysql.connector.connect(
        host=os.getenv("MYSQLHOST") or os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost"),
        user=os.getenv("MYSQLUSER") or os.getenv("MYSQL_USER") or os.getenv("DB_USER", "root"),
        password=os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_ROOT_PASSWORD") or os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", ""),
        port=os.getenv("MYSQLPORT") or os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306")
    )
    cursor = connection.cursor()
    
    # Create DB if it doesn't exist
    db_name = os.getenv("MYSQLDATABASE") or os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME", "team_task_manager")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    cursor.execute(f"USE {db_name}")

    # Create Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('Admin', 'Member') DEFAULT 'Member',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        created_by INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Create Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        project_id INT,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        status ENUM('To Do', 'In Progress', 'Done') DEFAULT 'To Do',
        assigned_to INT,
        due_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
    )
    """)

    connection.commit()
    cursor.close()
    connection.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    init_db()
