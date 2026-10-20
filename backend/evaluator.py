# =====================================================
# AI SCHOLARSHIP FINDER — BENCHMARK EVALUATOR
# Module: evaluator.py
# Independent offline evaluation framework for recommendation quality.
# Measures Precision@K, Recall@K, Top-K Accuracy, and Mean Reciprocal Rank (MRR).
# Ground truth relevant scholarships are MANUALLY CURATED independently of the algorithm.
# =====================================================

import sqlite3
import os
import sys
import io

# Set UTF-8 encoding for stdout on Windows console
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def evaluate_system(scholarships):
    """
    Evaluates the 2-tier recommendation system across 5 benchmark test profiles.
    Independent ground truth sets are manually curated for each profile.
    
    Metrics Computed:
    - Precision@3 & Precision@5: Ratio of top-K recommendations that are truly relevant.
    - Recall@3 & Recall@5: Ratio of total ground truth relevant schemes retrieved in top-K.
    - Top-K Accuracy (Top-3 & Top-5): Percentage of test queries with at least 1 relevant item in top-K.
    - MRR (Mean Reciprocal Rank): 1 / rank of first relevant item recommended.
    """
    from eligibility_engine import evaluate_eligibility
    from recommender import rank_recommendations

    # Map scholarship names to IDs if list of dicts provided
    name_to_id = {s.get("name", "").strip(): s.get("id") for s in scholarships if s.get("name")}

    # Helper function to resolve scholarship IDs from names or IDs
    def resolve_ids(id_or_name_list):
        res = set()
        for item in id_or_name_list:
            if isinstance(item, int):
                res.add(item)
            elif isinstance(item, str) and item in name_to_id:
                res.add(name_to_id[item])
        return res

    # 5 Realistically Curated Benchmark Student Profiles with Independent Ground Truth
    test_profiles = [
        {
            "id": "Profile_1",
            "name": "Ananya Sharma (Female, TN, CS Engg, 85%, ₹2L Income, OBC, 20 yrs)",
            "student": {
                "fullName": "Ananya Sharma",
                "educationLevel": "Undergraduate",
                "course": "Computer Science Engineering",
                "academic_score_type": "Percentage",
                "academic_score": 85.0,
                "marks": 85.0,
                "income": 200000.0,
                "family_income": 200000.0,
                "state": "Tamil Nadu",
                "category": "OBC",
                "gender": "Female",
                "age": 20
            },
            # Manually curated expected relevant scholarship IDs
            "expected_names": [
                "AICTE Pragati Scholarship for Girl Students",
                "PM-USP Central Sector Scheme of Scholarships",
                "PM YASASVI Post-Matric Scholarship",
                "Tamil Nadu Govt First Generation Graduate Fee Waiver",
                "Tamil Nadu Pudhumai Penn Scheme (Moovalur Ramamirtham)",
                "Reliance Foundation Undergraduate Scholarship",
                "Kotak Kanya Scholarship for Girl Students",
                "HDFC Bank Parivartan's ECSS Programme"
            ]
        },
        {
            "id": "Profile_2",
            "name": "Rahul Verma (Male, TN, Mech Engg, 65%, ₹4L Income, General, 22 yrs)",
            "student": {
                "fullName": "Rahul Verma",
                "educationLevel": "Undergraduate",
                "course": "Mechanical Engineering",
                "academic_score_type": "Percentage",
                "academic_score": 65.0,
                "marks": 65.0,
                "income": 400000.0,
                "family_income": 400000.0,
                "state": "Tamil Nadu",
                "category": "General",
                "gender": "Male",
                "age": 22
            },
            "expected_names": [
                "Tamil Nadu Govt First Generation Graduate Fee Waiver",
                "Reliance Foundation Undergraduate Scholarship",
                "HDFC Bank Parivartan's ECSS Programme"
            ]
        },
        {
            "id": "Profile_3",
            "name": "Kavitha S (Female, TN, ECE Engg, 90%, ₹1.8L Income, SC, 19 yrs)",
            "student": {
                "fullName": "Kavitha S",
                "educationLevel": "Undergraduate",
                "course": "Electronics and Communication Engineering",
                "academic_score_type": "Percentage",
                "academic_score": 90.0,
                "marks": 90.0,
                "income": 180000.0,
                "family_income": 180000.0,
                "state": "Tamil Nadu",
                "category": "SC",
                "gender": "Female",
                "age": 19
            },
            "expected_names": [
                "AICTE Pragati Scholarship for Girl Students",
                "PM-USP Central Sector Scheme of Scholarships",
                "Post Matric Scholarships Scheme for SC Students",
                "Tamil Nadu Govt First Generation Graduate Fee Waiver",
                "Tamil Nadu Pudhumai Penn Scheme (Moovalur Ramamirtham)",
                "Reliance Foundation Undergraduate Scholarship",
                "Kotak Kanya Scholarship for Girl Students",
                "HDFC Bank Parivartan's ECSS Programme"
            ]
        },
        {
            "id": "Profile_4",
            "name": "Vikram Malhotra (Male, Delhi, Commerce, 82%, ₹3L Income, General, 21 yrs)",
            "student": {
                "fullName": "Vikram Malhotra",
                "educationLevel": "Undergraduate",
                "course": "Commerce & Management",
                "academic_score_type": "Percentage",
                "academic_score": 82.0,
                "marks": 82.0,
                "income": 300000.0,
                "family_income": 300000.0,
                "state": "Delhi",
                "category": "General",
                "gender": "Male",
                "age": 21
            },
            "expected_names": [
                "PM-USP Central Sector Scheme of Scholarships",
                "HDFC Bank Parivartan's ECSS Programme"
            ]
        },
        {
            "id": "Profile_5",
            "name": "Sneha Patil (Female, Maharashtra, CS Engg, 8.8 CGPA, ₹5L Income, General, 23 yrs)",
            "student": {
                "fullName": "Sneha Patil",
                "educationLevel": "Undergraduate",
                "course": "Computer Science Engineering",
                "academic_score_type": "CGPA",
                "academic_score": 8.8,
                "marks": 88.0,
                "income": 500000.0,
                "family_income": 500000.0,
                "state": "Maharashtra",
                "category": "General",
                "gender": "Female",
                "age": 23
            },
            "expected_names": [
                "AICTE Pragati Scholarship for Girl Students",
                "Reliance Foundation Undergraduate Scholarship",
                "HDFC Bank Parivartan's ECSS Programme"
            ]
        }
    ]

    print("=====================================================")
    print("AI SCHOLARSHIP FINDER -- BENCHMARK EVALUATION REPORT")
    print("=====================================================\n")

    p_at_3_list, r_at_3_list = [], []
    p_at_5_list, r_at_5_list = [], []
    top_3_hits, top_5_hits = 0, 0
    reciprocal_ranks = []

    for profile_item in test_profiles:
        profile_name = profile_item["name"]
        student = profile_item["student"]
        expected_names = profile_item["expected_names"]

        # Resolve ground truth IDs from expected names in dataset
        expected_ids = set()
        for s in scholarships:
            if s.get("name") in expected_names:
                expected_ids.add(s["id"])

        # Compute hard eligibility map using engine
        eligibility_results = {}
        for sch in scholarships:
            eligibility_results[sch["id"]] = evaluate_eligibility(student, sch)

        # Run Tier 2 Content-Based AI Recommender
        ranked = rank_recommendations(student, scholarships, eligibility_results)
        ranked_ids = [item["id"] for item in ranked]

        # Top-3 Evaluation
        top_3_rec_ids = set(ranked_ids[:3])
        hits_3 = top_3_rec_ids.intersection(expected_ids)
        p_3 = len(hits_3) / 3.0
        r_3 = len(hits_3) / float(len(expected_ids)) if len(expected_ids) > 0 else 1.0
        p_at_3_list.append(p_3)
        r_at_3_list.append(r_3)
        if len(hits_3) > 0:
            top_3_hits += 1

        # Top-5 Evaluation
        top_5_rec_ids = set(ranked_ids[:5])
        hits_5 = top_5_rec_ids.intersection(expected_ids)
        p_5 = len(hits_5) / 5.0
        r_5 = len(hits_5) / float(len(expected_ids)) if len(expected_ids) > 0 else 1.0
        p_at_5_list.append(p_5)
        r_at_5_list.append(r_5)
        if len(hits_5) > 0:
            top_5_hits += 1

        # MRR Calculation
        rr = 0.0
        for rank_idx, rid in enumerate(ranked_ids, 1):
            if rid in expected_ids:
                rr = 1.0 / float(rank_idx)
                break
        reciprocal_ranks.append(rr)

        print(f"Profile: {profile_name}")
        print(f"  - Ground Truth Relevant Schemes: {len(expected_ids)}")
        print(f"  - Top-3 Recommended:")
        for idx, sch in enumerate(ranked[:3], 1):
            is_hit = "[RELEVANT]" if sch["id"] in expected_ids else "[OTHER]"
            print(f"    {idx}. [{sch['ai_match_score']}% Match] {sch['name']} {is_hit}")
        print(f"  - Precision@3: {p_3 * 100:.1f}% | Recall@3: {r_3 * 100:.1f}%")
        print(f"  - Precision@5: {p_5 * 100:.1f}% | Recall@5: {r_5 * 100:.1f}%\n")

    num_profiles = float(len(test_profiles))
    avg_p_3 = (sum(p_at_3_list) / num_profiles) * 100.0
    avg_r_3 = (sum(r_at_3_list) / num_profiles) * 100.0
    avg_p_5 = (sum(p_at_5_list) / num_profiles) * 100.0
    avg_r_5 = (sum(r_at_5_list) / num_profiles) * 100.0
    top_3_acc = (top_3_hits / num_profiles) * 100.0
    top_5_acc = (top_5_hits / num_profiles) * 100.0
    mrr = sum(reciprocal_ranks) / num_profiles

    print("-----------------------------------------------------")
    print("OVERALL INDEPENDENT EVALUATION METRICS:")
    print(f"Precision@3: {avg_p_3:.1f}%")
    print(f"Recall@3:    {avg_r_3:.1f}%")
    print(f"Precision@5: {avg_p_5:.1f}%")
    print(f"Recall@5:    {avg_r_5:.1f}%")
    print(f"Top-3 Accuracy: {top_3_acc:.1f}%")
    print(f"Top-5 Accuracy: {top_5_acc:.1f}%")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.3f}")
    print("=====================================================\n")

    return {
        "precision_at_3": round(avg_p_3, 2),
        "recall_at_3": round(avg_r_3, 2),
        "precision_at_5": round(avg_p_5, 2),
        "recall_at_5": round(avg_r_5, 2),
        "top_3_accuracy": round(top_3_acc, 2),
        "top_5_accuracy": round(top_5_acc, 2),
        "mrr": round(mrr, 3)
    }

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "scholarship.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scholarships")
        rows = cursor.fetchall()
        sch_list = [dict(row) for row in rows]
        conn.close()
        evaluate_system(sch_list)
    except Exception as e:
        print("Evaluation runner requires initialized database:", e)

