import streamlit as st
import time
import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

st.markdown("<h2 class='header-gradient'>✍️ Practice Workspace</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; margin-bottom: 25px;'>Solve mock GATE questions, time your performance, and review answers with explanations.</p>", unsafe_allow_html=True)

# Initialize Session State variables for practicing
if "practice_q" not in st.session_state:
    st.session_state.practice_q = None
if "practice_start_time" not in st.session_state:
    st.session_state.practice_start_time = None
if "practice_submitted" not in st.session_state:
    st.session_state.practice_submitted = False
if "practice_feedback" not in st.session_state:
    st.session_state.practice_feedback = {}

# Fetch filters
def get_filter_options():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM subjects")
    subjects = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subjects

subjects = get_filter_options()

# Render Filters
col_filt1, col_filt2, col_filt3 = st.columns([1, 1, 1])

with col_filt1:
    selected_subject = st.selectbox("Choose Subject", ["All"] + subjects)

with col_filt2:
    # Fetch topics based on subject
    topics = []
    if selected_subject != "All":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.name FROM topics t 
            JOIN subjects s ON t.subject_id = s.id 
            WHERE s.name = ?
        """, (selected_subject,))
        topics = [row[0] for row in cursor.fetchall()]
        conn.close()
    selected_topic = st.selectbox("Choose Topic", ["All"] + topics)

with col_filt3:
    selected_diff = st.selectbox("Choose Difficulty", ["All", "Easy", "Medium", "Hard"])

# Reset current question if filters change
def reset_question():
    st.session_state.practice_q = None
    st.session_state.practice_start_time = None
    st.session_state.practice_submitted = False
    st.session_state.practice_feedback = {}
    st.session_state.pop("practice_answer", None)

# Button to load a new question
col_act1, col_act2 = st.columns([1, 4])
previous_question_id = st.session_state.pop("practice_previous_question_id", None)
with col_act1:
    if st.button("New Question 🔄", use_container_width=True):
        current_question = st.session_state.practice_q
        if isinstance(current_question, dict):
            previous_question_id = current_question["id"]
        reset_question()

# Fetch a question matching criteria
def fetch_matching_question(user_id, subject, topic, difficulty, exclude_question_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT q.*, t.name as topic_name, s.name as subject_name 
        FROM questions q
        JOIN topics t ON q.topic_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        WHERE 1=1
    """
    params = []
    
    if subject != "All":
        query += " AND s.name = ?"
        params.append(subject)
    if topic != "All" and topic != "":
        query += " AND t.name = ?"
        params.append(topic)
    if difficulty != "All":
        query += " AND q.difficulty = ?"
        params.append(difficulty)
    if exclude_question_id is not None:
        query += " AND q.id != ?"
        params.append(exclude_question_id)
        
    # Order by whether the user has attempted it or not (attempted last, unattempted first)
    query += """
        ORDER BY CASE WHEN q.id IN (
            SELECT question_id FROM user_attempts WHERE user_id = ?
        ) THEN 1 ELSE 0 END ASC, RANDOM() LIMIT 1
    """
    params.append(user_id)
    
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Load question if not loaded
if st.session_state.practice_q is None:
    q = fetch_matching_question(
        st.session_state.user_id,
        selected_subject,
        selected_topic,
        selected_diff,
        exclude_question_id=previous_question_id
    )
    if q is None and previous_question_id is not None:
        q = fetch_matching_question(st.session_state.user_id, selected_subject, selected_topic, selected_diff)
        if q and q["id"] == previous_question_id:
            st.info("This is the only question available for the selected filters.")

    if q:
        st.session_state.practice_q = q
        st.session_state.practice_start_time = time.time()
        st.session_state.practice_submitted = False
        st.session_state.practice_feedback = {}
    else:
        st.session_state.practice_q = "None Found"

# Display Question Panel
if st.session_state.practice_q == "None Found":
    st.warning("No questions found matching your filter criteria. Try relaxing the filters or choosing another subject.")
elif st.session_state.practice_q is not None:
    q = st.session_state.practice_q
    
    # Meta badges
    diff_badge = f"<span class='badge badge-{q['difficulty'].lower()}'>{q['difficulty']}</span>"
    st.markdown(f"""
    <div style='margin-bottom: 15px;'>
        <span style='color: #6366F1; font-weight: 600;'>{q['subject_name']}</span> &nbsp;•&nbsp; 
        <span style='color: #94A3B8;'>{q['topic_name']}</span> &nbsp;•&nbsp; 
        {diff_badge} &nbsp;•&nbsp;
        <span style='color: #F59E0B;'>{q['marks']} Mark(s)</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Question text panel
    st.markdown(f"""
    <div class='metric-card' style='background: rgba(30, 41, 59, 0.25); border-left: 4px solid #6366F1;'>
        <p style='font-size: 1.15rem; font-weight: 500; line-height: 1.6; white-space: pre-line;'>{q['question_text']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    options = {
        "A": q["option_a"],
        "B": q["option_b"],
        "C": q["option_c"],
        "D": q["option_d"]
    }
    
    # Checkbox select or radio buttons
    # In order to look premium, we can display them as a radio option but styled
    selected_option_key = st.radio(
        "Select your answer:", 
        options=["A", "B", "C", "D"], 
        format_func=lambda x: f"({x})  {options[x]}",
        disabled=st.session_state.practice_submitted,
        key="practice_answer"
    )
    
    # Action buttons
    col_sub1, col_sub2 = st.columns([1, 4])
    
    with col_sub1:
        if st.button("Submit Answer 🚀", disabled=st.session_state.practice_submitted, use_container_width=True):
            # Calculate elapsed time
            elapsed = int(time.time() - st.session_state.practice_start_time)
            elapsed = max(5, min(600, elapsed)) # clamp to reasonable 5s to 10mins
            
            is_correct = 1 if selected_option_key == q["correct_option"] else 0
            
            # Log attempt into database
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_attempts (user_id, question_id, selected_option, is_correct, time_spent_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (st.session_state.user_id, q["id"], selected_option_key, is_correct, elapsed))
            conn.commit()
            conn.close()
            
            # Set feedback states
            st.session_state.practice_submitted = True
            st.session_state.practice_feedback = {
                "is_correct": is_correct,
                "selected": selected_option_key,
                "correct_option": q["correct_option"],
                "explanation": q["explanation"],
                "time_taken": elapsed
            }
            st.rerun()

    # Show feedback
    if st.session_state.practice_submitted:
        feedback = st.session_state.practice_feedback
        if feedback["is_correct"]:
            st.markdown(f"""
            <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 10px; padding: 15px; margin-top: 20px;'>
                <h5 style='color: #34D399; margin: 0;'>🎉 Correct Answer!</h5>
                <p style='color: #E2E8F0; margin-top: 8px;'>You solved this in <strong>{feedback["time_taken"]} seconds</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; border-radius: 10px; padding: 15px; margin-top: 20px;'>
                <h5 style='color: #F87171; margin: 0;'>❌ Incorrect Answer</h5>
                <p style='color: #E2E8F0; margin-top: 8px;'>You selected <strong>({feedback["selected"]})</strong>. The correct option is <strong>({feedback["correct_option"]})</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Display explanation
        st.markdown(f"""
        <div class='metric-card' style='margin-top: 15px; background: rgba(255,255,255,0.02);'>
            <h6>📚 Solution Rationale:</h6>
            <p style='color: #94A3B8; font-size: 0.95rem; line-height: 1.6; margin-top: 8px;'>
                {feedback["explanation"]}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Next button
        if st.button("Load Next Question ➡️"):
            st.session_state.practice_previous_question_id = q["id"]
            reset_question()
            st.rerun()
