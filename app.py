import streamlit as st
import os
import sys

# Page configuration MUST be the very first Streamlit command
st.set_page_config(
    page_title="AI-Powered GATE Mentor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Append directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.auth import init_session_state, login_user, register_user, set_login_session, logout_user
from database.connection import init_db

# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize Session State
init_session_state()
load_css()

# Ensure Database is initialized on launch
@st.cache_resource
def run_db_initialization():
    init_db()
run_db_initialization()

# Render Authentication / Landing Screen if not logged in
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;' class='header-gradient'>🤖 AI-Powered GATE Mentor</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.15rem; margin-bottom: 40px;'>Your intelligent personalized study companion & score predictor for GATE preparation</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.markdown("""
        <div class='metric-card glowing-card' style='height: 100%;'>
            <h3>Accelerate Your GATE Preparation 🚀</h3>
            <p style='color: #E2E8F0; margin-top: 15px;'>
                AI-Powered GATE Mentor combines cognitive science, machine learning, and automation to streamline your engineering studies.
            </p>
            <div style='margin-top: 25px;'>
                <p><strong>🎯 Key Platform Capabilities:</strong></p>
                <ul style='color: #94A3B8; line-height: 1.8;'>
                    <li>📊 <strong>Interactive Readiness Tracker:</strong> Measure your subject-wise syllabus coverage and score probability.</li>
                    <li>🔮 <strong>ML Score & Rank Predictor:</strong> Real-time score forecasting trained on peer performance models.</li>
                    <li>🧠 <strong>Spaced Repetition Scheduler:</strong> Never forget a concept with memory-retention-based revision prompts.</li>
                    <li>📅 <strong>Dynamic Study Planner:</strong> Generate automated daily hourly schedules tailored to your weaknesses.</li>
                    <li>📝 <strong>Adaptive Practice Simulator:</strong> Solve subject-focused mock questions with detailed rationales.</li>
                </ul>
            </div>
            <div style='margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px;'>
                <p style='color: #64748B; font-size: 0.85rem;'>
                    💡 <strong>Quick Access:</strong> Click the <strong>"Login as Demo User"</strong> button on the right to immediately explore with loaded history.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔒 Secure Login", "📝 Create Account"])

        with tab_login:
            # Login Form
            login_user_input = st.text_input("Username or Email", placeholder="e.g. demo", key="login_username")
            login_pass_input = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("Sign In", use_container_width=True):
                    if not login_user_input or not login_pass_input:
                        st.error("Please enter both credentials.")
                    else:
                        user = login_user(login_user_input, login_pass_input)
                        if user:
                            set_login_session(user)
                            st.success(f"Welcome back, {user['username']}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
            
            with col_btn2:
                # Fast demo access
                if st.button("Login as Demo User 🚀", use_container_width=True):
                    # We login as 'demo' (password 'demo')
                    user = login_user("demo", "demo")
                    if user:
                        set_login_session(user)
                        st.success("Logged in as Demo User!")
                        st.rerun()
                    else:
                        st.error("Demo user is not seeded. Run data seeder first.")

        with tab_register:
            # Registration Form
            reg_username = st.text_input("Username", placeholder="e.g. gatenewbie", key="reg_username")
            reg_email = st.text_input("Email Address", placeholder="e.g. user@domain.com", key="reg_email")
            reg_password = st.text_input("Password", type="password", placeholder="Minimum 6 characters", key="reg_password")
            reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="reg_confirm")
            
            col_reg1, col_reg2 = st.columns([1, 1])
            with col_reg1:
                target_year = st.selectbox("Target GATE Year", [2027, 2028, 2029], index=0)
            with col_reg2:
                study_hours = st.slider("Daily Study Hours Available", 1.0, 16.0, 4.0, step=0.5)

            if st.button("Create My Account", use_container_width=True):
                if not reg_username or not reg_email or not reg_password:
                    st.error("All fields are required.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    success = register_user(reg_username, reg_email, reg_password, target_year, study_hours)
                    if success:
                        st.success("Account created successfully! Please Sign In.")
                    else:
                        st.error("Username or email already registered.")

        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Define multi-page setup using st.Page and st.navigation (Streamlit >= 1.35)
    dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊", default=True)
    performance_page = st.Page("pages/2_Performance.py", title="Performance Analytics", icon="📈")
    advanced_page = st.Page("pages/6_Advanced_Tools.py", title="Advanced AI Tools", icon="🔮")
    planner_page = st.Page("pages/3_Study_Planner.py", title="Study Planner", icon="📅")
    revision_page = st.Page("pages/4_Revision.py", title="Revision Scheduler", icon="⏰")
    practice_page = st.Page("pages/5_Practice.py", title="Practice Workspace", icon="✍️")

    # Define Navigation
    pg = st.navigation({
        "Dashboard & Stats": [dashboard_page, performance_page, advanced_page],
        "Preparation Engine": [practice_page, planner_page, revision_page]
    })

    # Sidebar Header
    st.sidebar.markdown(f"### Welcome, **{st.session_state.username}** 👋")
    st.sidebar.markdown(f"🎯 **Target**: GATE {st.session_state.target_gate_year}")
    st.sidebar.markdown(f"⏱️ **Daily Study Limit**: {st.session_state.daily_study_hours} Hrs")
    st.sidebar.markdown("---")

    # Run current page
    pg.run()

    # Sidebar Footer Logout
    if st.sidebar.button("Logout 🚪", use_container_width=True):
        logout_user()
