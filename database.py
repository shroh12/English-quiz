import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# Database initialization
DB_PATH = Path(__file__).parent / "quiz_app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create learning history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            group_code TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """비밀번호를 해시화하는 함수"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email, name):
    """새로운 사용자를 등록하는 함수"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if username or email already exists
        c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if c.fetchone() is not None:
            return False
        
        # Insert new user
        hashed_password = hash_password(password)
        c.execute(
            'INSERT INTO users (username, password, email, name) VALUES (?, ?, ?, ?)',
            (username, hashed_password, email, name)
        )
        conn.commit()
        return True
        
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    """사용자 인증을 수행하는 함수"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        hashed_password = hash_password(password)
        c.execute(
            'SELECT id FROM users WHERE username = ? AND password = ?',
            (username, hashed_password)
        )
        result = c.fetchone()
        
        if result:
            return True, result[0]  # Return success and user_id
        return False, None
        
    except sqlite3.Error:
        return False, None
    finally:
        conn.close()

def update_username(user_id, new_username):
    """사용자의 닉네임을 변경하는 함수"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if new username already exists
        c.execute('SELECT id FROM users WHERE username = ? AND id != ?', (new_username, user_id))
        if c.fetchone() is not None:
            return False
        
        # Update username
        c.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
        conn.commit()
        return True
        
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def save_learning_history(user_id, group_code, score, total_questions):
    """학습 기록을 저장하는 함수"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute(
            'INSERT INTO learning_history (user_id, group_code, score, total_questions) VALUES (?, ?, ?, ?)',
            (user_id, group_code, score, total_questions)
        )
        conn.commit()
        return True
        
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_learning_history(user_id):
    """사용자의 학습 기록을 조회하는 함수"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT group_code, score, total_questions, timestamp 
            FROM learning_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        return c.fetchall()
        
    except sqlite3.Error:
        return []
    finally:
        conn.close()

# Initialize database when module is imported
init_db() 
