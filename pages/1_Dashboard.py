import streamlit as st
import pandas as pd
import datetime
import math
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from utils.visuals import (
    draw_readiness_gauge, 
    draw_subject_radar, 
    draw_activity_heatmap
)
from models.predictor import get_predictions

# Set page configuration
st.markdown("<h2 class='header-gradient'>📊 Aspirant Preparation Dashboard</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; margin-bottom: 25px;'>A real-time overview of your performance, mock score forecast, and daily coaching feedback.</p>", unsafe_allow_html=True)

# Helper function to query user metrics
def get_user_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Overall stats
    cursor.execute("""
        SELECT 
            COUNT(id) as total_solved,
            SUM(is_correct) as correct_solved,
            AVG(time_spent_seconds) as avg_speed
        FROM user_attempts 
        WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    stats = dict(row) if row else {"total_solved": 0, "correct_solved": 0, "avg_speed": 0}
    
    # 2. Total unique topics attempted
    cursor.execute("""
        SELECT COUNT(DISTINCT q.topic_id)
        FROM user_attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE a.user_id = ?
    """, (user_id,))
    attempted_topics = cursor.fetchone()[0] or 0
    
    # 3. Total topics in system
    cursor.execute("SELECT COUNT(*) FROM topics")
    total_topics = cursor.fetchone()[0] or 36
    
    # 4. Subject-wise performance
    df_subject = pd.read_sql_query("""
        SELECT 
            s.name as subject_name,
            COUNT(a.id) as total_attempts,
            SUM(a.is_correct) as correct_attempts,
            (CAST(SUM(a.is_correct) AS REAL) / COUNT(a.id)) * 100 as accuracy
        FROM subjects s
        JOIN topics t ON t.subject_id = s.id
        JOIN questions q ON q.topic_id = t.id
        JOIN user_attempts a ON a.question_id = q.id
        WHERE a.user_id = ?
        GROUP BY s.name
    """, conn, params=(user_id,))
    
    # 5. Attempts grouped by date for heatmap
    df_heatmap = pd.read_sql_query("""
        SELECT 
            DATE(attempted_at) as attempt_date,
            COUNT(id) as total_attempts
        FROM user_attempts
        WHERE user_id = ?
        GROUP BY DATE(attempted_at)
    """, conn, params=(user_id,))
    
    conn.close()
    
    stats["attempted_topics"] = attempted_topics
    stats["total_topics"] = total_topics
    
    return stats, df_subject, df_heatmap

# Fetch current session user stats
user_id = st.session_state.user_id
stats, df_subject, df_heatmap = get_user_stats(user_id)

total_solved = stats["total_solved"] or 0
correct_solved = stats["correct_solved"] or 0
accuracy = (correct_solved / total_solved * 100) if total_solved > 0 else 0.0
avg_speed = stats["avg_speed"] or 0.0
syllabus_coverage = (stats["attempted_topics"] / stats["total_topics"] * 100) if stats["total_topics"] > 0 else 0.0

# 6. ML Score & Rank Predictor (Inference Layer)
predicted_score, predicted_rank, computed_features = get_predictions(user_id)
readiness_pct = (accuracy * 0.45) + (syllabus_coverage * 0.35) + (computed_features["consistency"] * 100 * 0.20)
readiness_pct = max(0.0, min(100.0, readiness_pct))
confidence = round(80.0 + 15.0 * min(1.0, total_solved / 150.0), 1) if total_solved > 0 else 0.0

# Render main layout
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📋 Questions Solved</div>
        <div class="metric-value">{total_solved}</div>
        <div class="metric-sub">Across {stats["attempted_topics"]} topics</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🎯 Overall Accuracy</div>
        <div class="metric-value metric-value-green">{accuracy:.1f}%</div>
        <div class="metric-sub">{correct_solved} correct answers</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">⚡ Average Speed</div>
        <div class="metric-value">{int(avg_speed)}s</div>
        <div class="metric-sub">Per practice question</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi4:
    rank_display = f"#{predicted_rank:,}" if total_solved > 0 else "N/A"
    st.markdown(f"""
    <div class="metric-card glowing-card">
        <div class="metric-label">🔮 Predicted Score & AIR</div>
        <div class="metric-value metric-value-accent">{predicted_score} <span style="font-size: 1rem; color: #94A3B8;">({rank_display})</span></div>
        <div class="metric-sub">ML confidence: {confidence}%</div>
    </div>
    """, unsafe_allow_html=True)

# Middle Section: Readiness Meter & AI Coach
col_mid1, col_mid2 = st.columns([0.45, 0.55])

with col_mid1:
    st.markdown("<h4>Ready-to-Test Meter</h4>", unsafe_allow_html=True)
    fig_gauge = draw_readiness_gauge(readiness_pct)
    st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown(f"""
    <div style='margin-top: -15px;'>
        <p style='color: #94A3B8; font-size: 0.9rem;'>
            Syllabus Coverage: <strong>{syllabus_coverage:.1f}%</strong> | Accuracy: <strong>{accuracy:.1f}%</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_mid2:
    st.markdown("<h4>🧠 AI Study Coach Feedback</h4>", unsafe_allow_html=True)
    
    # Simple rule-based coach recommendations based on seeded values
    coach_feedback = []
    
    if total_solved == 0:
        coach_feedback = [
            "Welcome! You haven't attempted any questions yet. Head over to the **Practice Workspace** to begin.",
            "Suggested path: Start with **General Aptitude** or **Engineering Mathematics** to build momentum."
        ]
    else:
        # Find weak and strong subjects
        weak_subjects = df_subject[df_subject['accuracy'] < 50]['subject_name'].tolist()
        strong_subjects = df_subject[df_subject['accuracy'] > 75]['subject_name'].tolist()
        
        if weak_subjects:
            coach_feedback.append(f"⚠️ **Critical Attention Required**: Accuracy is low in **{', '.join(weak_subjects[:2])}**. Dedicate revision slots for these areas.")
        else:
            coach_feedback.append("✅ **Balanced Profile**: You do not have any critical subject-wise weaknesses (<50% accuracy) at the moment. Keep practicing!")
            
        if strong_subjects:
            coach_feedback.append(f"🔥 **Top Strength**: You are performing excellently in **{', '.join(strong_subjects[:2])}**. Use these as leverage during full-length mocks.")
        
        # Coverage suggestion
        if syllabus_coverage < 40:
            coach_feedback.append("📝 **Syllabus Expansion Needed**: Your topic coverage is low. Try attempting questions in new subjects rather than re-practicing comfortable ones.")
        elif syllabus_coverage > 80:
            coach_feedback.append("⚡ **Mock Test Ready**: You have covered most of the syllabus. We suggest scheduling 1 full length Mock Test this weekend.")
        else:
            coach_feedback.append("📈 **Targeted Revisions**: Focus on spaced repetition cards due this week to lock down concepts in memory.")

    for feedback in coach_feedback:
        st.markdown(f"<div style='background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; border-left: 3px solid #6366F1; margin-bottom: 12px; font-size: 0.92rem; color: #E2E8F0;'>{feedback}</div>", unsafe_allow_html=True)

# Bottom Section: Subject Mastery & Progress Heatmap
col_bot1, col_bot2 = st.columns([0.5, 0.5])

with col_bot1:
    st.markdown("<h4>Subject Mastery Analysis</h4>", unsafe_allow_html=True)
    if not df_subject.empty:
        fig_radar = draw_subject_radar(df_subject)
        st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Attempt questions in the Practice Workspace to view your subject radar chart.")

with col_bot2:
    st.markdown("<h4>📅 Daily Consistency Heatmap</h4>", unsafe_allow_html=True)
    fig_heatmap = draw_activity_heatmap(df_heatmap)
    st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})
    st.markdown("""
    <div style='margin-top: 10px; text-align: center; color: #64748B; font-size: 0.8rem;'>
        This heat grid plots daily practice volume over the past 5 weeks (35 days). Keep the streak green!
    </div>
    """, unsafe_allow_html=True)
