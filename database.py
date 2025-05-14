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
            user_id INTEGER NOT NULL,
            group_code TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            question_content TEXT,
            feedback TEXT,
            user_choice TEXT,
            correct_answer TEXT,
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
        
        # Check if username already exists
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone() is not None:
            return False
            
        # Check if there are already 2 accounts with the same name and email
        c.execute('SELECT COUNT(*) FROM users WHERE name = ? AND email = ?', (name, email))
        count = c.fetchone()[0]
        if count >= 2:
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
        
        # 먼저 사용자 정보를 가져옵니다
        c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        
        if not result:
            return False, None
            
        user_id, stored_password = result
        
        # 새로운 해시 방식으로 시도
        hashed_password = hash_password(password)
        if stored_password == hashed_password:
            return True, user_id
            
        # 이전 해시 방식으로 시도 (bcrypt)
        try:
            import bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                return True, user_id
        except:
            pass
            
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

def reset_learning_history():
    """학습 기록을 초기화합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM learning_history")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error resetting learning history: {e}")
        return False
    finally:
        if conn:
            conn.close()

def save_learning_history(user_id: int, group_code: str, score: int, total_questions: int, question_content: str = "", feedback: str = "", user_choice: str = "", correct_answer: str = ""):
    """학습 기록을 저장합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 현재 시간을 한국 시간으로 설정
        cursor.execute("""
            INSERT INTO learning_history 
            (user_id, group_code, score, total_questions, question_content, feedback, user_choice, correct_answer, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+9 hours'))
        """, (user_id, group_code, score, total_questions, question_content, feedback, user_choice, correct_answer))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving learning history: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_learning_history(user_id: int) -> list:
    """사용자의 학습 기록을 가져옵니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                group_code,
                score,
                total_questions,
                timestamp,
                question_content,
                feedback,
                user_choice,
                correct_answer
            FROM learning_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        """, (user_id,))
            
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting learning history: {e}")
        return []
    finally:
        if conn:
            conn.close()

def find_username(name: str, email: str) -> str | None:
    """이름과 이메일로 아이디를 찾습니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM users WHERE name = ? AND email = ?",
            (name, email)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error finding username: {e}")
        return None

def reset_password(username: str, email: str, new_password: str) -> bool:
    """비밀번호를 재설정합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 사용자 확인
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND email = ?",
            (username, email)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
            
        # 비밀번호 해시 생성
        hashed_password = hash_password(new_password)
        
        # 비밀번호 업데이트
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ? AND email = ?",
            (hashed_password, username, email)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False

def migrate_database():
    """기존 데이터베이스를 새로운 스키마로 마이그레이션합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 기존 테이블 백업
        cursor.execute("ALTER TABLE learning_history RENAME TO learning_history_old")
        
        # 새로운 스키마로 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            group_code TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            question_content TEXT,
            feedback TEXT,
            user_choice TEXT,
            correct_answer TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 기존 데이터 마이그레이션
        cursor.execute("""
        INSERT INTO learning_history 
        (user_id, group_code, score, total_questions, timestamp)
        SELECT user_id, group_code, score, total_questions, timestamp
        FROM learning_history_old
        """)
        
        # 기존 테이블 삭제
        cursor.execute("DROP TABLE learning_history_old")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error migrating database: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Initialize database when module is imported
init_db()
# Migrate database to new schema
migrate_database() 
