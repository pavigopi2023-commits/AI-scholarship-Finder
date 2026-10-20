# =====================================================
# AI SCHOLARSHIP FINDER — AI EXPLANATION GENERATOR
# Module: ai_explanation.py
# Generates transparent, human-readable personalized AI explanations.
# =====================================================

def generate_ai_explanation(student, scholarship, eligibility_result, ai_score):
    """
    Generates a clear, transparent explanation detailing:
    1. Deterministic eligibility status
    2. Specific passed, failed, and not-applicable criteria
    3. Personalized AI recommendation summary statement
    """
    is_eligible = eligibility_result.get("eligible", False)
    passed_criteria = eligibility_result.get("passed_criteria", [])
    failed_criteria = eligibility_result.get("failed_criteria", [])
    not_applicable = eligibility_result.get("not_applicable_criteria", [])

    reasons = []
    
    # Add passed eligibility criteria
    for passed in passed_criteria:
        reasons.append({"text": passed, "passed": True, "type": "passed"})

    # Add failed criteria
    for failed in failed_criteria:
        reasons.append({"text": failed, "passed": False, "type": "failed"})

    # Add not applicable criteria
    for na in not_applicable:
        reasons.append({"text": na, "passed": True, "type": "not_applicable"})

    # Formulate personalized summary statement based on specific criteria
    if is_eligible:
        if passed_criteria:
            first_pass = passed_criteria[0]
            summary_statement = f"Recommended ({ai_score}% AI Match). Your profile satisfies mandatory eligibility ({first_pass})."
        else:
            summary_statement = f"Eligible match ({ai_score}% AI Match). All applicable criteria satisfied."
    else:
        if failed_criteria:
            first_fail = failed_criteria[0]
            summary_statement = f"Not eligible ({ai_score}% Feature Score). {first_fail}."
        else:
            summary_statement = f"Ineligible match ({ai_score}% Feature Score). One or more criteria did not match."

    return {
        "summary_statement": summary_statement,
        "reasons": reasons,
        "is_eligible": is_eligible,
        "ai_match_score": ai_score
    }

