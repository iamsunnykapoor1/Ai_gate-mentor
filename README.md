# AI-Powered GATE Mentor 🤖🎯

AI-Powered GATE Mentor is a comprehensive, dashboard-driven preparation platform for GATE (Graduate Aptitude Test in Engineering) aspirants. It combines cognitive science, machine learning, and structured schedules to help students track syllabus coverage, identify critical weaknesses, schedule reviews using spaced repetition, and forecast their GATE scores and ranks.

This project is built entirely in **Python** using **Streamlit** for a premium glassmorphic UI, **SQLite** for local persistence, and **Scikit-Learn** for Random Forest regression predictions.

---

## 🚀 Key Features

1. **User Dashboard**: Real-time KPI metrics showing overall accuracy, questions solved, average solve speed, predicted GATE score, and estimated All India Rank (AIR).
2. **Topic Performance Tracking**: Breaks down subject-wise performance and segments topics into Weak, Moderate, and Strong bins.
3. **Adaptive Practice Workspace**: Filter questions by Subject, Topic, and Difficulty. Tracks solving speed, scores inputs instantly, and logs history with comprehensive solutions.
4. **Automated Study Planner**: Dynamically allocates daily study targets across weak subjects based on the user's daily hours availability.
5. **Spaced Repetition Scheduler**: Leverages the **SuperMemo SM-2 algorithm** to compute cognitive forgetting curves, prompting students for revisions precisely when they are due.
6. **Advanced AI Tools**:
   - **What-If Simulator**: Real-time score simulator sliders to test hypothetical preparation levels.
   - **Peer Benchmarking**: Compare your score against a distribution of 1,200 simulated peer profiles and view your percentile.
   - **Interactive AI Study Coach**: Get diagnostics on your bottlenecks, roadmap to score improvements, speed metrics, and strengths.

---

## 🛠️ Technology Stack

* **Frontend & Routing**: Streamlit (using new dynamic `st.navigation` API)
* **Styling**: Custom CSS (Vanilla CSS, Glassmorphic cards, Glowing borders, Google fonts)
* **Data Processing**: Pandas & NumPy
* **Visualizations**: Plotly (Radar, Gauge, Heatmaps, Timeline, Histograms, Bubble scatter plots)
* **Machine Learning**: Scikit-Learn (Random Forest Regressor)
* **Persistence**: SQLite (Local file `gate_mentor.db`)
* **Security**: Hashing passwords using `bcrypt`

---

## 📁 Directory Structure

```
AI-GATE-Mentor/
│
├── assets/                  # CSS styles
│   └── styles.css
│
├── data/                    # SQLite database and CSV files
│   ├── gate_mentor.db       # Created automatically
│   └── synthetic_peers.csv  # Created during training
│
├── database/                # Database configurations & migrations
│   ├── connection.py        # Connection wrappers
│   ├── schema.sql           # Schema definitions
│   └── seed.py              # Mock data seeder
│
├── models/                  # ML models & training
│   ├── train_models.py      # Model training script
│   ├── predictor.py         # Prediction wrappers
│   ├── gate_score_model.pkl # Trained Score model
│   └── gate_rank_model.pkl  # Trained Rank model
│
├── pages/                   # Streamlit subpages
│   ├── 1_Dashboard.py
│   ├── 2_Performance.py
│   ├── 3_Study_Planner.py
│   ├── 4_Revision.py
│   ├── 5_Practice.py
│   └── 6_Advanced_Tools.py
│
├── app.py                   # Main entry point (Login/Register)
├── requirements.txt         # Dependencies
└── README.md                # Documentation
```

---

## 💾 Database Schema

The database uses SQLite, containing 7 primary tables:
* `users`: Stores secure credentials (bcrypt hashed) and study limits.
* `subjects` & `topics`: Maps the GATE Computer Science syllabus hierarchy.
* `questions`: Multiple-choice practice questions with difficulty ratings and solutions.
* `user_attempts`: Logs single-question attempts, solve speeds, and correctness.
* `revision_schedule`: Tracks SM-2 spaced repetition stats (ease factor, repetitions, next due dates).
* `study_plans`: Holds daily hourly timetables.

---

## 🧠 Machine Learning Engine

The score prediction utilizes Scikit-Learn **Random Forest Regressors** trained on 1,200 synthetic peer records.
* **Score Predictor Features**: Total questions solved, accuracy, medium/hard accuracy, average speed, study consistency, and syllabus coverage.
* **Rank Predictor Features**: Simulated/predicted score. Matches historical curves mapping GATE scores to All India Ranks.
* **Accuracy Metrics**: Both regressors score highly on R² evaluation metrics ($R^2 > 0.97$).

---

## 💻 Local Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd AI-GATE-Mentor
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database & Seed Data**:
   This command creates the database tables, seeds standard GATE Computer Science subjects and topics, loads a sample pool of mock questions, and generates 30 days of active practice history for the default demo user.
   ```bash
   python database/seed.py
   ```

4. **Train Machine Learning Models**:
   Trains the Random Forest predictors and saves the serialized weights.
   ```bash
   python models/train_models.py
   ```

5. **Launch Application**:
   ```bash
   streamlit run app.py
   ```

6. **Login**:
   * Click **Login as Demo User** to explore with populated prep history immediately.
   * Or register a new account to track your progress from scratch.

---

## 🌐 Deployment to Streamlit Cloud

1. Push your repository to **GitHub**. Make sure `requirements.txt` is in the root directory.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and link your GitHub account.
3. Click **New App**, select your repository, branch, and set the entry file to `app.py`.
4. In the advanced settings of Streamlit deployment:
   * (Optional) Specify secrets or environment variables. No secrets are needed for this app since SQLite runs locally inside the container filesystem.
5. Click **Deploy**. Streamlit will install the dependencies and launch the site.
6. Once deployed, run the data seeder and model training from an initialization block or let the app run `init_db` automatically. (The app is programmed to run database initialization automatically on launch, and you can practice or register right away!).
