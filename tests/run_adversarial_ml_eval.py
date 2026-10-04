"""Adversarial evaluation script for AI-JobShield ML model (Step 6)."""
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services import ml_service

ml_service.load_model()

variations = {
    # Variation A: Same legitimate job in 4 styles
    "A1_legit_professional": {
        "group": "A: Legitimate Styles",
        "title": "Senior Software Engineer",
        "company": "Infosys",
        "text": "Infosys is seeking a Senior Software Engineer with 5+ years of experience in Python and cloud microservices. Candidates must possess a Bachelor's degree in Computer Science, strong algorithms knowledge, and experience with distributed architectures. Competitive compensation package with health benefits and retirement savings.",
        "salary": "15-20 LPA",
    },
    "A2_legit_informal_poor_grammar": {
        "group": "A: Legitimate Styles",
        "title": "senior software engineer",
        "company": "Infosys",
        "text": "hey we need python dev fast for our cloud team. must have 5 yr exp and know cs basics and cloud stuff. gud pay with health insurance and retirement plans. apply now if u got the skills.",
        "salary": "15-20 LPA",
    },
    "A3_legit_brief": {
        "group": "A: Legitimate Styles",
        "title": "Software Engineer",
        "company": "Infosys",
        "text": "Hiring Python software engineer with 5 years experience for cloud systems. Bachelor degree required.",
        "salary": "Competitive",
    },
    "A4_legit_long_enterprise": {
        "group": "A: Legitimate Styles",
        "title": "Senior Cloud Infrastructure Engineer",
        "company": "Infosys",
        "text": "Infosys is a global leader in next-generation digital services and consulting. We enable clients in more than 50 countries to navigate their digital transformation. With over four decades of experience in managing the systems and workings of global enterprises, we expertly steer our clients through their digital journey. We do it by enabling the enterprise with an AI-powered core that helps prioritize the execution of change. We also empower the business with agile digital at scale to deliver unprecedented levels of performance and customer delight. Responsibilities: Architect and implement scalable cloud infrastructure on AWS and Azure. Design high-availability microservices architectures adhering to enterprise security governance frameworks. Collaborate with cross-functional teams including site reliability engineers, product managers, and solution architects. Qualifications: Bachelor of Engineering or Master of Science in Computer Science or related engineering discipline. Minimum 6 years of experience in enterprise backend development with Python, Go, or Java. Extensive knowledge of Kubernetes, Docker, Terraform, CI/CD pipelines, and automated monitoring with Prometheus and Grafana. Excellent communication skills, analytical problem solving, and proven track record of mentoring junior technical staff. Salary compensation: 18-25 LPA plus performance incentives.",
        "salary": "18-25 LPA",
    },

    # Variation B: Same scam in 4 styles
    "B1_scam_obvious": {
        "group": "B: Scam Variations",
        "title": "Online Data Entry Operator",
        "company": "Apex Global Services",
        "text": "Earn 5000 to 10000 daily working from home! Simple typing and form filling work. No experience needed. Immediate joining guaranteed. Registration fee of Rs 1500 required for account activation and software kit. Contact HR on WhatsApp now to start earning today!",
        "salary": "Rs 10,000 per day",
    },
    "B2_scam_paraphrased": {
        "group": "B: Scam Variations",
        "title": "Remote Records Specialist",
        "company": "Apex Global Services",
        "text": "Flexible remote position assisting with digital record management. Earn attractive compensation distributed daily. Prior background not mandatory. Mandatory training deposit of Rs 1500 to secure documentation package and dedicated portal access. Reach our recruitment coordinator via secure mobile messaging application.",
        "salary": "Attractive daily compensation",
    },
    "B3_scam_indirect_equipment": {
        "group": "B: Scam Variations",
        "title": "Administrative Assistant Remote",
        "company": "Apex Global Services",
        "text": "We are seeking a reliable Remote Administrative Assistant to support our operations. You will manage scheduling and correspondence. We will mail you a corporate reimbursement check to purchase required home office equipment from our certified vendor. Deposit the check in your personal bank account and transfer vendor fees immediately.",
        "salary": "$35/hour",
    },
    "B4_scam_professional_deposit": {
        "group": "B: Scam Variations",
        "title": "Management Trainee Program",
        "company": "Apex Global Services",
        "text": "Apex Global Services announces its 2026 Executive Management Trainee intake. Selected candidates undergo comprehensive corporate leadership training across operations, business development, and supply chain. Candidates must submit a 100% refundable onboarding security deposit of Rs 3,500 prior to background verification and laptop dispatch. Deposit is refunded with the first month salary.",
        "salary": "8 LPA",
    },

    # Variation C: Legitimate job with scam-associated words
    "C1_legit_payment_gateway": {
        "group": "C: Legitimate with Sensitive Words",
        "title": "Payment Operations Engineer",
        "company": "Razorpay",
        "text": "Razorpay is hiring a Backend Engineer to build payment infrastructure. You will optimize money transfer APIs, secure wire transfers, automate bank account verification, and handle credit card transactions at scale. Experience with high-throughput banking integration required.",
        "salary": "25-35 LPA",
    },
    "C2_legit_hr_whatsapp": {
        "group": "C: Legitimate with Sensitive Words",
        "title": "Campus Recruitment Specialist",
        "company": "Tata Consultancy Services",
        "text": "TCS is seeking an HR Recruitment Specialist to manage nationwide campus hiring drives. The specialist will coordinate candidate communications via official email, SMS portal, and official verified WhatsApp Business account for interview scheduling and venue directions.",
        "salary": "6-9 LPA",
    },
    "C3_legit_crypto_blockchain": {
        "group": "C: Legitimate with Sensitive Words",
        "title": "Blockchain Protocol Developer",
        "company": "Polygon",
        "text": "Polygon Labs is looking for a Protocol Engineer. The role involves designing smart contracts, securing decentralized crypto wallet custody solutions, analyzing blockchain consensus mechanisms, and testing token disbursement smart contracts on testnet.",
        "salary": "30-50 LPA",
    },
    "C4_legit_gift_cards": {
        "group": "C: Legitimate with Sensitive Words",
        "title": "Merchant Partnerships Operations Manager",
        "company": "Amazon",
        "text": "Amazon India is hiring an Operations Manager for Gift Cards and Corporate Rewards. Responsibilities include managing voucher inventory distribution, auditing bulk corporate gift card procurement, reconciling merchant payouts, and preventing promo code abuse.",
        "salary": "16-22 LPA",
    },

    # Variation D: Scam job with legitimate-sounding text
    "D1_scam_copied_jd_with_fee_tail": {
        "group": "D: Scam in Legit Disguise",
        "title": "Senior Software Engineer",
        "company": "Google",
        "text": "Google is seeking a Senior Software Engineer with 5+ years of experience in distributed systems and cloud infrastructure. Bachelor's degree in CS required. Key responsibilities include designing scalable microservices. Selected candidates must pay a mandatory Rs 2,500 background screening processing fee to our accredited third-party verification partner prior to final interview.",
        "salary": "45-60 LPA",
    },
    "D2_scam_corporate_buzzwords": {
        "group": "D: Scam in Legit Disguise",
        "title": "Global Strategic Operations Associate",
        "company": "OmniCorp Global",
        "text": "Drive cross-functional enterprise synergy and optimize holistic paradigm shifts across multinational stakeholder ecosystems. Leverage cutting-edge analytics to maximize operational leverage. Onboarding requires a provisional technology licensing fee of Rs 4,999 reimbursable upon corporate workstation deployment.",
        "salary": "12 LPA",
    },
    "D3_scam_fortune_500_claim": {
        "group": "D: Scam in Legit Disguise",
        "title": "Regional Logistics Coordinator",
        "company": "Tata Motors",
        "text": "Tata Motors Fleet Management Division invites applications for Regional Logistics Coordinators. Coordinate supply chain corridors across western zone hubs. Candidates must wire an initial security clearance deposit of Rs 2,000 to our logistics vendor account to reserve their recruitment examination slot.",
        "salary": "7 LPA",
    },
    "D4_scam_realistic_process_then_fee": {
        "group": "D: Scam in Legit Disguise",
        "title": "Graduate Business Analyst",
        "company": "Apex Global Solutions",
        "text": "Round 1: Online Aptitude Assessment. Round 2: Technical Case Study. Round 3: Panel Interview with Practice Leads. Candidates must have a B.Tech or MBA with minimum 65% aggregate. To schedule your Round 1 testing portal slot, a non-refundable examination proctoring fee of Rs 950 must be paid via UPI to the assessment proctor.",
        "salary": "6.5 LPA",
    },
}

print(f"{'Key':<32} | {'Group':<32} | {'P(scam)':<8} | {'P(legit)':<8} | {'Pred':<4} | Top Contributing Terms")
print("-" * 120)

for key, var in variations.items():
    combined = f"{var['title']} {var['company']} {var['text']} {var.get('salary', '')}"
    res = ml_service.predict(combined)
    p_scam = res["scam_probability"]
    p_legit = 1.0 - p_scam if p_scam is not None else None
    pred = 1 if p_scam >= 0.5 else 0
    top_t = ", ".join([f"{t['term']} ({t['weight']:+.2f})" for t in res.get("top_terms", [])[:4]])
    print(f"{key:<32} | {var['group']:<32} | {p_scam:<8.4f} | {p_legit:<8.4f} | {pred:<4} | {top_t}")
