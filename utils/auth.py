import sqlite3
import bcrypt
import streamlit as st
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def login_user(username_or_email: str, password: str):
    """
    Checks user credentials against the database.
    Returns user row dictionary if successful, else None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?", 
            (username_or_email, username_or_email)
        )
        row = cursor.fetchone()
        if row:
            user_data = dict(row)
            if verify_password(password, user_data['password_hash']):
                return user_data
        return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None
    finally:
        conn.close()

def register_user(username: str, email: str, password: str, target_year: int, study_hours: float) -> bool:
    """
    Registers a new user in the database.
    Returns True if successful, False if username or email already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, target_gate_year, daily_study_hours) VALUES (?, ?, ?, ?, ?)",
            (username, email, hashed_pw, target_year, study_hours)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username or Email already exists
        return False
    except Exception as e:
        print(f"Error registering user: {e}")
        return False
    finally:
        conn.close()

def update_user_profile(user_id: int, target_year: int, study_hours: float) -> bool:
    """Updates user target year and daily study hours."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET target_gate_year = ?, daily_study_hours = ? WHERE id = ?",
            (target_year, study_hours, user_id)
        )
        conn.commit()
        # Update session state as well
        st.session_state.target_gate_year = target_year
        st.session_state.daily_study_hours = study_hours
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False
    finally:
        conn.close()

def init_session_state():
    """Initializes standard authentication states in Streamlit session_state."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'email' not in st.session_state:
        st.session_state.email = None
    if 'target_gate_year' not in st.session_state:
        st.session_state.target_gate_year = 2027
    if 'daily_study_hours' not in st.session_state:
        st.session_state.daily_study_hours = 4.0

def set_login_session(user_data):
    """Sets session state after successful login."""
    st.session_state.logged_in = True
    st.session_state.user_id = user_data['id']
    st.session_state.username = user_data['username']
    st.session_state.email = user_data['email']
    st.session_state.target_gate_year = user_data['target_gate_year']
    st.session_state.daily_study_hours = user_data['daily_study_hours']

def logout_user():
    """Clears authentication session states."""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.target_gate_year = 2027
    st.session_state.daily_study_hours = 4.0
    st.rerun()
