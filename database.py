import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# DB 경로 설정
DB_PATH = Path(__file__).parent / "quiz_app.db"

# DB 초기화 함수
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 사용자 테이블 생성
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

    # 학습 기록 테이블 생성
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

# 비밀번호 해시 처리
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 회원가입
def register_user(username, password, email, name):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone() is not None:
            return False

        c.execute('SELECT COUNT(*) FROM users WHERE name = ? AND email = ?', (name, email))
        if c.fetchone()[0] >= 2:
            return False

        hashed_pw = hash_password(password)
        c.execute('INSERT INTO users (username, password, email, name) VALUES (?, ?, ?, ?)',
                  (username, hashed_pw, email, name))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# 로그인 검증
def verify_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        result = c.fetchone()

        if not result:
            return False, None

        user_id, stored_password = result
        if stored_password == hash_password(password):
            return True, user_id
        return False, None
    except sqlite3.Error:
        return False, None
    finally:
        conn.close()

# 닉네임 변경
def update_username(user_id, new_username):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ? AND id != ?', (new_username, user_id))
        if c.fetchone() is not None:
            return False

        c.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# 학습 기록 초기화
def reset_learning_history():
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

# 학습 기록 저장
def save_learning_history(user_id, group_code, score, total_questions, question_content="", feedback="", user_choice="", correct_answer=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
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

# 학습 기록 조회
def get_learning_history(user_id):
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

# 아이디 찾기
def find_username(name, email):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE name = ? AND email = ?", (name, email))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error finding username: {e}")
        return None
    finally:
        if conn:
            conn.close()

# 비밀번호 재설정
def reset_password(username, email, new_password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND email = ?", (username, email))
        result = cursor.fetchone()

        if not result:
            return False

        hashed_pw = hash_password(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE username = ? AND email = ?",
                       (hashed_pw, username, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False
    finally:
        if conn:
            conn.close()

# DB 마이그레이션 처리
def migrate_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("ALTER TABLE learning_history RENAME TO learning_history_old")

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

        cursor.execute("""
            INSERT INTO learning_history 
            (user_id, group_code, score, total_questions, timestamp)
            SELECT user_id, group_code, score, total_questions, timestamp
            FROM learning_history_old
        """)

        cursor.execute("DROP TABLE learning_history_old")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error migrating database: {e}")
        return False
    finally:
        if conn:
            conn.close()
