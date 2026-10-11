import pickle
import os
import sqlite3
import pandas as pd
import numpy as np
import datetime
import sys

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_MODEL_PATH = os.path.join(MODELS_DIR, 'gate_score_model.pkl')
RANK_MODEL_PATH = os.path.join(MODELS_DIR, 'gate_rank_model.pkl')

def load_models():
    """Loads score and rank models if available, otherwise returns None."""
    score_model = None
    rank_model = None
    
    if os.path.exists(SCORE_MODEL_PATH):
        with open(SCORE_MODEL_PATH, 'rb') as f:
            score_model = pickle.load(f)
            
    if os.path.exists(RANK_MODEL_PATH):
        with open(RANK_MODEL_PATH, 'rb') as f:
            rank_model = pickle.load(f)
            
    return score_model, rank_model

def extract_user_features(user_id: int):
    """
    Computes performance features for a specific user based on DB history.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Total attempts, overall accuracy, avg time
    cursor.execute("""
        SELECT 
            COUNT(a.id) as total_attempts,
            AVG(a.is_correct) as accuracy,
            AVG(a.time_spent_seconds) as avg_time
        FROM user_attempts a
        WHERE a.user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    total_attempts = row[0] or 0
    accuracy = row[1] or 0.0
    avg_time = row[2] or 120.0 # fallback default speed
    
    # 2. Medium and Hard accuracy
    cursor.execute("""
        SELECT AVG(a.is_correct) 
        FROM user_attempts a
        JOIN questions q ON a.question_id = q.id
        WHERE a.user_id = ? AND q.difficulty IN ('Medium', 'Hard')
    """, (user_id,))
    med_hard_acc = cursor.fetchone()[0] or (accuracy * 0.85) # fallback proxy
    
    # 3. Consistency (Attempts frequency over last 14 days)
    # Measured as: (days active in last 14 days) / 14
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    fortnight_ago = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT DATE(attempted_at))
        FROM user_attempts
        WHERE user_id = ? AND DATE(attempted_at) BETWEEN ? AND ?
    """, (user_id, fortnight_ago, today))
    active_days = cursor.fetchone()[0] or 0
    consistency = active_days / 14.0
    
    # 4. Syllabus Coverage
    cursor.execute("""
        SELECT COUNT(DISTINCT q.topic_id) 
        FROM user_attempts a
        JOIN questions q ON a.question_id = q.id
        WHERE a.user_id = ?
    """, (user_id,))
    attempted_topics = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM topics")
    total_topics = cursor.fetchone()[0] or 36
    syllabus_coverage = attempted_topics / float(total_topics) if total_topics > 0 else 0.0
    
    conn.close()
    
    return {
        "total_attempts": int(total_attempts),
        "accuracy": float(accuracy),
        "medium_hard_accuracy": float(med_hard_acc),
        "avg_time_spent": float(avg_time),
        "consistency": float(consistency),
        "syllabus_coverage": float(syllabus_coverage)
    }

def get_predictions(user_id: int, overrides=None):
    """
    Predicts GATE score and rank for the user.
    Allows passing overrides for 'What-If' simulations.
    """
    if overrides:
        features = overrides
    else:
        features = extract_user_features(user_id)
        
    score_model, rank_model = load_models()
    
    # Check if models exist. If not, use high-fidelity math fallback
    if score_model is None or rank_model is None:
        return run_heuristic_predictions(features)
        
    # Format features for RF Model as DataFrame to keep feature names
    feature_df = pd.DataFrame([{
        "total_attempts": features["total_attempts"],
        "accuracy": features["accuracy"],
        "medium_hard_accuracy": features["medium_hard_accuracy"],
        "avg_time_spent": features["avg_time_spent"],
        "consistency": features["consistency"],
        "syllabus_coverage": features["syllabus_coverage"]
    }])
    
    # Run Inference
    pred_score = score_model.predict(feature_df)[0]
    pred_score = int(np.clip(pred_score, 100, 1000))
    
    # Predict Rank based on score DataFrame
    rank_df = pd.DataFrame([{"gate_score": pred_score}])
    pred_rank = rank_model.predict(rank_df)[0]
    pred_rank = int(np.clip(pred_rank, 1, 150000))
    
    return pred_score, pred_rank, features

def run_heuristic_predictions(features):
    """Fallback prediction algorithm when pickles are missing."""
    total_attempts = features["total_attempts"]
    accuracy = features["accuracy"]
    med_hard_acc = features["medium_hard_accuracy"]
    avg_time = features["avg_time_spent"]
    consistency = features["consistency"]
    syllabus_coverage = features["syllabus_coverage"]
    
    if total_attempts == 0:
        return 100, 125000, features
        
    readiness_pct = (accuracy * 0.45) + (syllabus_coverage * 0.35) + (consistency * 0.20)
    
    # Forecast
    pred_score = int(120 + 820 * readiness_pct - (avg_time / 400.0) * 40 + (med_hard_acc * 60))
    pred_score = max(100, min(1000, pred_score))
    
    # Rank mapping
    if pred_score >= 850:
        pred_rank = int(1 + (1000 - pred_score) * 0.7)
    elif pred_score >= 700:
        pred_rank = int(105 + (850 - pred_score) * 6)
    elif pred_score >= 500:
        pred_rank = int(1005 + (700 - pred_score) * 20)
    elif pred_score >= 350:
        pred_rank = int(5005 + (500 - pred_score) * 120)
    else:
        pred_rank = int(23005 + (350 - pred_score) * 650)
        
    pred_rank = max(1, min(150000, pred_rank))
    return pred_score, pred_rank, features
