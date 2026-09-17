# eval_extraction.py
"""
NEXUS Extraction Evaluation Script (Section 4.3 Bonus)
Checks the extraction step against hand-labelled ground truth pages and reports accuracy.
"""
from app.services.extractor import extract_job_details

# 3 Hand-Labeled Benchmark Pages (Ground Truth)
BENCHMARK_PAGES = [
    {
        "source": "Python.org (Adzuna)",
        "raw_text": """
        Senior Python Developer at Adzuna. London, UK (Remote allowed). 
        Salary: €60,000 - €70,000 annually.
        We need expertise in Spark, LLMs, PostgreSQL, React, and AWS. Rolling deadline.
        """,
        "ground_truth": {
            "title": "Senior Python Developer",
            "company": "Adzuna",
            "remote_ok": True,
            "stipend": "€60,000 - €70,000",
            "skills": {"python", "spark", "llms", "postgresql", "react", "aws"}
        }
    },
    {
        "source": "Ashby ATS (Rivian)",
        "raw_text": """
        Rivian - Data Engineering Intern - AI & Analytics - January - August 2027.
        Palo Alto, CA. Compensation: $51/hr.
        Building data pipelines using Python, SQL, Databricks, Snowflake, dbt, and Terraform.
        """,
        "ground_truth": {
            "title": "Data Engineering Intern - AI & Analytics",
            "company": "Rivian",
            "remote_ok": True,
            "stipend": "$51/hr",
            "skills": {"python", "sql", "databricks", "snowflake", "dbt", "terraform"}
        }
    },
    {
        "source": "HFT Portal (Citadel)",
        "raw_text": """
        Citadel LLC - Machine Learning Researcher - PhD Intern - US.
        Houston, TX (On-site only). Compensation: $125/hr.
        Applying machine learning, deep learning, statistical modeling, and Python.
        """,
        "ground_truth": {
            "title": "Machine Learning Researcher",
            "company": "Citadel",
            "remote_ok": False,
            "stipend": "$125/hr",
            "skills": {"machine learning", "deep learning", "statistical modeling", "python"}
        }
    }
]

def run_eval():
    print("=" * 70)
    print("📋 NEXUS Extraction Accuracy Benchmark (Section 4.3)")
    print("=" * 70)

    total_fields = 0
    correct_fields = 0
    skill_f1_scores = []

    for idx, item in enumerate(BENCHMARK_PAGES, 1):
        gt = item["ground_truth"]
        pred = extract_job_details(item["raw_text"])

        if not pred:
            print(f"[{idx}] {item['source']}: FAILED (Extraction returned None)")
            continue

        # Check scalar fields
        comp_ok = gt["company"].lower() in pred.company.lower()
        title_ok = gt["title"].lower() in pred.title.lower() or pred.title.lower() in gt["title"].lower()
        remote_ok = (pred.remote_ok == gt["remote_ok"])
        stipend_ok = gt["stipend"].lower() in (pred.stipend or "").lower()

        total_fields += 4
        correct_fields += sum([comp_ok, title_ok, remote_ok, stipend_ok])

        # Check skills precision & recall
        pred_skills = {s.lower().strip() for s in (pred.required_skills or [])}
        true_skills = gt["skills"]
        
        overlap = len(pred_skills.intersection(true_skills))
        precision = overlap / len(pred_skills) if pred_skills else 0
        recall = overlap / len(true_skills) if true_skills else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
        skill_f1_scores.append(f1)

        print(f"\n[{idx}] {item['source']}:")
        print(f"    • Company: {'✅' if comp_ok else '❌'} ({pred.company})")
        print(f"    • Title:   {'✅' if title_ok else '❌'} ({pred.title})")
        print(f"    • Remote:  {'✅' if remote_ok else '❌'} ({pred.remote_ok})")
        print(f"    • Stipend: {'✅' if stipend_ok else '❌'} ({pred.stipend})")
        print(f"    • Skills F1: {round(f1 * 100, 1)}% (Matched {overlap}/{len(true_skills)} skills)")

    field_acc = round((correct_fields / total_fields) * 100, 1)
    avg_f1 = round((sum(skill_f1_scores) / len(skill_f1_scores)) * 100, 1)

    print("\n" + "=" * 70)
    print("📊 EXTRACTION EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Field-Level Accuracy: {field_acc}%")
    print(f"Average Skills F1:    {avg_f1}%")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_eval()