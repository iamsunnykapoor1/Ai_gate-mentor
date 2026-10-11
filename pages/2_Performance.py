import streamlit as st
import pandas as pd
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from utils.visuals import (
    draw_accuracy_trend,
    draw_time_vs_accuracy,
    draw_solved_distribution
)

# Header
st.markdown("<h2 class='header-gradient'>📈 Performance & Topic Tracking</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; margin-bottom: 25px;'>Analyze topic-specific accuracy, solve-speed efficiency, and historical learning progress trends.</p>", unsafe_allow_html=True)

# Fetch user metrics
def get_performance_data(user_id):
    conn = get_connection()
    
    # 1. Topic-wise aggregation
    df_topics = pd.read_sql_query("""
        SELECT 
            t.name as topic_name,
            s.name as subject_name,
            COUNT(a.id) as total_attempts,
            SUM(a.is_correct) as correct_attempts,
            (CAST(SUM(a.is_correct) AS REAL) / COUNT(a.id)) * 100 as accuracy,
            AVG(a.time_spent_seconds) as avg_time_spent
        FROM topics t
        JOIN subjects s ON t.subject_id = s.id
        JOIN questions q ON q.topic_id = t.id
        JOIN user_attempts a ON a.question_id = q.id
        WHERE a.user_id = ?
        GROUP BY t.id, t.name, s.name
    """, conn, params=(user_id,))
    
    # 2. Daily progress trend
    df_trend = pd.read_sql_query("""
        SELECT 
            DATE(attempted_at) as attempt_date,
            COUNT(id) as total_attempts,
            (CAST(SUM(is_correct) AS REAL) / COUNT(id)) * 100 as daily_accuracy
        FROM user_attempts
        WHERE user_id = ?
        GROUP BY DATE(attempted_at)
        ORDER BY attempt_date ASC
    """, conn, params=(user_id,))
    
    # 3. Subject solved distributions
    df_subject_solved = pd.read_sql_query("""
        SELECT 
            s.name as subject_name,
            COUNT(a.id) as total_attempts
        FROM subjects s
        JOIN topics t ON t.subject_id = s.id
        JOIN questions q ON q.topic_id = t.id
        JOIN user_attempts a ON a.question_id = q.id
        WHERE a.user_id = ?
        GROUP BY s.name
    """, conn, params=(user_id,))
    
    conn.close()
    return df_topics, df_trend, df_subject_solved

user_id = st.session_state.user_id
df_topics, df_trend, df_subject_solved = get_performance_data(user_id)

if df_topics.empty:
    st.info("No practice attempts recorded. Start solving questions in the Practice Workspace to view performance metrics.")
else:
    # Segment Topics into Weak (< 50%), Moderate (50%-75%), Strong (> 75%)
    weak_df = df_topics[df_topics['accuracy'] < 50.0].sort_values('accuracy', ascending=True)
    strong_df = df_topics[df_topics['accuracy'] >= 75.0].sort_values('accuracy', ascending=False)
    mod_df = df_topics[(df_topics['accuracy'] >= 50.0) & (df_topics['accuracy'] < 75.0)].sort_values('accuracy', ascending=False)

    col1, col2 = st.columns([0.45, 0.55])
    
    with col1:
        st.markdown("<div class='metric-card' style='height: 380px; overflow-y: auto;'>", unsafe_allow_html=True)
        st.markdown("<h4>🔍 Topic strength breakdown</h4>", unsafe_allow_html=True)
        
        tab_weak, tab_strong, tab_moderate = st.tabs([
            f"❌ Weak ({len(weak_df)})", 
            f"✅ Strong ({len(strong_df)})", 
            f"⚠️ Moderate ({len(mod_df)})"
        ])
        
        with tab_weak:
            if weak_df.empty:
                st.write("🎉 Good job! You have no weak topics.")
            else:
                for idx, row in weak_df.iterrows():
                    st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.05); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #EF4444; margin-bottom: 8px; font-size: 0.88rem;">
                        <strong>{row['topic_name']}</strong> <span style="color: #64748B;">({row['subject_name']})</span><br>
                        Accuracy: <span style="color: #F87171; font-weight: 600;">{row['accuracy']:.1f}%</span> | Solved: {row['total_attempts']} | Speed: {int(row['avg_time_spent'])}s
                    </div>
                    """, unsafe_allow_html=True)
                    
        with tab_strong:
            if strong_df.empty:
                st.write("Keep practicing to build your strong topics catalog!")
            else:
                for idx, row in strong_df.iterrows():
                    st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.05); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #10B981; margin-bottom: 8px; font-size: 0.88rem;">
                        <strong>{row['topic_name']}</strong> <span style="color: #64748B;">({row['subject_name']})</span><br>
                        Accuracy: <span style="color: #34D399; font-weight: 600;">{row['accuracy']:.1f}%</span> | Solved: {row['total_attempts']} | Speed: {int(row['avg_time_spent'])}s
                    </div>
                    """, unsafe_allow_html=True)
                    
        with tab_moderate:
            if mod_df.empty:
                st.write("No moderate topics identified.")
            else:
                for idx, row in mod_df.iterrows():
                    st.markdown(f"""
                    <div style="background: rgba(245, 158, 11, 0.05); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #F59E0B; margin-bottom: 8px; font-size: 0.88rem;">
                        <strong>{row['topic_name']}</strong> <span style="color: #64748B;">({row['subject_name']})</span><br>
                        Accuracy: <span style="color: #FBBF24; font-weight: 600;">{row['accuracy']:.1f}%</span> | Solved: {row['total_attempts']} | Speed: {int(row['avg_time_spent'])}s
                    </div>
                    """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='metric-card' style='height: 380px;'>", unsafe_allow_html=True)
        st.markdown("<h4>📈 Accuracy Improvement Trend</h4>", unsafe_allow_html=True)
        fig_trend = draw_accuracy_trend(df_trend)
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Middle Row: Bubble Plot & Solved bar chart
    col_mid1, col_mid2 = st.columns([0.55, 0.45])
    
    with col_mid1:
        st.markdown("<div class='metric-card' style='height: 380px;'>", unsafe_allow_html=True)
        st.markdown("<h4>⚡ Solve Time vs. Topic Accuracy</h4>", unsafe_allow_html=True)
        fig_bubble = draw_time_vs_accuracy(df_topics)
        st.plotly_chart(fig_bubble, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_mid2:
        st.markdown("<div class='metric-card' style='height: 380px;'>", unsafe_allow_html=True)
        st.markdown("<h4>📋 Syllabus Volume per Subject</h4>", unsafe_allow_html=True)
        fig_solved = draw_solved_distribution(df_subject_solved)
        st.plotly_chart(fig_solved, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Detailed Table
    st.markdown("### Detailed Topic Mastery Grid")
    
    # Format accuracy and average speed for display
    df_display = df_topics.copy()
    df_display['accuracy'] = df_display['accuracy'].map(lambda x: f"{x:.1f}%")
    df_display['avg_time_spent'] = df_display['avg_time_spent'].map(lambda x: f"{int(x)}s")
    
    df_display.columns = ["Topic", "Subject", "Total Solved", "Correct Solved", "Accuracy Rate", "Avg Solve Speed"]
    
    st.dataframe(df_display, use_container_width=True)
