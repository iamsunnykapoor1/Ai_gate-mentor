import streamlit as st
import datetime
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from utils.planner import get_daily_plan, generate_daily_plan, update_plan_status
from utils.auth import update_user_profile

st.markdown("<h2 class='header-gradient'>📅 Daily Study Planner</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; margin-bottom: 25px;'>Analyze weaknesses and structure your study schedule into daily revision blocks.</p>", unsafe_allow_html=True)

user_id = st.session_state.user_id
today_str = datetime.date.today().strftime("%Y-%m-%d")

# 1. Expandable Settings Panel to modify study hours
with st.expander("⚙️ Adjust Study Preferences"):
    col_pref1, col_pref2 = st.columns(2)
    with col_pref1:
        new_target_year = st.selectbox(
            "Change Target GATE Year", 
            [2027, 2028, 2029], 
            index=[2027, 2028, 2029].index(st.session_state.target_gate_year)
        )
    with col_pref2:
        new_study_hours = st.slider(
            "Available Study Hours per Day", 
            1.0, 16.0, 
            float(st.session_state.daily_study_hours), 
            step=0.5
        )
        
    if st.button("Save Preferences"):
        success = update_user_profile(user_id, new_target_year, new_study_hours)
        if success:
            st.success("Preferences updated! Regenerating study schedules...")
            # Delete today's plan to force regenerate with new hours
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM study_plans WHERE user_id = ? AND date = ?", (user_id, today_str))
            conn.commit()
            conn.close()
            st.rerun()

# 2. Date Selection (allows browsing historical schedules)
col_date, col_action = st.columns([1.5, 2.5])
with col_date:
    selected_date = st.date_input("Select Plan Date", datetime.date.today())
    selected_date_str = selected_date.strftime("%Y-%m-%d")

with col_action:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # spacer
    # Force Regenerate Button (only for today or future dates)
    if selected_date >= datetime.date.today():
        if st.button("Regenerate Schedule 🔄"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM study_plans WHERE user_id = ? AND date = ?", (user_id, selected_date_str))
            conn.commit()
            conn.close()
            # Generate new
            generate_daily_plan(user_id, selected_date_str, st.session_state.daily_study_hours)
            st.success("Schedule regenerated!")
            st.rerun()

# 3. Load or Generate Plan
plan_items = generate_daily_plan(user_id, selected_date_str, st.session_state.daily_study_hours)

st.markdown("---")

# Render Study Plan Tasks
if not plan_items:
    st.info("No study tasks scheduled for this date.")
else:
    # Title and progress indicator
    total_items = len(plan_items)
    completed_items = sum(1 for item in plan_items if item['status'] == 'Completed')
    completion_rate = (completed_items / total_items) if total_items > 0 else 0.0
    
    st.markdown(f"### Today's Study Block Allocation")
    
    # Progress Bar
    progress_pct = int(completion_rate * 100)
    st.progress(completion_rate)
    st.markdown(f"<p style='color: #94A3B8; font-size: 0.9rem; margin-top: -10px;'>Completion Rate: <strong>{progress_pct}%</strong> ({completed_items} of {total_items} tasks done)</p>", unsafe_allow_html=True)

    # Render checklist cards
    for idx, item in enumerate(plan_items):
        topic_id = item['topic_id']
        allocated = item['allocated_minutes']
        status = item['status']
        
        # Display as a card
        card_class = "metric-card" + (" glowing-card-green" if status == 'Completed' else "")
        status_lbl = "✅ Completed" if status == 'Completed' else "⏳ Pending"
        
        st.markdown(f"""
        <div class="{card_class}" style="padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.8rem; color: #6366F1; font-weight: 600; text-transform: uppercase;">{item['subject_name']}</span>
                    <h5 style="margin: 4px 0 0 0; color: #F8FAFC;">{item['topic_name']}</h5>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #E2E8F0;">{allocated} mins</span><br>
                    <span style="font-size: 0.8rem; color: {'#34D399' if status == 'Completed' else '#F59E0B'}">{status_lbl}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Checkbox to toggle state
        checkbox_key = f"chk_{topic_id}_{selected_date_str}"
        is_checked = (status == 'Completed')
        
        new_val = st.checkbox(
            f"Mark '{item['topic_name']}' as completed", 
            value=is_checked, 
            key=checkbox_key, 
            label_visibility="collapsed"
        )
        
        # Update database if status toggled
        if new_val != is_checked:
            new_status = 'Completed' if new_val else 'Pending'
            update_plan_status(user_id, selected_date_str, topic_id, new_status)
            st.rerun()

# 4. Recommendation Engine Block
st.markdown("---")
st.markdown("### 💡 Recommended Next Steps")

col_rec1, col_rec2 = st.columns(2)

with col_rec1:
    st.markdown("<div class='metric-card' style='height: 250px;'>", unsafe_allow_html=True)
    st.markdown("<h4>📚 Subject Focus Recommendations</h4>", unsafe_allow_html=True)
    
    # Query topics with zero attempts or lowest accuracy that are not in today's study plan
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current plan topic IDs
    plan_topic_ids = [item['topic_id'] for item in plan_items]
    placeholders = ",".join("?" for _ in plan_topic_ids)
    
    query = """
        SELECT t.name as topic_name, s.name as subject_name
        FROM topics t
        JOIN subjects s ON t.subject_id = s.id
        LEFT JOIN questions q ON q.topic_id = t.id
        LEFT JOIN user_attempts a ON a.question_id = q.id AND a.user_id = ?
        WHERE 1=1
    """
    params = [user_id]
    if plan_topic_ids:
        query += f" AND t.id NOT IN ({placeholders})"
        params.extend(plan_topic_ids)
        
    query += """
        GROUP BY t.id, t.name, s.name
        ORDER BY AVG(a.is_correct) ASC, COUNT(a.id) ASC
        LIMIT 3
    """
    
    cursor.execute(query, params)
    rec_topics = cursor.fetchall()
    conn.close()
    
    if rec_topics:
        for idx, row in enumerate(rec_topics):
            st.markdown(f"**{idx+1}. {row['topic_name']}** ({row['subject_name']})")
            st.markdown("<p style='color: #64748B; font-size: 0.82rem; margin-top:-5px;'>Unattempted or critical low accuracy. Click practice to improve.</p>", unsafe_allow_html=True)
    else:
        st.write("You have successfully attempted all available subjects! Take a mock exam.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_rec2:
    st.markdown("<div class='metric-card' style='height: 250px;'>", unsafe_allow_html=True)
    st.markdown("<h4>📝 Recommended Practice Tests</h4>", unsafe_allow_html=True)
    
    # Simple recommendation rules
    if completion_rate >= 1.0:
        st.success("🎯 Daily study targets complete!")
        st.write("✨ **Subject Practice Test**: Operating Systems (Core concepts scheduler & paging).")
        st.write("✨ **GATE PYQ Mock**: Attempt the 2024 general CS questions to test overall recall.")
    else:
        st.write("✨ **Topic Practice**: Practice 5 questions in your weakest topic to boost your accuracy.")
        st.write("✨ **Speed Practice**: Solve 3 Easy difficulty questions to optimize solve-speed.")
        st.write("✨ **Memory Drill**: Complete your due revisions today to lock down learning.")
    st.markdown("</div>", unsafe_allow_html=True)
