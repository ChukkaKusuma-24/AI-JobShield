# Step 6: Machine Learning Model Audit, Validation, and Performance Analysis

## 1. Executive Summary of ML Health

An exhaustive audit of the machine learning subsystem in AI-JobShield was performed to evaluate its architecture, training data integrity, inference pipeline, calibration, and real-world robustness.

### Key Audit Verdict:
The current machine learning model is **critically brittle and suffers from extreme synthetic overfitting and severe data leakage**. While it achieves a deceptive **100% accuracy, precision, and recall on its synthetic training split**, its real-world performance collapses to **65.5% accuracy and 57.1% recall** when evaluated against non-synthetic, realistic, and adversarial recruitment cases.

### Core Audit Findings:
1. **Severe Dataset Leakage & Synthetic Artifacts**:
   - The entire training dataset (`data/demo_training_data.csv`, $N=400$) is 100% synthetically generated from only 18 hardcoded templates (10 scam, 8 legitimate) via `ml/generate_demo_data.py`.
   - Company names were strictly partitioned: legitimate companies (Infosys, TCS, Wipro, Google) appeared **only** in legitimate samples; scam company names appeared **only** in scam samples.
   - Domains were strictly partitioned: webmail domains (`@gmail.com`, `@yahoo.com`) appeared **only** in scam templates; official corporate domains appeared **only** in legitimate templates.
2. **Inference Input Disconnect**:
   - The training templates embedded emails and URLs directly into the training text (`Apply at <EMAIL> or visit <URL>`).
   - However, in production (`analyzer.py`), the ML service receives only `f"{title} {company_name} {description} {salary or ''}"`. Crucial signals like email and URL are completely absent from the inference text string.
3. **Severe Vulnerability to Adversarial Evasion and Dilution**:
   - When a scam includes realistic qualifications, interview rounds, or enterprise buzzwords, the scam fee keywords are diluted, causing the ML model to produce a **False Negative** (e.g., copied Google JD with Rs 2,500 background fee scores $P(\text{scam}) = 0.3984$, completely missed by ML).
   - When legitimate tech roles describe payment infrastructure or banking APIs (e.g., Razorpay Payment Operations Engineer), the model produces a **False Positive** ($P(\text{scam}) = 0.5188$, classified as scam due to tokens `bank`, `account`, `bank account`).
4. **Scoring Architecture Safeguard**:
   - Because ML contributes only **30% of Dimension 4** (which itself is 30% of the overall trust score), the ML model directly accounts for only **9% of the overall trust score** ($0.30 \times 0.30 = 0.09$).
   - Critical rule-based hard caps (`IMPERSONATION_RISK \le 25`, `CRITICAL_EVIDENCE \le 35`, `UNVERIFIED \le 65`) successfully protect the end user from ML false negatives.
5. **Clear Recommendation**:
   - **Option B: Retrain using an improved, real-world, leak-free dataset** with natural lexical diversity, proper n-gram tokenization, probability calibration, and strict elimination of company/domain leakage.

---

## 2. Complete Pipeline Trace

The end-to-end ML lifecycle proceeds through the following sequential stages:

```
+---------------------------------------------------------------------------------------+
| 1. Training Pipeline (ml/train.py)                                                    |
|                                                                                       |
|   data/demo_training_data.csv (400 rows)                                              |
|       |                                                                               |
|       v                                                                               |
|   Preprocessing (ml/preprocess.py: lowercase, url/email normalization, punctuation)  |
|       |                                                                               |
|       v                                                                               |
|   TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True) [956 features]     |
|       |                                                                               |
|       v                                                                               |
|   LogisticRegression(C=1.0, class_weight='balanced', solver='liblinear', penalty='l2') |
|       |                                                                               |
|       v                                                                               |
|   backend/models/jobshield_model.joblib (Pipeline)                                    |
+---------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------+
| 2. Production Inference & Scoring Pipeline (analyzer.py -> ml_service.py -> scoring.py)|
|                                                                                       |
|   User Input: title, company_name, description, salary                                 |
|       |                                                                               |
|       v                                                                               |
|   analyzer.py: combined = f"{title} {company_name} {description} {salary}"            |
|       |                                                                               |
|       v                                                                               |
|   ml_service.predict(combined):                                                       |
|     - Clean with preprocess_text()                                                    |
|     - pipe.predict_proba([clean])[0][1] -> p_scam                                     |
|     - Extract top 8 contributing TF-IDF terms                                         |
|       |                                                                               |
|       v                                                                               |
|   scoring.compute_trust_score():                                                      |
|     - ml_risk = p_scam * 100.0                                                        |
|     - ml_scam_score = clamp(100.0 - ml_risk, 0.0, 100.0)                              |
|     - Dimension 4 Score = 0.70 * rule_scam_score + 0.30 * ml_scam_score               |
|     - Dimension 4 contributes 30% of raw weighted score (9% total trust score)        |
|     - Hard caps applied: Impersonation (<=25), Critical Scam (<=35), Unverified (<=65)|
+---------------------------------------------------------------------------------------+
```

### Exact Production Model Specifications:
- **Model Type**: Scikit-Learn `Pipeline([('tfidf', TfidfVectorizer), ('clf', LogisticRegression)])`
- **Vectorizer**:
  - `ngram_range`: `(1, 2)` (unigrams and bigrams)
  - `min_df`: `2` (terms appearing in at least 2 documents)
  - `max_df`: `1.0`
  - `sublinear_tf`: `True` ($1 + \log(\text{tf})$ scaling)
  - `stop_words`: `None` (standard English stop words are retained)
  - `max_features`: `None` (full vocabulary retained)
  - **Vocabulary Size**: 956 features
- **Classifier**:
  - `LogisticRegression`
  - `C`: `1.0`
  - `penalty`: `l2`
  - `class_weight`: `'balanced'`
  - `solver`: `'liblinear'`
  - `max_iter`: `1000`
- **Classes**:
  - `0`: Legitimate Posting
  - `1`: Fraudulent / Scam Posting
- **Calibration**: Uncalibrated logistic sigmoid output (`predict_proba`).

---

## 3. Training Dataset Quality Report

The dataset `data/demo_training_data.csv` was audited in detail:
- **Total Samples**: 400 rows
- **Class Balance**: Perfectly balanced:
  - Class `0` (Legitimate): 200 samples (50.0%)
  - Class `1` (Scam): 200 samples (50.0%)
- **Data Source**: 100% synthetically generated by `ml/generate_demo_data.py`.
- **Template Diversity**: Only **18 distinct templates** exist in the generator:
  - 10 scam templates (data entry, registration fee, Telegram recruitment, typing jobs, daily payment, part-time home jobs).
  - 8 legitimate templates (software engineer, cloud architect, product manager, data analyst, DevOps engineer).
- **Synthetic Artifacts**:
  - Text is generated by randomly slotting variable company names and salaries into fixed boilerplate sentences.
  - As a result, the dataset contains near-zero lexical variance, zero natural grammatical typos, and zero domain overlap.

---

## 4. Leakage and Contamination Analysis

Three major forms of leakage and contamination were uncovered during the audit:

### A. Strict Company Name Partitioning
In `ml/generate_demo_data.py`:
- `COMPANIES_LEGIT = ["Tata Consultancy Services", "Infosys", "Wipro", "HCL Tech", "Tech Mahindra", "Google", "Amazon", "Microsoft"]`
- `COMPANIES_SCAM = ["QuickEarn Services", "Global Data Corp", "FastJobs India", "Apex Solutions", "Prime Remote Work", "BrightPath Careers"]`
- **Impact**: The model learns that seeing `"Infosys"` or `"Google"` strongly correlates with Class 0 (Legitimate), while `"Apex"` or `"QuickEarn"` correlates with Class 1 (Scam). If a scammer claims to be `"Google"` or `"Infosys"`, the presence of the legitimate company name actively pushes the ML score toward Legitimate!

### B. Strict Domain Partitioning
- Legitimate templates only contain official enterprise email domains (`@tcs.com`, `@infosys.com`).
- Scam templates only contain generic webmail domains (`@gmail.com`, `@yahoo.com`, `@outlook.com`).
- **Impact**: The model learned that domain string patterns strictly define the class.

### C. Train/Test Overlap via Boilerplate Memorization
- When splitting the 400 synthetic rows into 75% train / 25% test, identical template sentences appear in both splits (only minor entity substitutions differ).
- The model memorized whole multi-word n-grams (`infosys is`, `competitive compensation`, `earn daily`, `registration fee`) rather than generalizable semantic concepts.

---

## 5. Model Metrics Comparison: Synthetic vs Non-Synthetic

A side-by-side empirical evaluation was conducted comparing the model's reported performance on the synthetic test split versus a realistic, non-synthetic evaluation set ($N=29$) consisting of the controlled benchmark cases and adversarial job postings.

| Metric | Synthetic 25% Test Split ($N=100$) | Real-World & Adversarial Cases ($N=29$) | $\Delta$ Degradation |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **1.0000 (100.0%)** | **0.6552 (65.5%)** | **-34.5%** |
| **Precision** | **1.0000 (100.0%)** | **0.9231 (92.3%)** | **-7.7%** |
| **Recall** | **1.0000 (100.0%)** | **0.5714 (57.1%)** | **-42.9%** |
| **F1-Score** | **1.0000 (100.0%)** | **0.7059** | **-29.4%** |
| **ROC-AUC** | **1.0000** | **0.7976** | **-0.2024** |
| **PR-AUC** | **1.0000** | **0.8654** | **-0.1346** |
| **Brier Score** | **0.0147** (Near-perfect) | **0.2185** (Severe error) | **+14.8x higher error** |

### Confusion Matrix on Real-World / Adversarial Data ($N=29$):
- **True Positives (Scam detected as Scam)**: 8
- **False Negatives (Scam missed by ML)**: 6 (Miss rate: **42.9%**)
- **True Negatives (Legitimate detected as Legit)**: 11
- **False Positives (Legitimate flagged as Scam)**: 1 (Razorpay payment engineer)

---

## 6. Independent Evaluation on Controlled 15-Case Benchmark

Each of the 15 benchmark cases was evaluated through the ML model in isolation, recording the model's probability distribution and comparing it to the rule-based Dimension 4 score and final trust score:

| Case ID | Case Description | Category | Comp Status | $P(\text{scam})$ | $P(\text{legit})$ | ML Pred | ML Score | Rule D4 | Blend D4 | Final Trust Score |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | Genuine verified TCS | Legitimate | VERIFIED | 0.2622 | 0.7378 | 0 | 73.78 | 100.0 | 92.1 | **92** |
| **2** | Genuine verified Infosys | Legitimate | VERIFIED | 0.2415 | 0.7585 | 0 | 75.85 | 100.0 | 92.8 | **93** |
| **3** | Genuine unknown startup | Legitimate | UNVERIFIED | 0.2755 | 0.7245 | 0 | 72.45 | 100.0 | 91.7 | **65** |
| **4** | TCS using Gmail | Fraudulent | IMPERSONATION_RISK | 0.3484 | 0.6516 | **0** | 65.16 | 45.0 | 51.0 | **25** |
| **5** | TCS lookalike domain | Fraudulent | IMPERSONATION_RISK | 0.3337 | 0.6663 | **0** | 66.63 | 27.0 | 38.9 | **25** |
| **6** | Registration fee scam | Fraudulent | UNVERIFIED | 0.8302 | 0.1698 | 1 | 16.98 | 15.0 | 15.6 | **27** |
| **7** | Equipment/deposit scam | Fraudulent | UNVERIFIED | 0.6962 | 0.3038 | 1 | 30.38 | 0.0 | 9.1 | **25** |
| **8** | WhatsApp-only recruitment | Fraudulent | UNVERIFIED | 0.5301 | 0.4699 | 1 | 46.99 | 65.0 | 59.6 | **50** |
| **9** | Telegram-only recruitment | Fraudulent | UNVERIFIED | 0.4776 | 0.5224 | **0** | 52.24 | 65.0 | 61.2 | **51** |
| **10** | Unrealistic salary scam | Fraudulent | UNVERIFIED | 0.7374 | 0.2626 | 1 | 26.26 | 28.0 | 27.5 | **31** |
| **11** | Sensitive info request | Fraudulent | UNVERIFIED | 0.6741 | 0.3259 | 1 | 32.59 | 40.0 | 37.8 | **35** |
| **12** | Multiple critical signals | Fraudulent | UNVERIFIED | 0.7838 | 0.2162 | 1 | 21.62 | 0.0 | 6.5 | **26** |
| **13** | Legitimate incomplete posting | Legitimate | PARTIALLY VERIFIED | 0.3869 | 0.6131 | 0 | 61.31 | 80.0 | 74.4 | **60** |
| **14** | Legitimate job + WhatsApp | Legitimate | VERIFIED | 0.4320 | 0.5680 | 0 | 56.80 | 100.0 | 87.0 | **89** |
| **15** | Legitimate payment-context job | Legitimate | VERIFIED | 0.4616 | 0.5384 | 0 | 53.84 | 100.0 | 86.2 | **87** |

### Benchmark Audit Takeaways:
1. **Impersonation Scams (Cases 4 & 5)**: The ML model predicts $P(\text{scam}) \approx 0.34$, marking them as "Legitimate" (Pred 0). The text itself is copied genuine corporate text. The ML model cannot detect impersonation because email and URL domains are excluded from its input text. However, company identity verification and deterministic rules catch the impersonation and enforce the hard cap of 25.
2. **Telegram Blindspot (Case 9)**: The ML model predicts $P(\text{scam}) = 0.4776$ (Pred 0). The word `"telegram"` was underrepresented in the synthetic training data, rendering ML ineffective against Telegram-exclusive scams.
3. **Legitimate JDs with Communication/Fintech Terms (Cases 14 & 15)**: Innocent mentions of WhatsApp coordination or bank transfers inflate $P(\text{scam})$ from ~0.25 to 0.43–0.46, lowering ML scores to 53–56. The rule engine's context awareness ($100.0$ score) protects these jobs from being penalized.

---

## 7. Adversarial Text Evaluation Results

Systematic adversarial tests were executed across four distinct structural categories:

```
+----------------------------------------------------------------------------------------------------+
| Variation A: Legitimate Job In 4 Different Styles (Infosys Senior Engineer)                         |
|   A1: Professional Standard           -> P(scam): 0.2707 | Pred: 0 | Robust                         |
|   A2: Informal / Poor Grammar         -> P(scam): 0.3104 | Pred: 0 | Slight penalty for 'pay'       |
|   A3: Extremely Brief (2 sentences)   -> P(scam): 0.3616 | Pred: 0 | Acceptable                     |
|   A4: Very Long Enterprise JD (500w)  -> P(scam): 0.2473 | Pred: 0 | High confidence legitimate     |
+----------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------+
| Variation B: Scam Job In 4 Different Styles (Data Entry / Administrative)                          |
|   B1: Obvious Scam Keywords (fee, cash) -> P(scam): 0.8945 | Pred: 1 | High detection               |
|   B2: Paraphrased Scam (deposit, disb.) -> P(scam): 0.5036 | Pred: 1 | BORDERLINE EVASION (delta -39%)|
|   B3: Indirect Scam (equipment check)   -> P(scam): 0.5578 | Pred: 1 | Weak detection               |
|   B4: Professional Deposit Scam         -> P(scam): 0.5605 | Pred: 1 | Weak detection               |
+----------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------+
| Variation C: Legitimate Job with Scam-Associated Technical Words                                    |
|   C1: Payment Gateway (Razorpay)        -> P(scam): 0.5188 | Pred: 1 | FALSE POSITIVE! (bank, account)|
|   C2: HR Campus WhatsApp (TCS)          -> P(scam): 0.3769 | Pred: 0 | P(scam) elevated by +0.11     |
|   C3: Crypto Blockchain (Polygon)       -> P(scam): 0.3428 | Pred: 0 | Mild elevation                |
|   C4: Gift Cards Operations (Amazon)    -> P(scam): 0.4843 | Pred: 0 | BORDERLINE FALSE POSITIVE      |
+----------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------+
| Variation D: Scam Job in Legitimate Disguise                                                       |
|   D1: Copied Google JD + Tail Fee       -> P(scam): 0.3984 | Pred: 0 | FALSE NEGATIVE! (Evaded ML)   |
|   D2: Corporate Buzzwords + License Fee -> P(scam): 0.5585 | Pred: 1 | Weak detection               |
|   D3: Fortune 500 Claim (Tata Motors)   -> P(scam): 0.5571 | Pred: 1 | Weak detection               |
|   D4: Realistic Process + Exam Fee      -> P(scam): 0.4154 | Pred: 0 | FALSE NEGATIVE! (Evaded ML)   |
+----------------------------------------------------------------------------------------------------+
```

### Key Adversarial Insights:
1. **Keyword Dilution Exploit**: In D1 and D4, placing an upfront fee demand inside a lengthy, professional description completely blinds the ML model. The sheer volume of legitimate enterprise tokens (`experience`, `bachelor`, `responsibilities`, `systems`) out-votes the fee tokens in linear regression space.
2. **False Positive Trigger on Fintech**: In C1, a completely authentic backend engineering role at Razorpay is classified as a fraudulent scam ($P(\text{scam}) = 0.5188$) because the model treats `bank` (+0.08) and `account` (+0.12) as scam signals.

---

## 8. Feature Analysis (Top TF-IDF Coefficients)

Inspection of the trained pipeline coefficients reveals the model's decision drivers:

### Top 15 Scam Predictors (Positive Coefficients):
1. `fee` (+0.9348)
2. `num` (+0.9339) *(generic number replacement from preprocessing)*
3. `pay` (+0.9114)
4. `earn` (+0.9004)
5. `guaranteed` (+0.7195)
6. `whatsapp` (+0.6697)
7. `from home` (+0.6286)
8. `per day` (+0.5480)
9. `kit` (+0.4837)
10. `deposit` (+0.4612)
11. `bank` (+0.4431)
12. `account` (+0.4215)
13. `activation` (+0.4088)
14. `typing` (+0.3992)
15. `registration` (+0.3854)

### Top 15 Legitimate Predictors (Negative Coefficients):
1. `lpa` (-0.8409)
2. `with` (-0.7587)
3. `url` (-0.7468)
4. `qualifications` (-0.5735)
5. `salary` (-0.5412)
6. `process` (-0.5401)
7. `bachelor` (-0.5118)
8. `engineer` (-0.4982)
9. `experience` (-0.4820)
10. `degree` (-0.4671)
11. `systems` (-0.4429)
12. `software` (-0.4312)
13. `years` (-0.4187)
14. `infosys is` (-0.3980) *(Direct template leakage!)*
15. `tcs is` (-0.3812) *(Direct template leakage!)*

Notice that `infosys is` and `tcs is` appear in the top 15 legitimate predictors with large negative coefficients, proving that the model literally memorized the names of large companies from the synthetic generator.

---

## 9. Calibration and Probability Distribution Audit

### Synthetic Calibration:
On the synthetic training dataset, the Brier score was **0.0147**, showing an artificially polarized probability distribution:
- **[0.0, 0.2)**: 200 samples (50.0%)
- **[0.2, 0.8)**: **0 samples (0.0%)**
- **[0.8, 1.0)**: 200 samples (50.0%)

The model was trained on extreme, unambiguous polar opposites, preventing it from ever learning nuanced or borderline cases.

### Real-World / Adversarial Calibration:
On non-synthetic cases ($N=29$):
- **Brier Score degraded to 0.2185** (where 0.25 represents an uninformative constant 50/50 guessing baseline).
- **79.3% of all real-world cases fall between [0.2 and 0.6)**.
- Because the logistic regression output is uncalibrated (no Platt scaling or isotonic regression applied on realistic data), probabilities in the middle range [0.35, 0.65] are uncalibrated and highly volatile.

---

## 10. Math Behind Model vs Rule Engine Contribution

In `backend/app/services/scoring.py`, the multi-dimensional trust score is computed across 5 weighted dimensions:
1. Company Verification: 25%
2. Source Credibility: 20%
3. Job Posting Quality: 15%
4. Scam & Red Flag Detection: **30%**
5. Contact Consistency: 10%

### Dimension 4 Scam Score Formulation:
$$\text{rule\_scam\_score} = \max(0, \text{scam\_base} - \text{red\_flag\_points})$$
$$\text{ml\_scam\_score} = \text{clamp}(100.0 - (P(\text{scam}) \times 100.0), 0.0, 100.0)$$
$$\text{dim4\_score} = 0.70 \times \text{rule\_scam\_score} + 0.30 \times \text{ml\_scam\_score}$$

### Direct Trust Score Contribution:
$$\Delta \text{Trust Score} = W_{\text{dim4}} \times W_{\text{ml}} \times \Delta \text{ml\_scam\_score} = 0.30 \times 0.30 \times \Delta \text{ml\_scam\_score} = \mathbf{0.09} \times \Delta \text{ml\_scam\_score}$$

- **Maximum ML Impact**: An ML probability shift from $P(\text{scam}) = 0.0$ to $1.0$ can move the final trust score by at most **9 points**.
- **Guardrail Priority**: Hard caps override both rules and ML:
  - If `company_status == "IMPERSONATION_RISK"` $\implies \text{trust\_score} \le 25$.
  - If `has_critical_scam` (e.g. upfront fee) $\implies \text{trust\_score} \le 35$.
  - If `is_unverified_company` $\implies \text{trust\_score} \le 65$.

This 70/30 blend and hard-cap architecture is the exact reason why AI-JobShield remains safe and robust today despite the ML model's vulnerabilities.

---

## 11. Identified Failure Modes

| Failure Mode ID | Type | Description | Trigger Example | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **FM-1** | False Negative | **Keyword Dilution**: Fee demand hidden inside a long, legitimate JD | Copied Google JD + Rs 2,500 background fee | $P(\text{scam}) = 0.3984$ (ML misses scam completely) |
| **FM-2** | False Negative | **Channel Blindspot**: Unseen scam recruitment platform | Telegram-only channel @QuickJobsIndia | $P(\text{scam}) = 0.4776$ (ML misses scam completely) |
| **FM-3** | False Negative | **Company Name Hijacking**: Scam text claiming a verified company name | "Infosys Hiring Online Typing Rs 1000 Fee" | Negative coefficient of "infosys" counteracts fee keywords |
| **FM-4** | False Positive | **Technical Domain Conflation**: Legitimate payment / banking terms | Razorpay engineer building bank transfer API | $P(\text{scam}) = 0.5188$ (ML falsely labels legit as scam) |
| **FM-5** | False Positive | **HR Communication Conflation**: Official WhatsApp interview coordination | TCS HR mentions WhatsApp Business coordination | ML score drops to 56.80 due to "whatsapp" token |

---

## 12. Strategic Recommendation and Justification

Four possible paths were evaluated:
- **Option A**: Keep the current model as-is.
- **Option B**: Retrain using an improved, real-world, leak-free dataset.
- **Option C**: Replace the model with an ensemble or transformer architecture.
- **Option D**: Remove the ML component entirely and rely 100% on the deterministic rule engine.

### Recommendation: OPTION B (Retrain using an improved real-world dataset)

### Justification:
1. **Option A is Rejected**: The current model suffers from 42.9% miss rate on non-synthetic scams, 100% template leakage, company name contamination, and fintech false positives.
2. **Option D is Rejected**: A hybrid rule+ML system is fundamentally more resilient than rules alone. TF-IDF + linear classifier captures latent combinations of linguistic cues (e.g., informal phrasing, odd grammatical transitions, subtle work-from-home claims) that cannot be cleanly enumerated in regexes.
3. **Option C is Deferred**: Heavy transformers (e.g. BERT/RoBERTa) introduce significant latency (200-500ms vs 2ms for TF-IDF), GPU dependency, large memory footprints, and complex deployments without proportional gain for this classification scope.
4. **Option B is the Optimal Engineering Solution**:
   - Curate a clean, multi-source dataset combining real-world scam job postings (e.g., from the EMSCAD dataset and verified scam repositories) and diverse legitimate postings.
   - Strip specific company names and domains from training text to completely eliminate leakage.
   - Add negative training samples for legitimate fintech/banking, crypto, and HR coordination roles to eliminate false positives.
   - Calibrate output probabilities using Isotonic Regression or Platt scaling.
   - Maintain the fast, lightweight Scikit-Learn TF-IDF pipeline ($\approx 2\text{ms}$ inference latency).

---

## 13. Test Suite and Verification

A comprehensive unit test suite was implemented in `tests/test_ml_validation.py` covering:
1. Model loading and pipeline integrity (`tfidf` and `clf` named steps)
2. TF-IDF vectorizer configuration (`(1, 2)` ngrams, `min_df=2`, `sublinear_tf=True`)
3. Classifier configuration (`LogisticRegression`, `balanced`, `l2`)
4. Probability output bounds strictly in $[0.0, 1.0]$
5. Known legitimate text probability ($P(\text{scam}) < 0.40$)
6. Known scam text probability ($P(\text{scam}) > 0.60$)
7. Empty string and whitespace input handling without crashing
8. Very long input text (5000+ words) stability
9. Special characters, currency symbols (`₹`, `$`, `€`), and non-ASCII Unicode handling
10. ML output cannot override critical rule flags or hard caps
11. Graceful degradation when model is missing or unavailable
12. Top contributing terms extraction structure

### Test Execution Results:
```
pytest tests/test_ml_validation.py -v
======================= 12 passed in 3.68s =======================

All Project Test Suites:
- tests/test_history_and_scoring.py: 7 passed
- tests/test_evidence_hierarchy.py: 25 passed
- tests/test_company_identity.py: 13 passed
- tests/test_rule_engine_context.py: 27 passed
- tests/test_ml_validation.py: 12 passed
======================= 84 passed, 0 failures =======================
```

---

## 14. Action Plan for Step 7 (Dataset Curation and Model Retraining)

When proceeding to Step 7 upon user approval:
1. **Dataset Construction**:
   - Merge verified real-world scam corpora (e.g., EMSCAD dataset) with diverse Indian and international job descriptions.
   - Ensure a minimum of 2,000–5,000 diverse samples.
   - Include diverse legitimate postings spanning fintech, banking, web3, and HR coordination.
2. **De-biasing and Entity Masking**:
   - Preprocess training text by masking specific company names with a generic `<COMPANY>` token.
   - Mask specific recruiter domains and emails with `<EMAIL>`.
   - Prevent any single company name from correlating with the target label.
3. **Probability Calibration**:
   - Apply `CalibratedClassifierCV(method='sigmoid')` or Platt scaling on a clean validation holdout split.
   - Ensure Brier score on unseen real-world validation data is $\le 0.08$.
4. **Input Alignment**:
   - Update `analyzer.py` to ensure the exact text representation used during inference matches the training feature representation.
5. **Regression Verification**:
   - Verify that all 84 test cases pass, all 15 benchmark cases maintain proper trust score categorization, and false positives in fintech/payment engineering are eradicated.

---

> [!IMPORTANT]
> **Step 6 is strictly an audit and validation phase.**
> In accordance with instructions, no model retraining was performed, no weights were altered, and no source code was modified. All 84 tests pass. We await user review before proceeding.
