import sqlite3
import random
import datetime
import bcrypt
import os
import sys

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection, init_db

# Subjects and Topics mapping for GATE CS
SYLLABUS = {
    "Engineering Mathematics": ["Linear Algebra", "Calculus", "Probability & Statistics"],
    "Discrete Mathematics": ["Propositional Logic", "Sets, Relations, Functions", "Combinatorics", "Graph Theory"],
    "Digital Logic": ["Boolean Algebra", "Combinational Circuits", "Sequential Circuits"],
    "Computer Organization and Architecture": ["Instruction Pipelining", "Memory Hierarchy", "Cache Mapping"],
    "Programming and Data Structures": ["Arrays, Stacks, Queues", "Trees & Binary Search Trees", "Recursion in C"],
    "Algorithms": ["Sorting and Searching", "Greedy & Dynamic Programming", "Graph Algorithms"],
    "Theory of Computation": ["Finite Automata & Regular Expressions", "Context Free Grammars & Pushdown Automata", "Turing Machines & Undecidability"],
    "Compiler Design": ["Lexical Analysis", "LL/LR Parsing", "Intermediate Code Generation"],
    "Operating System": ["CPU Scheduling", "Deadlocks & Semaphores", "Virtual Memory & Paging"],
    "Databases": ["ER Diagrams & Relational Model", "SQL Queries", "Normalization & Normal Forms"],
    "Computer Networks": ["IP Addressing & Subnetting", "TCP/UDP Congestion Control", "Application Layer Protocols"],
    "General Aptitude": ["Quantitative Aptitude", "Logical Reasoning", "Verbal Ability"]
}

# Rich pool of sample questions
SAMPLE_QUESTIONS = [
    # Operating System
    {
        "subject": "Operating System",
        "topic": "CPU Scheduling",
        "question_text": "Consider three processes P1, P2, and P3 with arrival times 0, 1, and 2, and burst times 5, 2, and 4 respectively. If we use Preemptive Shortest Remaining Time First (SRTF) scheduling, what is the average waiting time of the processes?",
        "option_a": "1.67 ms",
        "option_b": "2.33 ms",
        "option_c": "2.00 ms",
        "option_d": "2.67 ms",
        "correct_option": "B",
        "explanation": "At time 0, P1 arrives with burst 5. At time 1, P2 arrives with burst 2. Remaining time of P1 is 4. P2's burst (2) is less than P1's remaining (4), so P2 preempts P1. P2 runs from 1 to 3 and finishes. At time 3, remaining times are: P1 (4), P3 (4). P1 runs from 3 to 7. P3 runs from 7 to 11. Waiting times: P2 = 0, P1 = 3 - 1 = 2, P3 = 7 - 2 = 5. Average waiting time = (2 + 0 + 5) / 3 = 7/3 = 2.33 ms.",
        "difficulty": "Medium",
        "marks": 2
    },
    {
        "subject": "Operating System",
        "topic": "Virtual Memory & Paging",
        "question_text": "A system uses 32-bit virtual addresses, 4 KB page size, and 4-byte page table entries (PTE). If a single-level page table is used, what is the total size of the page table?",
        "option_a": "1 MB",
        "option_b": "2 MB",
        "option_c": "4 MB",
        "option_d": "8 MB",
        "correct_option": "C",
        "explanation": "Page size = 4 KB = 2^12 bytes. Number of pages = 2^32 / 2^12 = 2^20. Each page table entry takes 4 bytes. Total page table size = 2^20 * 4 bytes = 4 MB.",
        "difficulty": "Easy",
        "marks": 1
    },
    {
        "subject": "Operating System",
        "topic": "Deadlocks & Semaphores",
        "question_text": "Consider a system with 3 processes and 4 resources of the same type. Each process requires at most 2 resources. Can a deadlock occur in this system?",
        "option_a": "Yes, always",
        "option_b": "No, deadlock is impossible",
        "option_c": "Yes, if they request resources concurrently",
        "option_d": "Cannot be determined",
        "correct_option": "B",
        "explanation": "For N processes and R resources, if each process needs at most M resources, deadlock is impossible if R >= N * (M - 1) + 1. Here, N=3, M=2, so 3 * (2 - 1) + 1 = 4. Since R = 4 >= 4, deadlock is impossible.",
        "difficulty": "Easy",
        "marks": 1
    },
    # Databases
    {
        "subject": "Databases",
        "topic": "Normalization & Normal Forms",
        "question_text": "A relation R(A, B, C, D, E) has the following functional dependencies: A -> BC, CD -> E, B -> D, E -> A. What are the candidate keys of the relation R?",
        "option_a": "{A}, {E}",
        "option_b": "{A}, {E}, {BC}",
        "option_c": "{A}, {E}, {BC}, {CD}",
        "option_d": "{A}, {E}, {CD}",
        "correct_option": "C",
        "explanation": "Let's check closures: A+ = {A,B,C,D,E}. E+ = {E,A,B,C,D}. CD+ = {C,D,E,A,B}. BC+ = {B,C,D,E,A}. Thus, all four ({A}, {E}, {BC}, {CD}) can determine all attributes of R, making them candidate keys.",
        "difficulty": "Hard",
        "marks": 2
    },
    {
        "subject": "Databases",
        "topic": "SQL Queries",
        "question_text": "Which of the following relational algebra expressions is equivalent to the SQL query: SELECT DISTINCT name FROM student WHERE age > 20?",
        "option_a": "Project_name ( Select_age > 20 ( student ) )",
        "option_b": "Select_age > 20 ( Project_name ( student ) )",
        "option_c": "Project_age ( Select_name > 20 ( student ) )",
        "option_d": "Select_name ( Project_age > 20 ( student ) )",
        "correct_option": "A",
        "explanation": "The SELECT clause corresponds to Projection (Project) and the WHERE clause corresponds to Selection (Select). We select students with age > 20 first, then project their names.",
        "difficulty": "Easy",
        "marks": 1
    },
    # Theory of Computation
    {
        "subject": "Theory of Computation",
        "topic": "Finite Automata & Regular Expressions",
        "question_text": "What is the minimum number of states in a Deterministic Finite Automaton (DFA) that accepts the language L over alphabet {0, 1} consisting of all strings containing '001' as a substring?",
        "option_a": "3",
        "option_b": "4",
        "option_c": "5",
        "option_d": "6",
        "correct_option": "B",
        "explanation": "The states represent the prefixes of the target substring '001' we have seen: State 0 (start state, seen nothing), State 1 (seen '0'), State 2 (seen '00'), State 3 (seen '001', trap/accepting state). Thus, 4 states are required.",
        "difficulty": "Easy",
        "marks": 1
    },
    {
        "subject": "Theory of Computation",
        "topic": "Turing Machines & Undecidability",
        "question_text": "Which of the following problems is decidable?",
        "option_a": "Checking if a Turing Machine halts on a blank input",
        "option_b": "Checking if the language of a Context-Free Grammar is empty",
        "option_c": "Checking if the languages of two CFGs are equal",
        "option_d": "Checking if a Turing Machine accepts a regular language",
        "correct_option": "B",
        "explanation": "Emptiness of Context-Free Languages is decidable (using algorithms to check if start symbol can derive any terminal string). The halting problem, equivalence of CFGs, and checking if TM accepts a regular language are all undecidable.",
        "difficulty": "Hard",
        "marks": 2
    },
    # Programming and Data Structures
    {
        "subject": "Programming and Data Structures",
        "topic": "Recursion in C",
        "question_text": "Consider the following recursive C function. What does foo(5) return?\n\nint foo(int n) {\n    if (n <= 1) return 1;\n    return n * foo(n - 2) + foo(n - 1);\n}",
        "option_a": "120",
        "option_b": "76",
        "option_c": "94",
        "option_d": "86",
        "correct_option": "D",
        "explanation": "foo(1) = 1. foo(2) = 2*foo(0) + foo(1) = 2*1 + 1 = 3 (since foo(0)=1). foo(3) = 3*foo(1) + foo(2) = 3*1 + 3 = 6. foo(4) = 4*foo(2) + foo(3) = 4*3 + 6 = 18. foo(5) = 5*foo(3) + foo(4) = 5*6 + 18 = 48? Wait, let's recompute:\nfoo(0)=1, foo(1)=1.\nfoo(2) = 2*foo(0) + foo(1) = 2*1 + 1 = 3.\nfoo(3) = 3*foo(1) + foo(2) = 3*1 + 3 = 6.\nfoo(4) = 4*foo(2) + foo(3) = 4*3 + 6 = 18.\nfoo(5) = 5*foo(3) + foo(4) = 5*6 + 18 = 48. Ah! Let's check: 5 * foo(3) + foo(4) = 5 * 6 + 18 = 48. Let's make sure the option lists 48 or adjust the function. Let's change option_c to 48 and make it correct! Or wait, let's set options: A: 32, B: 48, C: 64, D: 86. Correct: B.",
        "option_a": "32",
        "option_b": "48",
        "option_c": "64",
        "option_d": "86",
        "correct_option": "B",
        "explanation": "Unfolding the recursion:\nfoo(0) = 1, foo(1) = 1.\nfoo(2) = 2 * foo(0) + foo(1) = 2 * 1 + 1 = 3.\nfoo(3) = 3 * foo(1) + foo(2) = 3 * 1 + 3 = 6.\nfoo(4) = 4 * foo(2) + foo(3) = 4 * 3 + 6 = 18.\nfoo(5) = 5 * foo(3) + foo(4) = 5 * 6 + 18 = 48.",
        "difficulty": "Medium",
        "marks": 2
    },
    {
        "subject": "Programming and Data Structures",
        "topic": "Trees & Binary Search Trees",
        "question_text": "What is the worst-case time complexity of searching an element in a Binary Search Tree (BST) of size N?",
        "option_a": "O(1)",
        "option_b": "O(log N)",
        "option_c": "O(N)",
        "option_d": "O(N log N)",
        "correct_option": "C",
        "explanation": "In the worst case, a BST can be skewed (like a linked list), leading to a search traversal of all elements, which takes O(N) time.",
        "difficulty": "Easy",
        "marks": 1
    },
    # Algorithms
    {
        "subject": "Algorithms",
        "topic": "Greedy & Dynamic Programming",
        "question_text": "Consider the fractional knapsack problem with capacity W=50 and 3 items: I1 (val=60, wt=10), I2 (val=100, wt=20), I3 (val=120, wt=30). What is the maximum value we can obtain?",
        "option_a": "220",
        "option_b": "240",
        "option_c": "260",
        "option_d": "280",
        "correct_option": "B",
        "explanation": "Calculate value/weight ratio: I1 = 6, I2 = 5, I3 = 4. Sort by ratio: I1, I2, I3. Take all of I1 (wt=10, val=60), all of I2 (wt=20, val=100). Remaining capacity = 20. Take 20/30 fraction of I3 (wt=20, val=80). Total value = 60 + 100 + 80 = 240.",
        "difficulty": "Medium",
        "marks": 2
    },
    {
        "subject": "Algorithms",
        "topic": "Graph Algorithms",
        "question_text": "If we run Dijkstra's single source shortest path algorithm on a graph with negative edge weights but no negative cycles, does it always find the correct shortest path?",
        "option_a": "Yes, always",
        "option_b": "No, it may fail",
        "option_c": "Yes, if the graph is a DAG",
        "option_d": "Yes, if we add a positive constant to all weights",
        "correct_option": "B",
        "explanation": "Dijkstra's algorithm assumes that once a vertex is visited/closed, its shortest path is finalized. This assumption fails when negative edge weights are present, even if there are no negative cycles. Hence, it may fail.",
        "difficulty": "Medium",
        "marks": 1
    },
    # Computer Networks
    {
        "subject": "Computer Networks",
        "topic": "IP Addressing & Subnetting",
        "question_text": "An organization has been allocated a Classless Inter-Domain Routing (CIDR) block of 192.168.10.0/24. If they need to divide this block into 4 equal-sized subnets, what is the subnet mask and the range of the second subnet?",
        "option_a": "Subnet Mask: 255.255.255.192, Range: 192.168.10.64 to 192.168.10.127",
        "option_b": "Subnet Mask: 255.255.255.128, Range: 192.168.10.64 to 192.168.10.127",
        "option_c": "Subnet Mask: 255.255.255.192, Range: 192.168.10.32 to 192.168.10.63",
        "option_d": "Subnet Mask: 255.255.255.240, Range: 192.168.10.64 to 192.168.10.95",
        "correct_option": "A",
        "explanation": "To divide a /24 block into 4 subnets, we need log2(4) = 2 bits. The new prefix is /26. A /26 subnet mask is 255.255.255.192. The size of each subnet is 2^(32-26) = 64 addresses. Subnet 0: .0 to .63. Subnet 1: .64 to .127. Subnet 2: .128 to .191. Subnet 3: .192 to .255. Thus, subnet mask is 255.255.255.192, and the second subnet range is 192.168.10.64 to 192.168.10.127.",
        "difficulty": "Hard",
        "marks": 2
    },
    # Digital Logic
    {
        "subject": "Digital Logic",
        "topic": "Combinational Circuits",
        "question_text": "How many 2-to-1 Multiplexers are needed to implement a 4-to-1 Multiplexer?",
        "option_a": "1",
        "option_b": "2",
        "option_c": "3",
        "option_d": "4",
        "correct_option": "C",
        "explanation": "To construct a 4-to-1 MUX, we use 2 MUXes in the first stage to select between inputs (I0, I1) and (I2, I3), and then 1 MUX in the second stage to choose between the outputs of the first stage. Total = 3.",
        "difficulty": "Easy",
        "marks": 1
    },
    # Computer Organization and Architecture
    {
        "subject": "Computer Organization and Architecture",
        "topic": "Instruction Pipelining",
        "question_text": "A 5-stage pipeline has stage delays of 10, 12, 15, 11, and 8 ns respectively. If the pipeline register delay is 2 ns, what is the cycle time of this pipeline?",
        "option_a": "15 ns",
        "option_b": "17 ns",
        "option_c": "12 ns",
        "option_d": "14 ns",
        "correct_option": "B",
        "explanation": "The clock cycle time of a pipeline is determined by the maximum delay of any stage plus the pipeline register delay. Clock cycle time = max(10, 12, 15, 11, 8) + 2 = 15 + 2 = 17 ns.",
        "difficulty": "Easy",
        "marks": 1
    },
    # Compiler Design
    {
        "subject": "Compiler Design",
        "topic": "Lexical Analysis",
        "question_text": "Which of the following compiler phases is responsible for generating token streams from source code and checking for basic spelling errors in identifiers?",
        "option_a": "Syntax Analysis",
        "option_b": "Semantic Analysis",
        "option_c": "Lexical Analysis",
        "option_d": "Code Generation",
        "correct_option": "C",
        "explanation": "Lexical analysis (scanner) reads the input characters and groups them into meaningful sequences called lexemes, producing a stream of tokens. It reports lexical errors such as invalid characters.",
        "difficulty": "Easy",
        "marks": 1
    },
    # General Aptitude
    {
        "subject": "General Aptitude",
        "topic": "Quantitative Aptitude",
        "question_text": "A train passes a standing man in 6 seconds and a 150-meter-long platform in 15 seconds. What is the speed of the train?",
        "option_a": "50 km/h",
        "option_b": "60 km/h",
        "option_c": "72 km/h",
        "option_d": "80 km/h",
        "correct_option": "B",
        "explanation": "Let speed be V m/s, train length be L meters. L = 6V. Train passes platform: L + 150 = 15V. Substitute L: 6V + 150 = 15V => 9V = 150 => V = 150/9 = 50/3 m/s. Convert to km/h: (50/3) * (18/5) = 60 km/h.",
        "difficulty": "Medium",
        "marks": 1
    },
    {
        "subject": "General Aptitude",
        "topic": "Quantitative Aptitude",
        "question_text": "A number is increased by 20% and then decreased by 20%. What is the net percentage change?",
        "option_a": "No change",
        "option_b": "4% decrease",
        "option_c": "4% increase",
        "option_d": "2% decrease",
        "correct_option": "B",
        "explanation": "Starting from 100, a 20% increase gives 120. Decreasing 120 by 20% gives 96, which is 4% less than the original 100.",
        "difficulty": "Easy",
        "marks": 1
    },
    {
        "subject": "General Aptitude",
        "topic": "Quantitative Aptitude",
        "question_text": "The average of five consecutive integers is 18. What is the largest integer?",
        "option_a": "18",
        "option_b": "19",
        "option_c": "20",
        "option_d": "21",
        "correct_option": "C",
        "explanation": "For five consecutive integers, the average is the middle integer. The integers are 16, 17, 18, 19, and 20, so the largest is 20.",
        "difficulty": "Easy",
        "marks": 1
    },
    {
        "subject": "General Aptitude",
        "topic": "Logical Reasoning",
        "question_text": "If all roses are flowers and some flowers fade quickly, which conclusion must be true?",
        "option_a": "All roses fade quickly",
        "option_b": "Some roses fade quickly",
        "option_c": "All roses are flowers",
        "option_d": "No flowers are roses",
        "correct_option": "C",
        "explanation": "The first statement directly says that all roses are flowers. The statement about some flowers fading does not establish whether those flowers include any roses.",
        "difficulty": "Easy",
        "marks": 1
    },
    {
        "subject": "General Aptitude",
        "topic": "Logical Reasoning",
        "question_text": "Find the next number in the sequence: 2, 6, 12, 20, 30, __.",
        "option_a": "36",
        "option_b": "40",
        "option_c": "42",
        "option_d": "44",
        "correct_option": "C",
        "explanation": "The successive differences are 4, 6, 8, and 10. The next difference is 12, so the next term is 30 + 12 = 42.",
        "difficulty": "Easy",
        "marks": 1
    },
    {
        "subject": "General Aptitude",
        "topic": "Verbal Ability",
        "question_text": "Choose the word closest in meaning to 'concise'.",
        "option_a": "Brief",
        "option_b": "Unclear",
        "option_c": "Detailed",
        "option_d": "Repeated",
        "correct_option": "A",
        "explanation": "'Concise' means giving information clearly in few words; its closest meaning here is 'brief'.",
        "difficulty": "Easy",
        "marks": 1
    },
    {
        "subject": "General Aptitude",
        "topic": "Verbal Ability",
        "question_text": "Choose the grammatically correct sentence.",
        "option_a": "Neither of the answers are correct.",
        "option_b": "Neither of the answers is correct.",
        "option_c": "Neither answers is correct.",
        "option_d": "Neither of answers are correct.",
        "correct_option": "B",
        "explanation": "'Neither' is singular in this construction, so it takes the singular verb 'is'.",
        "difficulty": "Easy",
        "marks": 1
    }
]


def seed_data(reset_demo_history=True, seed_demo_history=True):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Seed Subjects & Topics
        subject_ids = {}
        topic_ids = {}
        for subject_name, topics in SYLLABUS.items():
            cursor.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject_name,))
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
            sub_id = cursor.fetchone()[0]
            subject_ids[subject_name] = sub_id

            for topic_name in topics:
                cursor.execute("INSERT OR IGNORE INTO topics (subject_id, name) VALUES (?, ?)", (sub_id, topic_name))
                cursor.execute("SELECT id FROM topics WHERE subject_id = ? AND name = ?", (sub_id, topic_name))
                top_id = cursor.fetchone()[0]
                topic_ids[(subject_name, topic_name)] = top_id

        # 2. Seed Questions
        for q in SAMPLE_QUESTIONS:
            t_id = topic_ids.get((q["subject"], q["topic"]))
            if t_id:
                cursor.execute(
                    "SELECT 1 FROM questions WHERE topic_id = ? AND question_text = ?",
                    (t_id, q["question_text"])
                )
                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO questions
                        (topic_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, difficulty, marks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (t_id, q["question_text"], q["option_a"], q["option_b"], q["option_c"], q["option_d"],
                          q["correct_option"], q["explanation"], q["difficulty"], q["marks"]))

        # 3. Create Demo User
        # Check if already exists
        cursor.execute("SELECT id FROM users WHERE username = 'demo'")
        user_row = cursor.fetchone()
        if not user_row:
            password = "demo"
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, target_gate_year, daily_study_hours)
                VALUES (?, ?, ?, ?, ?)
            """, ("demo", "demo@example.com", hashed, 2027, 5.0))
            cursor.execute("SELECT id FROM users WHERE username = 'demo'")
            user_id = cursor.fetchone()[0]
            print(f"Created demo user with ID: {user_id}")
        else:
            user_id = user_row[0]
            print(f"Demo user already exists with ID: {user_id}")

        if not seed_demo_history:
            conn.commit()
            print("Data seeded successfully!")
            return

        if reset_demo_history:
            cursor.execute("DELETE FROM user_attempts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM revision_schedule WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM study_plans WHERE user_id = ?", (user_id,))

        # 4. Seed Synthetic Attempt Logs for the Demo User
        # Define success rates per subject to establish strengths and weaknesses.
        subject_performance = {
            "Theory of Computation": 0.35,
            "Compiler Design": 0.40,
            "Computer Organization and Architecture": 0.50,
            "Computer Networks": 0.55,
            "Engineering Mathematics": 0.60,
            "Discrete Mathematics": 0.65,
            "General Aptitude": 0.85,
            "Programming and Data Structures": 0.70,
            "Algorithms": 0.65,
            "Digital Logic": 0.75,
            "Operating System": 0.82,
            "Databases": 0.88
        }

        # Select all inserted questions.
        cursor.execute("SELECT q.id, q.topic_id, t.name as topic_name, s.name as subject_name FROM questions q JOIN topics t ON q.topic_id = t.id JOIN subjects s ON t.subject_id = s.id")
        questions_db = [dict(row) for row in cursor.fetchall()]

        today = datetime.datetime.now()
        if questions_db:
            start_date = today - datetime.timedelta(days=30)

            # Generate 180 attempts.
            for i in range(180):
                q = random.choice(questions_db)
                sub_name = q["subject_name"]
                pass_rate = subject_performance.get(sub_name, 0.6)
                is_correct = 1 if random.random() < pass_rate else 0

                cursor.execute("SELECT correct_option FROM questions WHERE id = ?", (q["id"],))
                correct_opt = cursor.fetchone()[0]
                if is_correct:
                    selected_option = correct_opt
                else:
                    wrong_options = [opt for opt in ["A", "B", "C", "D"] if opt != correct_opt]
                    selected_option = random.choice(wrong_options)

                time_spent = random.randint(30, 180)
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                mins_ago = random.randint(0, 59)
                attempt_time = start_date + datetime.timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)

                cursor.execute("""
                    INSERT INTO user_attempts (user_id, question_id, selected_option, is_correct, time_spent_seconds, attempted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, q["id"], selected_option, is_correct, time_spent, attempt_time.strftime("%Y-%m-%d %H:%M:%S")))

        # 5. Populate Revision Schedules (Spaced Repetition)
        cursor.execute("SELECT id FROM topics")
        topic_rows = cursor.fetchall()
        for r in topic_rows[:8]:
            t_id = r[0]
            days_offset = random.choice([-2, -1, 0, 1, 2, 4, 8])
            next_rev = (today + datetime.timedelta(days=days_offset)).strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT OR IGNORE INTO revision_schedule (user_id, topic_id, ease_factor, interval_days, repetitions, next_revision_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, t_id, random.uniform(1.8, 2.8), random.randint(1, 10), random.randint(1, 4), next_rev))

        # 6. Populate Study Plans for the next few days
        for offset in range(-2, 3):
            plan_date = (today + datetime.timedelta(days=offset)).strftime("%Y-%m-%d")
            selected_topics = random.sample(topic_rows, 2)
            for t in selected_topics:
                t_id = t[0]
                status = "Completed" if offset < 0 else ("Completed" if offset == 0 and random.random() > 0.5 else "Pending")
                cursor.execute("""
                    INSERT OR IGNORE INTO study_plans (user_id, date, topic_id, allocated_minutes, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, plan_date, t_id, random.choice([60, 90, 120]), status))

        conn.commit()
        print("Data seeded successfully!")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize DB schema first
    init_db()
    seed_data()
