import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.job_content_validator import validate_job_related_text as v

cases = {
    "A_codeforces": (
        "Contest status Problem A Accepted C++20 Memory 16MB Time 78ms "
        "Codeforces Round 900 Div.2 Standing rating problemset Wrong Answer Time Limit"
    ),
    "B_shopping": (
        "Your cart Order total Payment delivery Add to cart Checkout Pay with UPI GPay"
    ),
    "C_job": (
        "Software Engineer Job Opening at TechNova. Required skills: Python, SQL. "
        "Responsibilities include API design. Qualifications: 2 years of experience. "
        "Salary 8 LPA. Apply now via careers@technova.com. Interview process: technical round, HR round."
    ),
    "D_recruiter": (
        "Hello candidate, we are hiring for a Software Developer position. "
        "Please send your resume. Recruiter from Talent Acquisition. Full-time job opportunity."
    ),
    "E_resume": (
        "John Doe Resume Curriculum Vitae Education B.Tech Skills Python React "
        "Work Experience Software Intern Projects Portfolio Professional Experience"
    ),
}

def test_job_content_validator():
    failed = False
    expect = {
        "A_codeforces": False,
        "B_shopping": False,
        "C_job": True,
        "D_recruiter": True,
        "E_resume": True,
    }
    for name, text in cases.items():
        r = v(text)
        ok = r["valid"] == expect[name]
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed = True
        sigs = [s["id"] for s in r["signals"][:10]]
        print(
            f"{status} {name}: valid={r['valid']} (want {expect[name]}) "
            f"score={r['score']} anti={r['anti_score']} signals={sigs}"
        )
    assert not failed, "Job content validator test cases failed"


if __name__ == "__main__":
    test_job_content_validator()
