import os
import sys
import subprocess

# Auto-install dependencies if they are missing
try:
    import flask
    import flask_cors
    import dotenv
    import jwt
    import bcrypt
    
except ImportError:
    print("Dependencies missing. Auto-installing from requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully. Restarting application...")
    os.execv(sys.executable, ['python'] + sys.argv)

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import jwt
import bcrypt
import datetime
from functools import wraps
from db import get_db_connection, init_db

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_fallback_secret_key_here')

# --- Middleware ---

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
            # Fetch user to pass to route
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (current_user_id,))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user['role'] != 'Admin':
            return jsonify({'message': 'Admin privilege required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


# --- Static / Template Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/project')
def project_view():
    return render_template('project.html')


# --- API Routes ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'Member') # Default to Member if not provided

    if not name or not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password.decode('utf-8'), role)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as err:
        return jsonify({'message': 'Registration failed', 'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        token = jwt.encode({
            'user_id': user['id'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        })
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/projects', methods=['GET'])
@token_required
def get_projects(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)

@app.route('/api/projects', methods=['POST'])
@token_required
@admin_required
def create_project(current_user):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')

    if not title:
        return jsonify({'message': 'Title is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (title, description, created_by) VALUES (?, ?, ?)",
        (title, description, current_user['id'])
    )
    conn.commit()
    project_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Project created!', 'id': project_id}), 201

@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks(current_user):
    project_id = request.args.get('project_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if project_id:
        cursor.execute("SELECT t.*, u.name as assigned_to_name FROM tasks t LEFT JOIN users u ON t.assigned_to = u.id WHERE t.project_id = ?", (project_id,))
    else:
        cursor.execute("SELECT t.*, p.title as project_title, u.name as assigned_to_name FROM tasks t JOIN projects p ON t.project_id = p.id LEFT JOIN users u ON t.assigned_to = u.id")
        
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
@token_required
def create_task(current_user):
    data = request.get_json()
    project_id = data.get('project_id')
    title = data.get('title')
    description = data.get('description', '')
    status = data.get('status', 'To Do')
    assigned_to = data.get('assigned_to')
    due_date = data.get('due_date')

    if not title or not project_id:
        return jsonify({'message': 'Title and project_id are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (project_id, title, description, status, assigned_to, due_date) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, title, description, status, assigned_to, due_date)
    )
    conn.commit()
    task_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Task created!', 'id': task_id}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(current_user, task_id):
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({'message': 'Status is required to update'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Task updated successfully!'})

@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total projects
    cursor.execute("SELECT COUNT(*) as count FROM projects")
    projects_count = cursor.fetchone()['count']
    
    # Task stats
    cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
    task_stats = cursor.fetchall()
    
    # Overdue tasks
    cursor.execute("SELECT * FROM tasks WHERE due_date < CURDATE() AND status != 'Done'")
    overdue_tasks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'projects_count': projects_count,
        'task_stats': task_stats,
        'overdue_tasks': overdue_tasks
    })

@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)


if __name__ == '__main__':
    # Initialize DB tables if they don't exist
    init_db()
    app.run(debug=True, port=5000)
