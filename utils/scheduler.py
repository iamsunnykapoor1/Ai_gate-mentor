import sqlite3
import datetime
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def get_due_revisions(user_id: int):
    """
    Returns list of due topics for revision.
    Next revision date <= today
    """
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT 
            r.id as schedule_id,
            r.topic_id,
            t.name as topic_name,
            s.name as subject_name,
            r.ease_factor,
            r.interval_days,
            r.repetitions,
            r.next_revision_date
        FROM revision_schedule r
        JOIN topics t ON r.topic_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        WHERE r.user_id = ? AND r.next_revision_date <= ?
        ORDER BY r.next_revision_date ASC
    """, (user_id, today_str))
    
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def schedule_topic_revision(user_id: int, topic_id: int, quality: int):
    """
    Applies the SuperMemo-2 (SM-2) algorithm to calculate the next revision date.
    quality: rating between 0 (completely forgot) and 5 (perfect recall).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if a schedule already exists
    cursor.execute("""
        SELECT ease_factor, interval_days, repetitions 
        FROM revision_schedule 
        WHERE user_id = ? AND topic_id = ?
    """, (user_id, topic_id))
    row = cursor.fetchone()
    
    if row:
        ease_factor = row["ease_factor"]
        interval_days = row["interval_days"]
        repetitions = row["repetitions"]
    else:
        # Default start states
        ease_factor = 2.5
        interval_days = 1
        repetitions = 0

    # SM-2 Algorithm logic
    if quality < 3:
        # If quality is poor, reset repetitions and schedule for next day
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = int(round(interval_days * ease_factor))
            
        repetitions += 1
        
        # Calculate new ease factor
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ease_factor = max(1.3, ease_factor)

    # Calculate next revision date
    today = datetime.date.today()
    next_revision_date = (today + datetime.timedelta(days=interval_days)).strftime("%Y-%m-%d")
    
    # Insert or update
    cursor.execute("""
        INSERT INTO revision_schedule (user_id, topic_id, ease_factor, interval_days, repetitions, next_revision_date, last_reviewed_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, topic_id) DO UPDATE SET
            ease_factor = excluded.ease_factor,
            interval_days = excluded.interval_days,
            repetitions = excluded.repetitions,
            next_revision_date = excluded.next_revision_date,
            last_reviewed_at = CURRENT_TIMESTAMP
    """, (user_id, topic_id, ease_factor, interval_days, repetitions, next_revision_date))
    
    conn.commit()
    conn.close()
    return interval_days, next_revision_date
