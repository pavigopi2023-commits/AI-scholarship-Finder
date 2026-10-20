# =====================================================
# AI SCHOLARSHIP FINDER — AI RECOMMENDATION ENGINE
# Module: recommender.py
# Content-Based Feature Vector Recommendation Model
# Calculates AI relevance, feature similarity, and rank scores.
# =====================================================

import math

def calculate_recommendation_score(student, scholarship, eligibility_result):
    """
    Calculates an explainable AI Recommendation Score (0 to 100%) based on 
    content-based feature vector similarity and weighted student-scholarship alignment.
    
    Crucially, Not Applicable (unspecified) scholarship criteria receive full fit credit 
    so that students are NOT penalized for criteria a scholarship does not restrict.

    Feature Weights (Total 100 Base Points):
    - Academic Performance & Margin Fit: 30 pts
    - Financial Need & Income Fit Gradient: 25 pts
    - Education Level & Course Field Fit: 20 pts
    - Domicile & Regional Alignment: 15 pts
    - Category & Gender Special Alignment: 10 pts
    """
    score = 0.0
    
    # -------------------------------------------------------------
    # 1. ACADEMIC PERFORMANCE & MARGIN FIT (30 Points Max)
    # -------------------------------------------------------------
    sch_req_type = str(scholarship.get("academic_requirement_type") or "Percentage").strip().lower()
    min_score = scholarship.get("minimum_academic_score")
    if min_score is None:
        min_score = scholarship.get("minimum_marks")
    
    min_score_val = float(min_score) if min_score is not None else 0.0

    if sch_req_type in ["none", "all", "any"] or min_score_val == 0.0:
        # No academic restriction specified: full fit credit (30 pts)
        score += 30.0
    else:
        std_score_type = str(student.get("academic_score_type") or "Percentage").strip().lower()
        std_score_val = student.get("academic_score")
        if std_score_val is None:
            std_score_val = student.get("marks")
        
        std_obtained = student.get("obtained_marks")
        std_max = student.get("max_marks")

        # Normalize student score if obtained/max provided for Marks
        if std_score_type == "marks" and std_obtained is not None and std_max is not None and float(std_max) > 0:
            if sch_req_type == "percentage":
                std_score_val = (float(std_obtained) / float(std_max)) * 100.0
                std_score_type = "percentage"
            elif sch_req_type == "marks":
                std_score_val = float(std_obtained)

        std_score_num = float(std_score_val) if std_score_val is not None else 0.0

        if std_score_type == sch_req_type:
            if std_score_num >= min_score_val:
                # Base credit for meeting requirement (22 pts)
                score += 22.0
                # Performance Margin Bonus (up to 8 pts)
                if sch_req_type == "cgpa":
                    margin = (std_score_num - min_score_val) / max(0.5, 10.0 - min_score_val)
                elif sch_req_type == "percentage":
                    margin = (std_score_num - min_score_val) / max(1.0, 100.0 - min_score_val)
                else:
                    margin = (std_score_num - min_score_val) / max(1.0, min_score_val)
                score += min(8.0, max(0.0, margin * 8.0))
            else:
                # Partial credit proportional to marks achieved
                ratio = std_score_num / min_score_val if min_score_val > 0 else 0.0
                score += min(15.0, ratio * 15.0)
        else:
            # Incompatible score type without conversion rule: neutral partial credit (12 pts)
            score += 12.0

    # -------------------------------------------------------------
    # 2. FINANCIAL NEED & INCOME GRADIENT (25 Points Max)
    # -------------------------------------------------------------
    max_income = scholarship.get("maximum_income")
    max_income_val = float(max_income) if max_income is not None else 0.0

    raw_income = student.get("income") if student.get("income") is not None else student.get("family_income")
    student_income = float(raw_income) if raw_income is not None else 0.0

    if max_income_val == 0.0 or max_income is None:
        # Scholarship has no income ceiling: full fit credit (25 pts)
        score += 25.0
    elif student_income <= max_income_val:
        # Base credit for being within income ceiling (18 pts)
        score += 18.0
        # Financial Need Priority (up to 7 pts): lower income relative to ceiling receives priority
        need_ratio = 1.0 - (student_income / max_income_val)
        score += min(7.0, max(0.0, need_ratio * 7.0))
    else:
        # Excess income: partial credit drops as income exceeds limit
        over_ratio = max_income_val / max(1.0, student_income)
        score += min(10.0, over_ratio * 10.0)

    # -------------------------------------------------------------
    # 3. EDUCATION LEVEL & COURSE FIELD FIT (20 Points Max)
    # -------------------------------------------------------------
    sch_edu = (scholarship.get("education") or "All").strip().lower()
    std_edu = (student.get("educationLevel") or student.get("education") or "All").strip().lower()
    
    if sch_edu in ["all", "none", "any", ""] or sch_edu == std_edu:
        score += 10.0
    else:
        score += 4.0  # Partial level similarity

    sch_course = (scholarship.get("course") or "All").strip().lower()
    std_course = (student.get("course") or "All").strip().lower()
    
    if sch_course in ["all", "none", "any", ""] or sch_course == std_course:
        score += 10.0
    elif sch_course in ["engineering & technology", "computer science engineering"] and "engineering" in std_course:
        score += 8.0
    else:
        score += 3.0

    # -------------------------------------------------------------
    # 4. DOMICILE & REGIONAL ALIGNMENT (15 Points Max)
    # -------------------------------------------------------------
    sch_state = (scholarship.get("state") or "All").strip().lower()
    std_state = (student.get("state") or "All").strip().lower()
    
    if sch_state in ["all", "none", "any", ""]:
        # Open to all states: full fit credit (15 pts)
        score += 15.0
    elif sch_state == std_state:
        # Specific state match (15 pts bonus for localized match)
        score += 15.0
    else:
        score += 5.0

    # -------------------------------------------------------------
    # 5. CATEGORY & DEMOGRAPHIC ALIGNMENT (10 Points Max)
    # -------------------------------------------------------------
    sch_cat = (scholarship.get("category") or "All").strip().lower()
    std_cat = (student.get("category") or "All").strip().lower()
    
    if sch_cat in ["all", "none", "any", ""] or sch_cat == std_cat:
        score += 6.0
    else:
        score += 2.0
        
    sch_gender = (scholarship.get("gender") or "All").strip().lower()
    std_gender = (student.get("gender") or "All").strip().lower()
    
    if sch_gender in ["all", "none", "any", ""] or sch_gender == std_gender:
        score += 4.0
    else:
        score += 1.0

    # Clamp final AI score between 0 and 100
    ai_score = round(min(100.0, max(0.0, score)), 1)
    
    return ai_score

def rank_recommendations(student, scholarships, eligibility_results):
    """
    Ranks candidate scholarships using a 2-tier process:
    1. First Tier: Hard Eligibility Filter status
    2. Second Tier: Content-Based AI Match Score
    
    Returns a sorted list of enriched scholarship dicts.
    """
    ranked_list = []
    
    for scholarship in scholarships:
        sch_id = scholarship.get("id")
        eligibility_res = eligibility_results.get(sch_id, {
            "eligible": False,
            "passed_criteria": [],
            "failed_criteria": ["Evaluation error"],
            "not_applicable_criteria": []
        })
        
        ai_score = calculate_recommendation_score(student, scholarship, eligibility_res)
        
        enriched = dict(scholarship)
        enriched["eligible"] = eligibility_res["eligible"]
        enriched["passed_criteria"] = eligibility_res["passed_criteria"]
        enriched["failed_criteria"] = eligibility_res["failed_criteria"]
        enriched["not_applicable_criteria"] = eligibility_res.get("not_applicable_criteria", [])
        enriched["ai_match_score"] = ai_score
        
        ranked_list.append(enriched)
        
    # Sort: Eligible items first, then by highest AI Match Score
    ranked_list.sort(key=lambda item: (1 if item["eligible"] else 0, item["ai_match_score"]), reverse=True)
    
    return ranked_list

