# =====================================================
# AI SCHOLARSHIP FINDER — HARD ELIGIBILITY ENGINE
# Module: eligibility_engine.py
# Deterministic rule-based eligibility evaluation engine.
# Evaluates mandatory hard constraints for candidate scholarships.
# Evaluates ONLY criteria specified by each scholarship.
# Categorizes unspecified criteria as "Not Applicable".
# =====================================================

def is_text_match(scholarship_val, student_val):
    """
    Checks string criteria match.
    A scholarship value of 'All', 'None', 'Any', or empty matches any student value.
    """
    if not scholarship_val or str(scholarship_val).strip().lower() in ["all", "none", "any", ""]:
        return True
    if not student_val:
        return True
    return str(scholarship_val).strip().lower() == str(student_val).strip().lower()

def is_course_match(scholarship_course, student_course):
    """
    Checks course/field compatibility.
    Handles exact match, 'All', or broader engineering/technology matching.
    """
    if not scholarship_course or str(scholarship_course).strip().lower() in ["all", "none", "any", ""]:
        return True
    if not student_course:
        return True
    
    sch_c = str(scholarship_course).strip().lower()
    std_c = str(student_course).strip().lower()
    
    if sch_c == std_c:
        return True
        
    # Check general Engineering / Technology branch overlap
    engineering_branches = [
        "computer science engineering", "information technology", 
        "electronics and communication engineering", "electrical engineering", 
        "mechanical engineering", "civil engineering"
    ]
    if sch_c == "engineering & technology" and (std_c in engineering_branches or "engineering" in std_c):
        return True
    if std_c == "engineering & technology" and (sch_c in engineering_branches or "engineering" in sch_c):
        return True
        
    return False

def evaluate_academic_eligibility(student, scholarship):
    """
    Evaluates dynamic academic score eligibility.
    Supports Percentage, CGPA, Marks, and None/Unspecified.
    Incompatible score types without verified conversion will fail hard eligibility.
    """
    sch_req_type = str(scholarship.get("academic_requirement_type") or "Percentage").strip()
    if sch_req_type.lower() in ["none", "all", "any", "null"]:
        return {
            "is_specified": False,
            "passed": True,
            "message": "Academic requirement: Not Applicable (Open to all academic score levels)"
        }

    sch_min_score = scholarship.get("minimum_academic_score")
    if sch_min_score is None:
        sch_min_score = scholarship.get("minimum_marks")
    
    # If no academic score requirement specified by scholarship
    if sch_min_score is None or float(sch_min_score) == 0:
        return {
            "is_specified": False,
            "passed": True,
            "message": "Academic requirement: Not Applicable (No minimum academic score specified)"
        }

    sch_min_score = float(sch_min_score)

    std_score_type = str(student.get("academic_score_type") or "Percentage").strip()
    std_score = student.get("academic_score")
    if std_score is None:
        std_score = student.get("marks")
    
    std_obtained = student.get("obtained_marks")
    std_max = student.get("max_marks")

    # If student provided Marks (obtained / max), calculate percentage if requirement is Percentage
    if std_score_type == "Marks" and std_obtained is not None and std_max is not None and float(std_max) > 0:
        calc_percentage = (float(std_obtained) / float(std_max)) * 100.0
        if sch_req_type == "Percentage":
            if calc_percentage >= sch_min_score:
                return {
                    "is_specified": True,
                    "passed": True,
                    "message": f"Academic marks ({std_obtained:g}/{std_max:g} = {calc_percentage:.1f}%) meet minimum required ({sch_min_score:.1f}%)"
                }
            else:
                return {
                    "is_specified": True,
                    "passed": False,
                    "message": f"Academic marks ({std_obtained:g}/{std_max:g} = {calc_percentage:.1f}%) below minimum required ({sch_min_score:.1f}%)"
                }
        elif sch_req_type == "Marks":
            if float(std_obtained) >= sch_min_score:
                return {
                    "is_specified": True,
                    "passed": True,
                    "message": f"Obtained marks ({std_obtained:g}/{std_max:g}) meet minimum required ({sch_min_score:g} Marks)"
                }
            else:
                return {
                    "is_specified": True,
                    "passed": False,
                    "message": f"Obtained marks ({std_obtained:g}/{std_max:g}) below minimum required ({sch_min_score:g} Marks)"
                }

    # Standard direct comparison when score types match
    if std_score_type.lower() == sch_req_type.lower():
        if std_score is not None and float(std_score) >= sch_min_score:
            unit = "%" if sch_req_type == "Percentage" else (" CGPA" if sch_req_type == "CGPA" else " Marks")
            return {
                "is_specified": True,
                "passed": True,
                "message": f"Academic {std_score_type} ({std_score:g}{unit}) meets minimum required ({sch_min_score:g}{unit})"
            }
        else:
            actual = float(std_score) if std_score is not None else 0.0
            unit = "%" if sch_req_type == "Percentage" else (" CGPA" if sch_req_type == "CGPA" else " Marks")
            return {
                "is_specified": True,
                "passed": False,
                "message": f"Academic {std_score_type} ({actual:g}{unit}) below minimum required ({sch_min_score:g}{unit})"
            }

    # Handle incompatible score types without arbitrary conversion
    return {
        "is_specified": True,
        "passed": False,
        "message": f"Academic requirement requires '{sch_req_type}' (Minimum: {sch_min_score:g}), but profile provided '{std_score_type}' ({std_score}). Direct comparison is incompatible."
    }

def evaluate_eligibility(student, scholarship):
    """
    Evaluates hard deterministic eligibility constraints in fixed order:
    1. Education Level
    2. Course / Field of Study
    3. Academic Score (Dynamic Percentage / CGPA / Marks)
    4. Family Income
    5. State / Domicile
    6. Category
    7. Gender
    8. Age Limit (Optional)

    Evaluates ONLY criteria specified by the scholarship.
    Returns dict:
    - eligible: True if ALL specified hard requirements are met.
    - passed_criteria: List of passed criteria explanations.
    - failed_criteria: List of failed criteria explanations.
    - not_applicable_criteria: List of non-applicable/unspecified criteria.
    """
    passed_criteria = []
    failed_criteria = []
    not_applicable_criteria = []

    # 1. Education Level Check
    sch_edu = scholarship.get("education")
    std_edu = student.get("educationLevel") or student.get("education")
    if not sch_edu or str(sch_edu).strip().lower() in ["all", "none", "any", ""]:
        not_applicable_criteria.append("Education level: Not Applicable (Open to all education levels)")
    else:
        if is_text_match(sch_edu, std_edu):
            passed_criteria.append(f"Education level ({std_edu or 'Current'}) satisfies requirement '{sch_edu}'")
        else:
            failed_criteria.append(f"Education level required is '{sch_edu}' (Current: '{std_edu}')")

    # 2. Course / Field of Study Check
    sch_course = scholarship.get("course")
    std_course = student.get("course")
    if not sch_course or str(sch_course).strip().lower() in ["all", "none", "any", ""]:
        not_applicable_criteria.append("Course field: Not Applicable (Open to all courses/fields)")
    else:
        if is_course_match(sch_course, std_course):
            passed_criteria.append(f"Course field ({std_course or 'Selected'}) is eligible for '{sch_course}'")
        else:
            failed_criteria.append(f"Course required is '{sch_course}' (Current: '{std_course}')")

    # 3. Dynamic Academic Score Check
    acad_res = evaluate_academic_eligibility(student, scholarship)
    if not acad_res["is_specified"]:
        not_applicable_criteria.append(acad_res["message"])
    elif acad_res["passed"]:
        passed_criteria.append(acad_res["message"])
    else:
        failed_criteria.append(acad_res["message"])

    # 4. Family Income Ceiling Check
    max_income = scholarship.get("maximum_income")
    raw_income = student.get("income") if student.get("income") is not None else student.get("family_income")
    student_income = float(raw_income) if raw_income is not None else None

    if max_income is None or float(max_income) == 0:
        not_applicable_criteria.append("Family income ceiling: Not Applicable (No income restriction specified)")
    else:
        if student_income is not None and student_income <= float(max_income):
            passed_criteria.append(f"Family income (₹{student_income:,.0f}) is within limit (≤ ₹{float(max_income):,.0f})")
        elif student_income is not None:
            failed_criteria.append(f"Family income (₹{student_income:,.0f}) exceeds maximum limit (₹{float(max_income):,.0f})")
        else:
            failed_criteria.append(f"Family income ceiling is ₹{float(max_income):,.0f} — Profile income not provided")

    # 5. State / Domicile Eligibility Check
    sch_state = scholarship.get("state")
    std_state = student.get("state")
    if not sch_state or str(sch_state).strip().lower() in ["all", "none", "any", ""]:
        not_applicable_criteria.append("State domicile: Not Applicable (Open to all Indian States/UTs)")
    else:
        if is_text_match(sch_state, std_state):
            passed_criteria.append(f"State domicile ({std_state or 'Current'}) matches requirement '{sch_state}'")
        else:
            failed_criteria.append(f"Applicable to state '{sch_state}' (Domicile: '{std_state}')")

    # 6. Category Reservation Check
    sch_cat = scholarship.get("category")
    std_cat = student.get("category")
    if not sch_cat or str(sch_cat).strip().lower() in ["all", "none", "any", ""]:
        not_applicable_criteria.append("Category reservation: Not Applicable (Open to all categories)")
    else:
        if is_text_match(sch_cat, std_cat):
            passed_criteria.append(f"Category ({std_cat or 'General'}) matches requirement '{sch_cat}'")
        else:
            failed_criteria.append(f"Category required is '{sch_cat}' (Current: '{std_cat}')")

    # 7. Gender Restriction Check
    sch_gender = scholarship.get("gender")
    std_gender = student.get("gender")
    if not sch_gender or str(sch_gender).strip().lower() in ["all", "none", "any", ""]:
        not_applicable_criteria.append("Gender requirement: Not Applicable (Open to all genders)")
    else:
        if is_text_match(sch_gender, std_gender):
            passed_criteria.append(f"Gender ({std_gender or 'Current'}) meets criteria '{sch_gender}'")
        else:
            failed_criteria.append(f"Scholarship restricted to '{sch_gender}' applicants (Current: '{std_gender}')")

    # 8. Age Limit Check (OPTIONAL criterion)
    age_limit = scholarship.get("age_limit")
    student_age = student.get("age")
    if age_limit is None or str(age_limit).strip() == "" or str(age_limit).lower() in ["none", "null"]:
        not_applicable_criteria.append("Age limit: Not Applicable (No age restriction specified)")
    else:
        age_limit_val = float(age_limit)
        if student_age is None or str(student_age).strip() == "":
            not_applicable_criteria.append(f"Age limit exists (≤ {age_limit_val:g} yrs) — Profile age not provided")
        elif float(student_age) <= age_limit_val:
            passed_criteria.append(f"Age ({student_age} yrs) is within permitted limit (≤ {age_limit_val:g} yrs)")
        else:
            failed_criteria.append(f"Age ({student_age} yrs) exceeds maximum age limit ({age_limit_val:g} yrs)")

    is_eligible = (len(failed_criteria) == 0)

    return {
        "eligible": is_eligible,
        "passed_criteria": passed_criteria,
        "failed_criteria": failed_criteria,
        "not_applicable_criteria": not_applicable_criteria
    }

