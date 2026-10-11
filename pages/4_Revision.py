import streamlit as st
import pandas as pd
import datetime
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from utils.scheduler import get_due_revisions, schedule_topic_revision

st.markdown("<h2 class='header-gradient'>⏰ Spaced Repetition Revision</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; margin-bottom: 25px;'>Retain concepts forever using cognitive spaced repetition (SM-2 algorithm).</p>", unsafe_allow_html=True)

user_id = st.session_state.user_id
due_items = get_due_revisions(user_id)

col1, col2 = st.columns([0.6, 0.4])

with col1:
    st.markdown("### Due Revisions Today")
    
    if not due_items:
        st.markdown("""
        <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 12px; padding: 24px; text-align: center;'>
            <h4 style='color: #34D399;'>🎉 Memory Retention Solid!</h4>
            <p style='color: #E2E8F0; margin-top: 10px; font-size: 0.95rem;'>
                You have no topics due for revision today. Your spaced reviews are fully up to date.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"You have {len(due_items)} topics due for active recall review today.")
        
        # Render the first due topic for focused revision (one at a time is cleaner!)
        focused_item = due_items[0]
        topic_id = focused_item['topic_id']
        topic_name = focused_item['topic_name']
        subject_name = focused_item['subject_name']
        reps = focused_item['repetitions']
        
        st.markdown(f"""
        <div class="metric-card glowing-card" style="padding: 24px; margin-bottom: 20px;">
            <span style="font-size: 0.8rem; color: #818CF8; font-weight: 600; text-transform: uppercase;">{subject_name}</span>
            <h3 style="margin: 8px 0 15px 0; color: #F8FAFC;">{topic_name}</h3>
            <p style="color: #94A3B8; font-size: 0.9rem;">
                Current repetitions streak: <strong>{reps}</strong> | Ease Factor: <strong>{focused_item['ease_factor']:.2f}</strong>
            </p>
            <div style="background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; border-left: 3px solid #6366F1; margin-top: 15px;">
                💡 <strong>Recall Drill:</strong> Close your eyes and try to explain this topic's key concepts (e.g. definitions, algorithms, formulas) to yourself. Once done, rate your recall below.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Familiarity rating
        rating = st.select_slider(
            "Rate your recall confidence:",
            options=[0, 1, 2, 3, 4, 5],
            format_func=lambda x: {
                0: "0 - Total Blackout (Forgot completely)",
                1: "1 - Incorrect (Felt slightly familiar)",
                2: "2 - Incorrect (Recalled easily after brief look)",
                3: "3 - Correct (Recalled with serious difficulty)",
                4: "4 - Correct (Recalled after a short hesitation)",
                5: "5 - Perfect (Immediate, effortless recall)"
            }[x]
        )
        
        if st.button("Submit Review & Reschedule ⏰"):
            interval, next_date = schedule_topic_revision(user_id, topic_id, rating)
            st.success(f"Review logged! Topic rescheduled in **{interval} days** (Next review: {next_date})")
            st.rerun()

with col2:
    st.markdown("### 🧠 The SM-2 Algorithm")
    st.markdown("""
    <div class='metric-card' style='font-size: 0.9rem; line-height: 1.6; background: rgba(15, 23, 42, 0.4);'>
        <p>This system utilizes the <strong>SuperMemo-2 (SM-2) algorithm</strong> to calculate optimal intervals for reviews.</p>
        <p><strong>How it works:</strong></p>
        <ul style='color: #94A3B8; padding-left: 15px;'>
            <li>Ratings <strong>&lt; 3</strong> reset the revision interval to 1 day.</li>
            <li>Correct ratings (<strong>&ge; 3</strong>) increase the intervals exponentially:
                <br><em>Interval = 1 -> 6 -> (Interval * Ease Factor)</em>
            </li>
            <li>The <strong>Ease Factor</strong> is dynamically modified based on your performance to model your custom forgetting curve.</li>
        </ul>
        <p style='color: #64748B; font-size: 0.8rem; margin-top: 15px;'>
            Using spaced repetition ensures you move concepts from short-term to permanent long-term memory with minimal study hours.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Bottom section: List of all scheduled cards
st.markdown("---")
st.markdown("### 🗂️ Memory Deck Overview")

conn = get_connection()
df_deck = pd.read_sql_query("""
    SELECT 
        t.name as topic_name,
        s.name as subject_name,
        r.ease_factor,
        r.interval_days,
        r.repetitions,
        r.next_revision_date
    FROM revision_schedule r
    JOIN topics t ON r.topic_id = t.id
    JOIN subjects s ON t.subject_id = s.id
    WHERE r.user_id = ?
    ORDER BY r.next_revision_date ASC
""", conn, params=(user_id,))
conn.close()

if df_deck.empty:
    st.info("No topics have been scheduled for revision yet. Start review drills by checking tasks off your Study Planner.")
else:
    # Format columns
    df_deck['ease_factor'] = df_deck['ease_factor'].map(lambda x: f"{x:.2f}")
    df_deck['interval_days'] = df_deck['interval_days'].map(lambda x: f"{x} days")
    
    df_deck.columns = ["Topic", "Subject", "Ease Factor", "Review Interval", "Repetitions", "Next Due Date"]
    st.dataframe(df_deck, use_container_width=True)
