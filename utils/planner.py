import sqlite3
import datetime
import pandas as pd
import numpy as np
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def get_daily_plan(user_id: int, date_str: str):
    """
    Fetches the study plan for a specific user and date.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.id,
            p.topic_id,
            t.name as topic_name,
            s.name as subject_name,
            p.allocated_minutes,
            p.status
        FROM study_plans p
        JOIN topics t ON p.topic_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        WHERE p.user_id = ? AND p.date = ?
    """, (user_id, date_str))
    
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def generate_daily_plan(user_id: int, date_str: str, daily_hours: float):
    """
    Generates and saves a study plan for a specific date.
    Prioritizes topics with low accuracy and low practice coverage.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if a plan already exists for this date. If so, return it.
    existing = get_daily_plan(user_id, date_str)
    if existing:
        conn.close()
        return existing
        
    # Get all subjects, topics and current user attempts count & accuracy
    # We load it using pandas for clean sorting and calculations
    df_attempts = pd.read_sql_query("""
        SELECT 
            t.id as topic_id,
            t.name as topic_name,
            s.name as subject_name,
            COUNT(a.id) as attempts,
            SUM(a.is_correct) as correct
        FROM topics t
        JOIN subjects s ON t.subject_id = s.id
        LEFT JOIN questions q ON q.topic_id = t.id
        LEFT JOIN user_attempts a ON a.question_id = q.id AND a.user_id = ?
        GROUP BY t.id, t.name, s.name
    """, conn, params=(user_id,))
    
    # Calculate weakness parameters
    df_attempts['attempts'] = df_attempts['attempts'].fillna(0)
    df_attempts['correct'] = df_attempts['correct'].fillna(0)
    
    # Calculate accuracy. If no attempts, accuracy is assumed 0 to prioritize learning it.
    df_attempts['accuracy'] = np.where(
        df_attempts['attempts'] > 0,
        df_attempts['correct'] / df_attempts['attempts'],
        0.0
    )
    
    # Calculate coverage: 3 attempts is fully covered (1.0). Fewer attempts is less covered.
    df_attempts['coverage'] = np.minimum(df_attempts['attempts'] / 3.0, 1.0)
    
    # Weakness Score: Higher means weaker. Unattempted topics get high score.
    # Weakness Score = (1 - Accuracy) * 0.7 + (1 - Coverage) * 0.3
    df_attempts['weakness_score'] = (1.0 - df_attempts['accuracy']) * 0.7 + (1.0 - df_attempts['coverage']) * 0.3
    
    # Sort topics by weakness descending
    df_sorted = df_attempts.sort_values('weakness_score', ascending=False)
    
    # Convert daily hours to minutes
    total_minutes = int(daily_hours * 60)
    if total_minutes < 30:
        total_minutes = 60 # minimum 1 hour allocation
        
    # Choose 2 or 3 topics to study based on time available
    # Minimum study block is 30 mins, default is 60 or 90 mins
    allocated_topics = []
    
    if total_minutes >= 180:
        # 3 hours or more: 3 topics (e.g. 50%, 30%, 20%)
        t1_mins = int(total_minutes * 0.50)
        t2_mins = int(total_minutes * 0.30)
        t3_mins = int(total_minutes * 0.20)
        
        # Round to nearest 15 mins
        t1_mins = (t1_mins // 15) * 15
        t2_mins = (t2_mins // 15) * 15
        t3_mins = total_minutes - (t1_mins + t2_mins)
        
        allocated_topics = [
            (int(df_sorted.iloc[0]['topic_id']), t1_mins),
            (int(df_sorted.iloc[1]['topic_id']), t2_mins),
            (int(df_sorted.iloc[2]['topic_id']), t3_mins)
        ]
    else:
        # Less than 3 hours: 2 topics (e.g. 60%, 40%)
        t1_mins = int(total_minutes * 0.60)
        t2_mins = total_minutes - t1_mins
        
        # Round to nearest 15 mins
        t1_mins = (t1_mins // 15) * 15
        t2_mins = total_minutes - t1_mins
        
        allocated_topics = [
            (int(df_sorted.iloc[0]['topic_id']), t1_mins),
            (int(df_sorted.iloc[1]['topic_id']), t2_mins)
        ]

    # Save to database
    for t_id, mins in allocated_topics:
        if mins > 0:
            cursor.execute("""
                INSERT OR IGNORE INTO study_plans (user_id, date, topic_id, allocated_minutes, status)
                VALUES (?, ?, ?, ?, 'Pending')
            """, (user_id, date_str, t_id, mins))
            
    conn.commit()
    conn.close()
    
    return get_daily_plan(user_id, date_str)

def update_plan_status(user_id: int, date_str: str, topic_id: int, status: str):
    """
    Updates status of a study plan item.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE study_plans 
        SET status = ? 
        WHERE user_id = ? AND date = ? AND topic_id = ?
    """, (status, user_id, date_str, topic_id))
    conn.commit()
    conn.close()
