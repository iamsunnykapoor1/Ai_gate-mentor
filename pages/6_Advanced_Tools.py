import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from models.predictor import extract_user_features, get_predictions

st.markdown("<h2 class='header-gradient'>🔮 Advanced AI Tools</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; margin-bottom: 25px;'>Simulate different preparation strategies, benchmark against peers, and consult the AI Study Coach.</p>", unsafe_allow_html=True)

user_id = st.session_state.user_id

# 1. Fetch current real stats for comparisons
real_score, real_rank, real_features = get_predictions(user_id)

tab_whatif, tab_peer, tab_coach = st.tabs([
    "🔮 What-If Score Simulator", 
    "📊 Peer Benchmarking", 
    "🤖 Interactive AI Study Coach"
])

# ==================== WHAT-IF SIMULATOR TAB ====================
with tab_whatif:
    st.markdown("### Simulate Preparation Adjustments")
    st.markdown("Drag the sliders to simulate changes in your study habits and accuracy, and see the immediate forecasted impact on your GATE Score and Rank.")
    
    col_sim_l, col_sim_r = st.columns([0.65, 0.35])
    
    with col_sim_l:
        # Load sliders with current real values as defaults
        sim_attempts = st.slider("Total Questions Solved", 10, 1000, real_features["total_attempts"], step=10)
        sim_accuracy = st.slider("Overall Practice Accuracy (%)", 30, 100, int(real_features["accuracy"] * 100), step=1) / 100.0
        sim_med_hard = st.slider("Medium & Hard Question Accuracy (%)", 20, 100, int(real_features["medium_hard_accuracy"] * 100), step=1) / 100.0
        sim_speed = st.slider("Average Solve Time (seconds)", 30, 240, int(real_features["avg_time_spent"]), step=5)
        sim_coverage = st.slider("Syllabus Coverage (%)", 10, 100, int(real_features["syllabus_coverage"] * 100), step=5) / 100.0
        sim_consistency = st.slider("Study Consistency index (%)", 10, 100, int(real_features["consistency"] * 100), step=5) / 100.0

    with col_sim_r:
        # Run prediction on simulated overrides
        sim_overrides = {
            "total_attempts": sim_attempts,
            "accuracy": sim_accuracy,
            "medium_hard_accuracy": sim_med_hard,
            "avg_time_spent": sim_speed,
            "consistency": sim_consistency,
            "syllabus_coverage": sim_coverage
        }
        
        sim_score, sim_rank, _ = get_predictions(user_id, overrides=sim_overrides)
        
        score_diff = sim_score - real_score
        rank_diff = real_rank - sim_rank # positive means rank improved (smaller number)
        
        # Simulated display card
        st.markdown("<div class='metric-label'>Simulated GATE Score</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value metric-value-accent'>{sim_score}</div>", unsafe_allow_html=True)
        if score_diff >= 0:
            st.markdown(f"<p style='color: #34D399; font-size: 0.9rem; margin-top: 5px;'>📈 +{score_diff} points from actual</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #F87171; font-size: 0.9rem; margin-top: 5px;'>📉 {score_diff} points from actual</p>", unsafe_allow_html=True)
        
        st.markdown("<div class='metric-label'>Simulated All India Rank</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value metric-value-green'>#{sim_rank:,}</div>", unsafe_allow_html=True)
        if rank_diff >= 0:
            st.markdown(f"<p style='color: #34D399; font-size: 0.9rem; margin-top: 5px;'>🚀 Improved by {rank_diff:,} spots</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #F87171; font-size: 0.9rem; margin-top: 5px;'>🔻 Declined by {abs(rank_diff):,} spots</p>", unsafe_allow_html=True)


# ==================== PEER BENCHMARKING TAB ====================
with tab_peer:
    st.markdown("### Peer Benchmarking & Statistics")
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'synthetic_peers.csv')
    
    if not os.path.exists(csv_path):
        st.warning("Peer comparison data is not generated. Please run model training first.")
    else:
        df_peers = pd.read_csv(csv_path)
        
        # Calculate peer comparisons
        peer_avg_score = int(df_peers['gate_score'].mean())
        peer_max_score = int(df_peers['gate_score'].max())
        
        # Calculate Percentile
        # Number of peers with score lower than user's real score
        lower_score_count = sum(df_peers['gate_score'] < real_score)
        percentile = (lower_score_count / len(df_peers)) * 100.0
        
        col_peer1, col_peer2, col_peer3 = st.columns(3)
        with col_peer1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">👥 Peer Average Score</div>
                <div class="metric-value">{peer_avg_score}</div>
                <div class="metric-sub">Mean score of 1,200 peer aspirants</div>
            </div>
            """, unsafe_allow_html=True)
        with col_peer2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🏆 Peer Highest Score</div>
                <div class="metric-value">{peer_max_score}</div>
                <div class="metric-sub">Highest recorded peer score</div>
            </div>
            """, unsafe_allow_html=True)
        with col_peer3:
            st.markdown(f"""
            <div class="metric-card glowing-card">
                <div class="metric-label">⚡ Your Peer Percentile</div>
                <div class="metric-value metric-value-green">{percentile:.1f}%</div>
                <div class="metric-sub">You outperform {percentile:.1f}% of peers</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Draw Distribution Histogram
        st.markdown("#### Peer Score Distribution overlay")
        
        fig_hist = go.Figure()
        # Peer distribution
        fig_hist.add_trace(go.Histogram(
            x=df_peers['gate_score'],
            name='Peer scores',
            marker_color='rgba(99, 102, 241, 0.4)',
            nbinsx=40
        ))
        
        # User line overlay
        fig_hist.add_vline(
            x=real_score, 
            line_width=3, 
            line_dash="dash", 
            line_color="#10B981",
            annotation_text=f"You ({real_score})",
            annotation_position="top right"
        )
        
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            showlegend=False,
            xaxis=dict(title="GATE Score", gridcolor="#1E293B", tickfont=dict(color="#64748B")),
            yaxis=dict(title="Count", gridcolor="#1E293B", tickfont=dict(color="#64748B"))
        )
        
        st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})


# ==================== AI COACH TAB ====================
with tab_coach:
    st.markdown("### Interactive AI Study Coach")
    st.markdown("Choose a topic of concern or query, and the Coach will perform a diagnostic analysis on your performance records to offer advice.")
    
    coach_query = st.selectbox(
        "Ask the AI Study Coach:",
        [
            "Select a question...",
            "What is my biggest preparation bottleneck right now?",
            "Give me a clear roadmap to increase my score by 150 points.",
            "Evaluate my study speed and solving consistency.",
            "Identify my top subject strengths and how to leverage them."
        ]
    )
    
    if coach_query != "Select a question...":

        st.markdown(f"<h5>👨‍🏫 Coach Response:</h5>", unsafe_allow_html=True)
        
        conn = get_connection()
        # Fetch topic performance details
        df_topics = pd.read_sql_query("""
            SELECT 
                t.name as topic_name,
                s.name as subject_name,
                COUNT(a.id) as attempts,
                AVG(a.is_correct) as accuracy
            FROM topics t
            JOIN subjects s ON t.subject_id = s.id
            JOIN questions q ON q.topic_id = t.id
            JOIN user_attempts a ON a.question_id = q.id
            WHERE a.user_id = ?
            GROUP BY t.id, t.name, s.name
        """, conn, params=(user_id,))
        conn.close()
        
        # Diagnostic analysis
        if df_topics.empty:
            st.write("You must solve at least 5 questions in the practice workspace before I can conduct a detailed diagnosis!")
        else:
            if coach_query == "What is my biggest preparation bottleneck right now?":
                # Find weakest topic
                weakest = df_topics.sort_values('accuracy', ascending=True).iloc[0]
                st.markdown(f"""
                Your primary bottleneck is currently **{weakest['topic_name']}** under **{weakest['subject_name']}**, where you have an accuracy of only **{weakest['accuracy']*100:.1f}%**.
                
                **🎯 Correction Strategy:**
                1. **Theory Check**: Do not solve more questions immediately. Re-read the core concepts (e.g., standard textbook or notes) for this specific topic.
                2. **Easy Drill**: Go to the *Practice Workspace*, filter *{weakest['topic_name']}*, and choose **Easy** difficulty. Solve 5 questions slowly to build confidence.
                3. **Interval review**: Add this topic to your revision deck immediately to ensure you reinforce it.
                """)
                
            elif coach_query == "Give me a clear roadmap to increase my score by 150 points.":
                # Find 2 weakest subjects
                df_subs = df_topics.groupby('subject_name')['accuracy'].mean().reset_index()
                weak_subs = df_subs.sort_values('accuracy', ascending=True).head(2)['subject_name'].tolist()
                
                st.markdown(f"""
                To boost your score by 150 points, we need to focus on low-hanging fruit—turning your critical weaknesses into moderate strengths.
                
                **📈 Action Plan:**
                1. **Core Subject Boost**: Focus heavily on **{', '.join(weak_subs)}**. Currently, these are dragging down your predicted score. Target raising their accuracy to 65%.
                2. **Extend Coverage**: Increase your unique topic attempts (syllabus coverage) by **15%**. Broad syllabus familiarity beats narrow topic mastery in GATE.
                3. **Study Hours**: Increase your daily study target in the *Study Planner* by **1.0 Hour** for the next 14 days to accommodate these extra drills.
                """)
                
            elif coach_query == "Evaluate my study speed and solving consistency.":
                speed = real_features["avg_time_spent"]
                consistency = real_features["consistency"] * 100.0
                
                speed_eval = ""
                if speed > 130:
                    speed_eval = "⚠️ **Too Slow**: You average over 2 minutes per question. In the actual GATE exam, time limits are tight. Work on shortcuts and formula memorization."
                elif speed < 50:
                    speed_eval = "⚠️ **Too Fast / Rushed**: You solve questions in under 50 seconds. This is likely causing silly mistakes. Read the question statements twice before marking options."
                else:
                    speed_eval = "✅ **Optimal Pace**: Your speed is around 1.5 - 2 minutes. This is the perfect balance for reasoning and accuracy."
                    
                const_eval = ""
                if consistency >= 70:
                    const_eval = "🔥 **Excellent Consistency**: You are practicing almost daily. This active learning keeps neural pathways reinforced."
                elif consistency >= 40:
                    const_eval = "⏳ **Moderate Consistency**: You study regularly but have gaps of 2-3 days. Try to solve at least 5 questions even on busy days to keep your momentum."
                else:
                    const_eval = "❌ **Irregular Practice**: Your practice activity is highly sparse. Spaced repetition fails if reviews are missed. Make consistency your top priority."
                
                st.markdown(f"""
                Here is the evaluation of your operational performance:
                
                * **Solve Speed ({int(speed)} seconds/question)**:
                  {speed_eval}
                * **Practice Consistency ({consistency:.1f}% index)**:
                  {const_eval}
                """)
                
            elif coach_query == "Identify my top subject strengths and how to leverage them.":
                strongest = df_topics[df_topics['accuracy'] >= 0.70]
                if strongest.empty:
                    st.write("You don't have subjects with >70% accuracy yet. Keep studying and practicing to build your strength catalog!")
                else:
                    strongest_list = strongest.sort_values('accuracy', ascending=False).head(2)
                    st.markdown("Your primary strength areas are:")
                    for idx, row in strongest_list.iterrows():
                        st.markdown(f"✨ **{row['topic_name']}** ({row['subject_name']}) — **{row['accuracy']*100:.1f}% accuracy**")
                        
                    st.markdown("""
                    **💡 How to Leverage Strengths:**
                    * **Time Bank**: In mock exams, solve these questions first. Doing so builds immediate momentum and saves time for tougher sections.
                    * **Anchor Marks**: These topics represent your guaranteed marks. Ensure you solve standard GATE papers to check if you maintain this accuracy under pressure.
                    """)
