# =====================================================
# AI SCHOLARSHIP FINDER — BACKEND API (app.py)
# Flask REST API Server + SQLite Database
# Integrates 2-Tier Architecture:
# - Deterministic Hard Eligibility Engine
# - Content-Based AI Feature Vector Recommender
# - Personalized AI Explanation Generator
# - Admin Scholarship Management Subsystem
# =====================================================

from flask import Flask, jsonify, request
import sqlite3
import os
from flask_cors import CORS

from eligibility_engine import evaluate_eligibility
from recommender import calculate_recommendation_score, rank_recommendations
from ai_explanation import generate_ai_explanation
from evaluator import evaluate_system

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "scholarship.db")
ADMIN_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "admin123")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    # ----- Create/Upgrade "students" table -----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            education TEXT NOT NULL,
            marks REAL NOT NULL,
            academic_score_type TEXT DEFAULT 'Percentage',
            academic_score REAL,
            obtained_marks REAL,
            max_marks REAL,
            family_income REAL NOT NULL,
            state TEXT NOT NULL,
            category TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            course TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe Schema migration helper for students table
    cursor.execute("PRAGMA table_info(students)")
    student_columns = [row[1] for row in cursor.fetchall()]

    student_extra_cols = [
        ("age", "INTEGER"),
        ("gender", "TEXT"),
        ("course", "TEXT"),
        ("academic_score_type", "TEXT DEFAULT 'Percentage'"),
        ("academic_score", "REAL"),
        ("obtained_marks", "REAL"),
        ("max_marks", "REAL")
    ]

    for col_name, col_type in student_extra_cols:
        if col_name not in student_columns:
            try:
                cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

    # ----- Create/Upgrade "scholarships" table -----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            description TEXT,
            amount REAL,
            minimum_marks REAL,
            academic_requirement_type TEXT DEFAULT 'Percentage',
            minimum_academic_score REAL,
            maximum_income REAL,
            education TEXT,
            state TEXT,
            category TEXT,
            course TEXT DEFAULT 'All',
            gender TEXT DEFAULT 'All',
            age_limit INTEGER DEFAULT NULL,
            deadline TEXT,
            application_url TEXT
        )
    """)

    # Safe Schema migration helper for scholarships table
    cursor.execute("PRAGMA table_info(scholarships)")
    columns = [row[1] for row in cursor.fetchall()]
    
    extra_cols = [
        ("course", "TEXT DEFAULT 'All'"),
        ("gender", "TEXT DEFAULT 'All'"),
        ("age_limit", "INTEGER DEFAULT NULL"),
        ("application_url", "TEXT DEFAULT NULL"),
        ("academic_requirement_type", "TEXT DEFAULT 'Percentage'"),
        ("minimum_academic_score", "REAL")
    ]
    
    for col_name, col_type in extra_cols:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE scholarships ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

    # Sync legacy minimum_marks with minimum_academic_score where missing
    cursor.execute("""
        UPDATE scholarships 
        SET minimum_academic_score = minimum_marks 
        WHERE minimum_academic_score IS NULL AND minimum_marks IS NOT NULL
    """)
    cursor.execute("""
        UPDATE scholarships 
        SET academic_requirement_type = 'Percentage' 
        WHERE academic_requirement_type IS NULL OR academic_requirement_type = ''
    """)

    # Check database seeding status
    cursor.execute("SELECT COUNT(*) FROM scholarships")
    scholarship_count = cursor.fetchone()[0]

    # Re-seed if demo dataset is low or empty
    if scholarship_count < 10:
        real_scholarships = [
            (
                "AICTE Pragati Scholarship for Girl Students",
                "AICTE / Ministry of Education",
                "Financial support of ₹50,000 per annum for eligible girl students pursuing technical undergraduate degree programs.",
                50000, 60, "Percentage", 60.0, 800000, "Undergraduate", "All", "All", "Engineering & Technology", "Female", 30, "2026-12-31",
                "https://www.aicte-india.org"
            ),
            (
                "AICTE Saksham Scholarship Scheme for Specially Abled",
                "AICTE / Ministry of Education",
                "Assistance of ₹50,000 per annum for specially-abled students pursuing technical degree education.",
                50000, 50, "Percentage", 50.0, 800000, "Undergraduate", "All", "All", "Engineering & Technology", "All", 30, "2026-12-31",
                "https://www.aicte-india.org"
            ),
            (
                "AICTE Swanath Scholarship Scheme",
                "AICTE / Ministry of Education",
                "Support of ₹50,000 per annum for orphan students or wards of martyrs pursuing technical degree programs.",
                50000, 50, "Percentage", 50.0, 800000, "Undergraduate", "All", "All", "Engineering & Technology", "All", 30, "2026-12-31",
                "https://www.aicte-india.org"
            ),
            (
                "PM-USP Central Sector Scheme of Scholarships",
                "Department of Higher Education / NSP",
                "Merit scholarship for top 20th percentile students scoring above 80th percentile in board examinations.",
                12000, 80, "Percentage", 80.0, 450000, "Undergraduate", "All", "All", "All", "All", 25, "2026-11-30",
                "https://scholarships.gov.in"
            ),
            (
                "PM YASASVI Post-Matric Scholarship",
                "Ministry of Social Justice and Empowerment / NTA",
                "Financial aid for meritorious students belonging to OBC, EBC, and DNT categories.",
                20000, 60, "Percentage", 60.0, 250000, "Undergraduate", "All", "OBC", "All", "All", 28, "2026-11-15",
                "https://yet.nta.ac.in"
            ),
            (
                "Post Matric Scholarships Scheme for SC Students",
                "Ministry of Social Justice and Empowerment / NSP",
                "Complete fee waiver and maintenance allowance support for Scheduled Caste students pursuing higher studies.",
                35000, 50, "Percentage", 50.0, 250000, "Undergraduate", "All", "SC", "All", "All", 30, "2026-12-15",
                "https://scholarships.gov.in"
            ),
            (
                "Tamil Nadu Govt First Generation Graduate Fee Waiver",
                "Directorate of Technical Education, Tamil Nadu",
                "Tuition fee waiver for First Generation Graduate students pursuing professional engineering courses in Tamil Nadu.",
                40000, 60, "Percentage", 60.0, 500000, "Undergraduate", "Tamil Nadu", "All", "Engineering & Technology", "All", 25, "2026-10-31",
                "https://tndce.tn.gov.in"
            ),
            (
                "Tamil Nadu Pudhumai Penn Scheme (Moovalur Ramamirtham)",
                "Social Welfare & Women Empowerment Dept, TN",
                "Monthly assistance of ₹1,000 for female students who studied from Class 6 to 12 in Tamil Nadu Government schools.",
                12000, 50, "Percentage", 50.0, 400000, "Undergraduate", "Tamil Nadu", "All", "All", "Female", 25, "2026-12-31",
                "https://penkalvi.tn.gov.in"
            ),
            (
                "Reliance Foundation Undergraduate Scholarship",
                "Reliance Foundation",
                "Prestigious scholarship award supporting meritorious undergraduate students in India up to ₹2 Lakhs.",
                200000, 60, "Percentage", 60.0, 1500000, "Undergraduate", "All", "All", "Engineering & Technology", "All", 26, "2026-10-15",
                "https://www.scholarships.reliancefoundation.org"
            ),
            (
                "Kotak Kanya Scholarship for Girl Students",
                "Kotak Education Foundation",
                "Financial support up to ₹1.5 Lakhs per year for meritorious girl students pursuing professional graduation.",
                150000, 85, "Percentage", 85.0, 600000, "Undergraduate", "All", "All", "Engineering & Technology", "Female", 25, "2026-09-30",
                "https://kotakeducation.org"
            ),
            (
                "HDFC Bank Parivartan's ECSS Programme",
                "HDFC Bank Parivartan Trust",
                "Merit-cum-means scholarship supporting undergraduate students facing financial hardship.",
                50000, 55, "Percentage", 55.0, 600000, "Undergraduate", "All", "All", "All", "All", 28, "2026-10-31",
                "https://www.hdfcbank.com"
            )
        ]

        cursor.executemany("""
            INSERT INTO scholarships (
                name, provider, description, amount, minimum_marks,
                academic_requirement_type, minimum_academic_score,
                maximum_income, education, state, category, course,
                gender, age_limit, deadline, application_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, real_scholarships)

    connection.commit()
    connection.close()

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "AI Scholarship Finder API",
        "architecture": "2-Tier (Hard Eligibility Engine + AI Recommendation Model)"
    })

@app.route("/scholarships", methods=["GET"])
def get_scholarships():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM scholarships")
        rows = cursor.fetchall()
        connection.close()

        scholarships_list = [dict(row) for row in rows]
        return jsonify(scholarships_list)

    except sqlite3.Error as db_error:
        return jsonify({"error": "Database error: " + str(db_error)}), 500

@app.route("/students", methods=["POST"])
def create_student():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"success": False, "message": "No JSON data received."}), 400

    name = data.get("name") or data.get("fullName") or ""
    education = data.get("education") or data.get("educationLevel") or ""
    score_type = data.get("academic_score_type", "Percentage")
    academic_score = data.get("academic_score")
    obtained_marks = data.get("obtained_marks")
    max_marks = data.get("max_marks")
    
    # Legacy marks fallback
    marks = data.get("marks")
    if marks is None:
        if academic_score is not None:
            marks = float(academic_score)
        elif obtained_marks is not None and max_marks is not None and float(max_marks) > 0:
            marks = (float(obtained_marks) / float(max_marks)) * 100.0

    family_income = data.get("family_income") if data.get("family_income") is not None else data.get("income")
    state = data.get("state", "")
    category = data.get("category", "")
    age = data.get("age")
    gender = data.get("gender", "")
    course = data.get("course", "")

    errors = []
    if not isinstance(name, str) or name.strip() == "":
        errors.append("Name is required.")
    if not isinstance(education, str) or education.strip() == "":
        errors.append("Education level is required.")
    if marks is None or not isinstance(marks, (int, float)) or float(marks) < 0:
        errors.append("Academic score must be a valid non-negative number.")
    if family_income is None or not isinstance(family_income, (int, float)) or float(family_income) < 0:
        errors.append("Family income must be a valid non-negative number.")
    if not isinstance(state, str) or state.strip() == "":
        errors.append("State is required.")
    if not isinstance(category, str) or category.strip() == "":
        errors.append("Category is required.")

    if errors:
        return jsonify({"success": False, "message": " ".join(errors)}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO students (
                name, education, marks, academic_score_type, academic_score,
                obtained_marks, max_marks, family_income, state, category,
                age, gender, course
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name.strip(), education.strip(), float(marks), score_type,
            float(academic_score) if academic_score is not None else float(marks),
            float(obtained_marks) if obtained_marks is not None else None,
            float(max_marks) if max_marks is not None else None,
            float(family_income), state.strip(), category.strip(),
            int(age) if age is not None and str(age).isdigit() else None,
            gender.strip() if gender else None,
            course.strip() if course else None
        ))

        connection.commit()
        new_student_id = cursor.lastrowid
        connection.close()

        return jsonify({
            "success": True,
            "message": "Student profile saved successfully",
            "student_id": new_student_id,
        })

    except sqlite3.Error as db_error:
        return jsonify({"success": False, "message": "Database error: " + str(db_error)}), 500

@app.route("/recommendations", methods=["POST"])
def get_recommendations():
    """
    POST /recommendations
    Pipeline:
    Student Profile -> Preprocessing -> Hard Eligibility Engine -> Content-Based AI Recommender -> AI Explanation Generator
    """
    student = request.get_json(silent=True)
    if student is None:
        return jsonify({"success": False, "message": "No student profile JSON received."}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM scholarships")
        rows = cursor.fetchall()
        connection.close()
        scholarships = [dict(row) for row in rows]
    except sqlite3.Error as db_error:
        return jsonify({"success": False, "message": "Database error: " + str(db_error)}), 500

    # 1. Hard Eligibility Evaluation
    eligibility_map = {}
    for sch in scholarships:
        eligibility_map[sch["id"]] = evaluate_eligibility(student, sch)

    # 2. AI Content-Based Recommendation & Ranking
    ranked_scholarships = rank_recommendations(student, scholarships, eligibility_map)

    # 3. Personalized AI Explanation Enrichment
    for sch in ranked_scholarships:
        sch_id = sch["id"]
        elig_res = eligibility_map[sch_id]
        ai_score = sch["ai_match_score"]
        
        explanation_obj = generate_ai_explanation(student, sch, elig_res, ai_score)
        sch["ai_explanation"] = explanation_obj["summary_statement"]

    return jsonify({
        "success": True,
        "total_scholarships_evaluated": len(scholarships),
        "recommendations": ranked_scholarships
    })

@app.route("/evaluate", methods=["GET"])
def evaluate_endpoint():
    """
    GET /evaluate — Runs benchmark evaluator with independent test profiles & ground truth.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM scholarships")
        rows = cursor.fetchall()
        connection.close()
        scholarships = [dict(row) for row in rows]

        metrics = evaluate_system(scholarships)
        return jsonify({"success": True, "metrics": metrics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------
# ADMIN SCHOLARSHIP MANAGEMENT ROUTES
# ---------------------------------------------------------

def is_admin_authorized(req):
    admin_key = req.headers.get("X-Admin-Key")
    return admin_key == ADMIN_SECRET_KEY

@app.route("/admin/scholarships", methods=["GET"])
def admin_get_scholarships():
    if not is_admin_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid Admin Key."}), 401
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM scholarships ORDER BY id DESC")
        rows = cursor.fetchall()
        connection.close()
        return jsonify({"success": True, "scholarships": [dict(r) for r in rows]})
    except sqlite3.Error as err:
        return jsonify({"success": False, "message": str(err)}), 500

@app.route("/admin/scholarships", methods=["POST"])
def admin_add_scholarship():
    if not is_admin_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid Admin Key."}), 401

    data = request.get_json(silent=True)
    if not data or not data.get("name") or not data.get("provider"):
        return jsonify({"success": False, "message": "Scholarship Name and Provider are required."}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        req_type = data.get("academic_requirement_type", "Percentage")
        min_score = data.get("minimum_academic_score")
        if min_score is None:
            min_score = data.get("minimum_marks")

        cursor.execute("""
            INSERT INTO scholarships (
                name, provider, description, amount, minimum_marks,
                academic_requirement_type, minimum_academic_score,
                maximum_income, education, state, category, course,
                gender, age_limit, deadline, application_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("name").strip(),
            data.get("provider").strip(),
            data.get("description", "").strip(),
            float(data.get("amount", 0.0)),
            float(min_score) if min_score is not None else 0.0,
            req_type,
            float(min_score) if min_score is not None else None,
            float(data.get("maximum_income")) if data.get("maximum_income") is not None else None,
            data.get("education", "Undergraduate").strip(),
            data.get("state", "All").strip(),
            data.get("category", "All").strip(),
            data.get("course", "All").strip(),
            data.get("gender", "All").strip(),
            int(data.get("age_limit")) if data.get("age_limit") is not None and str(data.get("age_limit")).isdigit() else None,
            data.get("deadline", "").strip(),
            data.get("application_url", "").strip()
        ))

        connection.commit()
        new_id = cursor.lastrowid
        connection.close()

        return jsonify({"success": True, "message": "Scholarship added successfully.", "id": new_id})
    except sqlite3.Error as err:
        return jsonify({"success": False, "message": "Database error: " + str(err)}), 500

@app.route("/admin/scholarships/<int:scholarship_id>", methods=["PUT"])
def admin_edit_scholarship(scholarship_id):
    if not is_admin_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid Admin Key."}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No update data received."}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM scholarships WHERE id = ?", (scholarship_id,))
        if not cursor.fetchone():
            connection.close()
            return jsonify({"success": False, "message": "Scholarship not found."}), 444

        req_type = data.get("academic_requirement_type", "Percentage")
        min_score = data.get("minimum_academic_score")
        if min_score is None:
            min_score = data.get("minimum_marks")

        cursor.execute("""
            UPDATE scholarships SET
                name = ?, provider = ?, description = ?, amount = ?,
                minimum_marks = ?, academic_requirement_type = ?, minimum_academic_score = ?,
                maximum_income = ?, education = ?, state = ?, category = ?,
                course = ?, gender = ?, age_limit = ?, deadline = ?, application_url = ?
            WHERE id = ?
        """, (
            data.get("name", "").strip(),
            data.get("provider", "").strip(),
            data.get("description", "").strip(),
            float(data.get("amount", 0.0)),
            float(min_score) if min_score is not None else 0.0,
            req_type,
            float(min_score) if min_score is not None else None,
            float(data.get("maximum_income")) if data.get("maximum_income") is not None else None,
            data.get("education", "All").strip(),
            data.get("state", "All").strip(),
            data.get("category", "All").strip(),
            data.get("course", "All").strip(),
            data.get("gender", "All").strip(),
            int(data.get("age_limit")) if data.get("age_limit") is not None and str(data.get("age_limit")).isdigit() else None,
            data.get("deadline", "").strip(),
            data.get("application_url", "").strip(),
            scholarship_id
        ))

        connection.commit()
        connection.close()

        return jsonify({"success": True, "message": "Scholarship updated successfully."})
    except sqlite3.Error as err:
        return jsonify({"success": False, "message": "Database error: " + str(err)}), 500

@app.route("/admin/scholarships/<int:scholarship_id>", methods=["DELETE"])
def admin_delete_scholarship(scholarship_id):
    if not is_admin_authorized(request):
        return jsonify({"success": False, "message": "Unauthorized. Invalid Admin Key."}), 401

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("DELETE FROM scholarships WHERE id = ?", (scholarship_id,))
        connection.commit()
        deleted = cursor.rowcount
        connection.close()

        if deleted == 0:
            return jsonify({"success": False, "message": "Scholarship ID not found."}), 404

        return jsonify({"success": True, "message": "Scholarship deleted successfully."})
    except sqlite3.Error as err:
        return jsonify({"success": False, "message": "Database error: " + str(err)}), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True)