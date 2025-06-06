from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import bcrypt
from functools import wraps
from dateutil import parser

app = Flask(__name__)
CORS(app)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
db = SQLAlchemy(app)

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    status = db.Column(db.String(20), default='pending')  # pending, in-progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'assignee_id': self.assignee_id,
            'creator_id': self.creator_id
        }

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='user') # 'user' or 'admin'
    tasks = db.relationship('Task', backref='assignee', lazy=True, foreign_keys=[Task.assignee_id])

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'profile_picture': self.profile_picture,
            'created_at': self.created_at.isoformat(),
            'role': self.role
        }

# Create database tables and initial admin user
with app.app_context():
    db.create_all()
    # Create a default admin user if none exists
    if not User.query.filter_by(username='admin').first():
        hashed_password = bcrypt.hashpw(b'admin123', bcrypt.gensalt())
        admin_user = User(
            username='admin',
            email='admin@taskapp.com',
            password=hashed_password.decode('utf-8'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Default admin user created (username: admin, password: admin123)')

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if current_user.role != 'admin':
                return jsonify({'message': 'Administrator access required!'}), 403
        except:
            return jsonify({'message': 'Token is invalid or user is not admin!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Auth routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password.decode('utf-8'),
        role='user' # New users are 'user' by default
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

@app.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify(current_user.to_dict())

@app.route('/api/auth/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.json
    if 'username' in data:
        current_user.username = data['username']
    if 'email' in data:
        current_user.email = data['email']
    if 'profile_picture' in data:
        current_user.profile_picture = data['profile_picture']
    if 'password' in data:
        current_user.password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db.session.commit()
    return jsonify(current_user.to_dict())

# Task routes
@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks(current_user):
    status = request.args.get('status')
    priority = request.args.get('priority')
    sort_by = request.args.get('sort_by', 'due_date')
    
    # Start with a base query
    query = Task.query

    # Apply filtering based on user role
    if current_user.role != 'admin':
        # Regular users only see tasks they created or are assigned to
        query = query.filter(
            (Task.creator_id == current_user.id) | (Task.assignee_id == current_user.id)
        )
    
    # Apply status and priority filters if provided
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    
    # Apply sorting
    if sort_by == 'due_date':
        query = query.order_by(Task.due_date.asc())
    elif sort_by == 'priority':
        query = query.order_by(Task.priority.desc())
    elif sort_by == 'created_at':
        query = query.order_by(Task.created_at.desc())
    
    tasks = query.all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/api/tasks', methods=['POST'])
@token_required
def create_task(current_user):
    data = request.json
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        due_date=parser.parse(data['due_date']) if 'due_date' in data and data['due_date'] else None,
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'pending'),
        creator_id=current_user.id,
        assignee_id=data.get('assignee_id')
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(current_user, task_id):
    task = Task.query.get_or_404(task_id)
    # Allow creator or assignee to update
    if task.creator_id != current_user.id and task.assignee_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.json
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.due_date = parser.parse(data['due_date']) if 'due_date' in data and data['due_date'] else task.due_date
    task.priority = data.get('priority', task.priority)
    task.status = data.get('status', task.status)
    task.assignee_id = data.get('assignee_id', task.assignee_id)
    
    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(current_user, task_id):
    task = Task.query.get_or_404(task_id)
    # Only creator can delete
    if task.creator_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    db.session.delete(task)
    db.session.commit()
    return '', 204

# User list route for task assignment (accessible only by admin)
@app.route('/api/users', methods=['GET'])
@admin_required
def get_users(current_user):
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

if __name__ == '__main__':
    app.run(debug=True) 