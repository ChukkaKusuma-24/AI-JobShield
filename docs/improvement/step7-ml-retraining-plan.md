# Step 7: Machine Learning Retraining Plan & Data Architecture

## 1. Audit of Available Data

A comprehensive inspection of all data assets across the AI-JobShield repository was conducted:

### Existing Datasets and Data Files
| File Path | Rows / Items | Columns / Format | Content & Provenance | Leakage / Risk Factors |
| :--- | :---: | :---: | :--- | :--- |
| `data/demo_training_data.csv` | 400 | `text, label, source` | 100% synthetic from `ml/generate_demo_data.py`. Exactly 200 Scam (50%), 200 Legit (50%). | **Severe Contamination**: Company names strictly partitioned (Infosys/TCS only in Legit; QuickEarn/Apex only in Scam). Emails/URLs present in text. 12 duplicate rows. |
| `data/verified_companies.json` | 25 | JSON objects | Registry of verified enterprise employers with verified domains, aliases, acronyms, and TLD rules. | Clean reference registry. |
| `data/free_email_domains.json` | 32 | JSON array | List of public webmail providers (gmail.com, yahoo.com, hotmail.com, etc.). | Clean reference rule list. |
| `data/suspicious_tlds.json` | 27 | JSON array | List of suspicious/cheap top-level domains (.top, .xyz, .click, .loan, etc.). | Clean reference rule list. |
| `data/known_scam_keywords.json` | 15 | JSON array | Curated keyword phrases commonly observed in Indian job fraud. | Reference rule list. |
| `tests/run_benchmark_step4.py` | 15 | Python dicts | The controlled 15-case benchmark covering genuine TCS, Infosys, unverified startup, impersonation, fee scams, and fintech. | Clean evaluation benchmark. |
| `tests/run_adversarial_ml_eval.py` | 16 | Python dicts | 16 adversarial text variants across 4 categories (A: styles, B: scam variants, C: sensitive words, D: disguised scams). | Clean evaluation benchmark. |
| `tests/test_rule_engine_context.py`| 27 | Pytest functions | 27 contextual test cases for fintech, crypto, WhatsApp, urgency, and salary. | Clean regression suite. |

### Data Audit Findings
1. **Single Training Dataset**: `data/demo_training_data.csv` is currently the **only** dataset available for model training.
2. **Zero Real-World Training Data**: The existing model has never been exposed to authentic, unscripted job descriptions or diverse recruitment communications.
3. **Severe Entity Correlation**: 100% of legitimate rows in `demo_training_data.csv` contain known large IT company names, while scam rows contain artificial spam business names.
4. **Conclusion**: Production retraining cannot succeed using the current 400 synthetic rows. An expanded, leak-free, multi-source dataset is mandatory.

---

## 2. Target Training Dataset Definition

To provide genuine generalization and robustness against adversarial evasion, the target training dataset is defined as follows:

### Target Scale & Class Distribution
- **Target Size**: **3,000 to 4,000 balanced rows**.
- **Class Balance**: 50% Legitimate (`label = 0`), 50% Scam (`label = 1`).
- **Diversity Breadth**: Spanning 8 major industry verticals, entry-level to director-level seniorities, and global as well as Indian recruitment contexts.

### Explicit Category Composition
```
+----------------------------------------------------------------------------------------------------+
| CLASS 1: SCAM & FRAUDULENT RECRUITMENT (1,500 - 2,000 samples)                                     |
+----------------------------------------------------------------------------------------------------+
| 1. Upfront Application / Registration Fee Scams      (250 samples)                                 |
| 2. Mandatory Refundable Security / Training Deposits (200 samples)                                 |
| 3. Fake Check & Equipment Re-shipping Scams          (150 samples)                                 |
| 4. Task / Daily Commission / Like-and-Earn Scams     (250 samples)                                 |
| 5. Crypto Investment & Wallet Funding Task Scams     (150 samples)                                 |
| 6. Direct Offer / Instant Selection Without Interview(200 samples)                                 |
| 7. Banking Credential Phishing (OTP, PIN, Password)  (150 samples)                                 |
| 8. Premature Identity Harvesting (Aadhaar/PAN/Pass.) (150 samples)                                 |
| 9. Exorbitant Salary for Low-Skill Work (Data Entry) (250 samples)                                 |
| 10. Coercive Urgency & Threat of Disqualification   (150 samples)                                 |
| 11. Keyword-Diluted Disguised Enterprise Scams       (100 samples)                                 |
+----------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------+
| CLASS 0: LEGITIMATE JOB POSTINGS (1,500 - 2,000 samples)                                           |
+----------------------------------------------------------------------------------------------------+
| 1. Enterprise IT, Software, & Cloud Engineering      (400 samples)                                 |
| 2. Early-Stage Startup Roles (Lean / Brief JDs)      (250 samples)                                 |
| 3. Customer Operations, BPO, & Technical Support     (200 samples)                                 |
| 4. Corporate Sales, Marketing, & Business Analytics  (200 samples)                                 |
| 5. Authentic Remote & Work-from-Home Positions       (200 samples)                                 |
| 6. HARD NEGATIVE: Fintech & Payment Operations       (150 samples)                                 |
| 7. HARD NEGATIVE: Banking & Ledger Reconciliations   (100 samples)                                 |
| 8. HARD NEGATIVE: Crypto & Blockchain Infrastructure (100 samples)                                 |
| 9. HARD NEGATIVE: Payroll & Bank Account Credits     (100 samples)                                 |
| 10. HARD NEGATIVE: Auxiliary WhatsApp HR Coordination (100 samples)                                 |
| 11. HARD NEGATIVE: Senior Executive Compensation     (100 samples)                                 |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Labeling Policy

### Binary Assignment
- **`label = 0` (Legitimate)**: The posting represents an authentic hiring process where applicant money, banking credentials, or unlawful tasks are never requested.
- **`label = 1` (Scam / Fraudulent)**: The posting or communication solicits money, demands account credentials, executes task-based pay-to-work fraud, or misrepresents employment to extort candidates.

### Contextual Disambiguation Rules
The dataset must teach the ML model **intent and semantic roles**, never keyword associations:
1. **Financial Keywords**:
   - `bank`, `account`, `payment`, `credit card`, `transfer`, `crypto` in the context of *software architecture, engineering duties, corporate accounting, or standard payroll* $\implies$ **`label = 0`**.
   - The same words in the context of *instructing the candidate to send, wire, deposit, or share funds/credentials* $\implies$ **`label = 1`**.
2. **Messaging Platforms**:
   - `WhatsApp`, `Telegram` mentioned as *an auxiliary coordination channel alongside official emails, career portals, or developer communities* $\implies$ **`label = 0`**.
   - `WhatsApp`, `Telegram` used as *the exclusive venue for interview bypass, fee payment, or task submission* $\implies$ **`label = 1`**.
3. **Incomplete or Informal Postings**:
   - Short descriptions, missing salary, or grammatical typos in small business/startup postings $\implies$ **`label = 0`** (Incomplete $\ne$ Scam).
4. **Compensation**:
   - High compensation for senior/architect/executive roles $\implies$ **`label = 0`**.
   - High compensation (e.g. ₹5,000/day) for unskilled typing/data entry $\implies$ **`label = 1`**.

---

## 4. Entity Leakage Prevention

### The Problem
In Step 6, feature inspection proved that `infosys is` (-0.398) and `tcs is` (-0.381) had some of the strongest negative weights in the model, while `apex` and `quickearn` had positive weights. The model memorized brand names instead of learning recruitment semantics.

### Universal Preprocessing Masking
All training texts and live inference inputs will be processed through an enhanced `preprocess_text()` function implementing strict entity masking:

| Entity Type | Regex / Pattern | Replacement Token | Reason |
| :--- | :--- | :---: | :--- |
| **Company Names** | Known registry entities & input company name | `<COMPANY>` | Prevents company name memorization |
| **Email Addresses** | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b` | `<EMAIL>` | Prevents domain string leakage into ML |
| **URLs** | `https?://\S+\|www\.\S+` | `<URL>` | Prevents URL token memorization |
| **Phone Numbers** | `\+?\d{10,12}\|\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b` | `<PHONE>` | Prevents specific phone prefix learning |
| **Monetary Values** | `(?:₹\|rs\.?\|inr\|\$\|usd)\s*[\d,]+(?:\.\d+)?` | `<MONEY>` | Normalizes currency scales |
| **Large Integers** | `\b\d{4,}\b` | `<NUM>` | Masks IDs, PINs, transaction codes |

### What Remains Unmasked
- **Action Verbs**: `pay`, `wire`, `deposit`, `transfer`, `reimburse`, `earn`, `apply`, `build`, `architect`, `reconcile`.
- **Nouns**: `fee`, `deposit`, `kit`, `salary`, `qualifications`, `experience`, `interview`, `assessment`, `round`, `portal`.
- **Platform Mentions**: `whatsapp`, `telegram`, `email`, `sms`.
- **Adjectives / Adverbs**: `guaranteed`, `urgent`, `instant`, `refundable`, `daily`.

---

## 5. Leakage-Resistant Data Splitting

A naive random train/test split leaks template sentences and boilerplate phrasing between splits.

### Splitting Protocol
1. **Deduplication**:
   - Hash all normalized texts; remove exact duplicates and near-duplicates (>90% 3-gram Jaccard similarity).
2. **Template & Source Grouping**:
   - Samples originating from the same source corpus or generated from the same template family are grouped together.
   - Group-based splitting ensures that **no template family or specific synthetic generator block appears in both train and test splits**.
3. **Partition Proportions**:
   - **Train Set (70%)**: Used exclusively to fit TF-IDF vocabulary and base classifier parameters.
   - **Validation Set (15%)**: Used exclusively for hyperparameter tuning (n-gram ranges, regularization $C$) and **Platt probability calibration**.
   - **Test Set (15%)**: Strict holdout; never seen during feature extraction, training, or calibration.
4. **Deterministic Seed**: Fixed random seed `42`.

---

## 6. Controlled Data Augmentation

### Policy: Quality Over Quantity
Unconstrained automatic paraphrasing (e.g. back-translation) often creates nonsensical JDs or duplicates boilerplate. We restrict augmentation to **controlled domain synthesis** targeting specific edge cases:

1. **Modern Task Scam Variations**: Synthesize varied descriptions of YouTube/Instagram like-and-earn tasks, app review tasks, and merchant rating commissions.
2. **Enterprise Disguised Fee Scams**: Embed upfront fee demands (background check proctoring, IT asset setup) within authentic-looking 300-word corporate JDs.
3. **Refundable Deposit Evasions**: Synthesize corporate traineeship descriptions requiring refundable laptop security deposits.
4. **Legitimate Auxiliary Communication**: Synthesize legitimate campus hiring announcements that provide WhatsApp for logistics.

---

## 7. Hard-Negative Legitimate Samples

To resolve the false positives discovered in Step 6 (e.g., Razorpay Payment Operations Engineer receiving $P(\text{scam}) = 0.5188$), the training dataset must be reinforced with **at least 350 hard-negative legitimate samples (`label = 0`)**:

```
+----------------------------------------------------------------------------------------------------+
| HARD-NEGATIVE PROFILES (LABEL = 0)                                                                 |
+----------------------------------------------------------------------------------------------------+
| Profile 1: Payment Gateway & Banking Infrastructure Engineer                                       |
|   "Backend Engineer at <COMPANY>. Develop high-throughput REST APIs for credit card processing,     |
|    instant bank transfers, NEFT/RTGS reconciliation, and automated fraud mitigation."              |
|                                                                                                    |
| Profile 2: Core Banking Operations & Ledger Reconciliation                                         |
|   "Financial Operations Analyst. Reconcile corporate bank accounts, audit daily transaction        |
|    ledgers, and process customer dispute settlements in compliance with RBI guidelines."           |
|                                                                                                    |
| Profile 3: Blockchain Custody & Protocol Engineer                                                  |
|   "Protocol Developer at <COMPANY>. Design smart contracts, secure institutional crypto wallet      |
|    custody protocols, and analyze liquidity pool disbursements on Ethereum testnet."               |
|                                                                                                    |
| Profile 4: Retail Gift Card & Voucher Operations Lead                                              |
|   "E-commerce Operations Specialist. Manage bulk corporate gift card distribution, audit digital   |
|    voucher inventory, and resolve merchant redemption discrepancies."                              |
|                                                                                                    |
| Profile 5: Campus Recruiter with Auxiliary WhatsApp Logistics                                      |
|   "HR Coordinator at <COMPANY>. Manage national campus hiring drives. Send interview slot updates   |
|    via official email portal and coordinate physical venue arrival via WhatsApp Business."         |
|                                                                                                    |
| Profile 6: Corporate Compensation & Payroll Manager                                                |
|   "Payroll Specialist at <COMPANY>. Ensure accurate monthly salary disbursement credited directly   |
|    to employee bank accounts; oversee Provident Fund and tax deductions."                         |
+----------------------------------------------------------------------------------------------------+
```

---

## 8. Model Architecture Evaluation & Selection

We conceptually evaluated six candidate architectures against AI-JobShield's production constraints:

| Architecture | Accuracy & F1 | CPU Latency | Model Size | Explainability | Calibration | Architectural Fit |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. TF-IDF + LogisticRegression (Platt Calibrated)** | **High (93-95%)** | **1-3 ms** | **~3 MB** | **Direct linear coefficients** | **Excellent (Platt)** | **RECOMMENDED: 100% Drop-in compatible** |
| 2. LinearSVC + CalibratedClassifierCV | High (93-95%) | 1-3 ms | ~3 MB | Via dual weights | Good | Requires extra wrappers; no direct log-odds |
| 3. Multinomial Naive Bayes | Moderate (85-88%)| <1 ms | ~1 MB | Log-probability ratios | Poor (Extreme 0/1 peaks)| Independence assumption fails on n-grams |
| 4. Word + Char TF-IDF + LogisticRegression | High (92-94%) | 8-15 ms | ~25 MB | Noisy character weights | Good | Vocabulary explosion (>60,000 terms) |
| 5. LightGBM / XGBoost on TF-IDF | High (93-95%) | 10-25 ms | ~15 MB | SHAP / Tree gain | Moderate | Higher complexity; tree splits on sparse text |
| 6. DistilBERT / MiniLM (Transformer) | Very High (96%)| 150-300 ms | ~250 MB | Complex attention maps | Requires temperature | Too heavy; introduces PyTorch/ONNX dependencies|

### Recommendation: OPTION 1 (TF-IDF + LogisticRegression with Platt Calibration)
- **Zero Architectural Disruption**: Directly replaces `jobshield_model.joblib` without changing inference APIs or adding dependencies.
- **Microsecond Latency**: Executes in 1–3 ms on standard CPU.
- **Explainability**: Seamlessly generates `top_terms` for the frontend explanation modal.
- **Effectiveness**: With entity masking and 3,500 diverse samples, linear TF-IDF easily achieves $\ge 93\%$ accuracy and $\ge 90\%$ scam recall.

---

## 9. Probability Calibration Strategy

### The Necessity of Calibration
In AI-JobShield, the ML output is directly used as a risk score:
$$\text{ml\_scam\_score} = \text{clamp}(100.0 - (P(\text{scam}) \times 100.0), 0.0, 100.0)$$
An uncalibrated model that outputs $P(\text{scam}) = 0.52$ for an innocent fintech job causes a 15-point drop in Dimension 4.

### Chosen Calibration Method: Platt Scaling (`method='sigmoid'`)
- Fit a sigmoid calibration mapping:
  $$P(y=1 | f(x)) = \frac{1}{1 + \exp(A \cdot f(x) + B)}$$
  where $f(x)$ is the raw decision margin (log-odds) from LogisticRegression.
- **Why Platt over Isotonic**: Isotonic regression is non-parametric and overfits on datasets with $<5,000$ samples, creating piecewise plateaus. Platt scaling produces smooth, continuous, well-calibrated probabilities.

### Data Partitioning for Calibration
- **Step 1**: Train TF-IDF vectorizer and base `LogisticRegression` on the 70% Train split.
- **Step 2**: Freeze the base estimator and fit `CalibratedClassifierCV(estimator=base_pipe, method='sigmoid', cv='prefit')` on the 15% Validation split.
- **Step 3**: Evaluate calibration (Brier score and calibration curve) strictly on the independent 15% Test split.

---

## 10. Feature Weight Audit & Expectations

Following retraining with entity masking and hard negatives:

### Expected Top Positive Features (Scam Predictors):
- `registration fee`, `application fee`, `training fee`, `vendor fee`, `refundable deposit`
- `earn daily`, `daily payout`, `typing jobs`, `per day without`, `task commission`
- `send otp`, `netbanking password`, `aadhaar pan copy`, `send pin`
- `no interview needed`, `instant selection`, `guaranteed selection`, `direct joining letter`
- `urgent joining pay`, `transfer fee to`

### Expected Top Negative Features (Legitimate Predictors):
- `responsibilities`, `qualifications`, `bachelor degree`, `years of experience`
- `technical round`, `interview process`, `coding assessment`, `system design`
- `health insurance`, `paid leave`, `provident fund`, `equal opportunity`
- `cloud infrastructure`, `backend services`, `collaborate with product`

### Features That Must NOT Dominate (Neutral / Zero Weight):
- Specific company names (`infosys`, `tcs`, `wipro`, `google` $\implies$ all masked to `<COMPANY>`)
- Webmail domains (`gmail`, `yahoo` $\implies$ all masked to `<EMAIL>`)
- Technical financial terms (`bank`, `account`, `payment`, `crypto` $\implies$ balanced by hard negatives)
- Communication channels (`whatsapp`, `telegram` $\implies$ balanced by auxiliary communication samples)

---

## 11. Evaluation Plan & Target Acceptance Criteria

The retrained model must satisfy the following strict quantitative thresholds on the unseen 15% holdout test set ($N \approx 500$):

| Evaluation Metric | Baseline Model (Step 6) | Retrained Model Target | Justification |
| :--- | :---: | :---: | :--- |
| **Accuracy** | 65.5% | $\ge \mathbf{92.0\%}$ | Generalization across diverse industries |
| **Scam Recall** | 57.1% | $\ge \mathbf{90.0\%}$ | Minimizes dangerous false negatives (misses $\le 10\%$) |
| **Scam Precision** | 92.3% | $\ge \mathbf{90.0\%}$ | Prevents user fatigue from false alarms |
| **F1-Score** | 0.7059 | $\ge \mathbf{0.9100}$ | Harmonic balance of precision and recall |
| **ROC-AUC** | 0.7976 | $\ge \mathbf{0.9500}$ | Strong class separability across all thresholds |
| **PR-AUC** | 0.8654 | $\ge \mathbf{0.9400}$ | High precision maintained across scam prevalence |
| **Brier Score** | 0.2185 | $\le \mathbf{0.0700}$ | Calibrated continuous probabilities |
| **Fintech False Positive Rate** | 25.0% | $\mathbf{0.0\%}$ | Zero false positives on legitimate payment/fintech roles |
| **Diluted Scam Detection Rate** | 0.0% | $\ge \mathbf{80.0\%}$ | Detects fee demands buried in enterprise JDs |

---

## 12. Regression Requirements

Before any retrained model can be deployed to production, it must successfully pass the following test suites:

1. **Benchmark Suite (`tests/run_ml_audit_cases.py`)**:
   - Cases 1, 2, 14, 15 (Legitimate Verified) must score $\ge 85$ (Low Risk).
   - Case 3 (Unknown Startup) must score $\approx 65$ (Medium Risk).
   - Cases 4, 5 (Impersonation) must score $\le 25$ (High Risk).
   - Cases 6, 7, 10, 11, 12 (Critical Scams) must score $\le 35$ (High Risk).
   - Cases 8, 9 (Messaging-only) must score $\le 55$ (Medium Risk).
2. **Context Suite (`tests/test_rule_engine_context.py`)**: All 27 tests pass.
3. **Identity Suite (`tests/test_company_identity.py`)**: All 13 tests pass.
4. **Evidence Hierarchy Suite (`tests/test_evidence_hierarchy.py`)**: All 25 tests pass.
5. **Scoring & History Suite (`tests/test_history_and_scoring.py`)**: All 7 tests pass.
6. **ML Validation Suite (`tests/test_ml_validation.py`)**: All 12 tests pass.
7. **New Regression Tests**:
   - Assert $P(\text{scam}) < 0.35$ for all hard-negative fintech/crypto engineering JDs.
   - Assert $P(\text{scam}) > 0.65$ for diluted scams (enterprise JD + proctoring fee).

---

## 13. Summary Answers to Strategic Questions

1. **What dataset should we train on?**
   A multi-source dataset fusing curated real-world postings from EMSCAD, verified Indian recruitment fraud cases, and targeted hard negatives.
2. **How should labels be defined?**
   Binary: `0` = Legitimate, `1` = Fraudulent. Labeling is governed by intent and context (extortion/credential harvesting vs technical duty/payroll), never isolated keywords.
3. **How do we prevent leakage?**
   Universal entity masking (`<COMPANY>`, `<EMAIL>`, `<URL>`, `<PHONE>`, `<MONEY>`, `<NUM>`) applied identically at training and inference.
4. **How many samples do we need?**
   3,000 to 4,000 balanced samples (approximately 1,800 legitimate and 1,700 scam).
5. **How should train/validation/test be split?**
   70% Train, 15% Validation (for calibration), 15% Test (isolated holdout), grouped by source/template family with deduplication.
6. **What preprocessing should be used?**
   Lowercase conversion, entity masking (`<COMPANY>`, `<EMAIL>`, `<URL>`, etc.), punctuation preservation for exclamation/currency cues, and sublinear TF scaling.
7. **What model should we use?**
   `TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)` with `LogisticRegression(class_weight='balanced')` calibrated via Platt scaling (`CalibratedClassifierCV`).
8. **How should probability calibration work?**
   Sigmoid Platt scaling fitted on the separate 15% validation split, mapping log-odds into well-calibrated $P(\text{scam})$ probabilities.
9. **What hard negatives are required?**
   At least 350 legitimate postings describing payment APIs, banking ledgers, crypto protocols, gift card operations, official WhatsApp campus coordination, and high executive salaries.
10. **What metrics determine whether retraining is successful?**
    Test accuracy $\ge 92\%$, scam recall $\ge 90\%$, Brier score $\le 0.07$, 0% false positives on fintech hard negatives, and 100% pass rate on all 84 regression tests.

---

## 14. Action Plan for Next Implementation Step

Upon approval, the retraining implementation will proceed in four sequential phases:
1. **Phase 1: Dataset Assembly**: Synthesize and curate the 3,500-sample balanced dataset in `data/training_data_v2.csv` with full entity masking and hard negatives.
2. **Phase 2: Preprocessing Upgrade**: Update `ml/preprocess.py` to support `<COMPANY>` and `<PHONE>` masking, ensuring identical transformations during training and live inference.
3. **Phase 3: Model Retraining & Platt Calibration**: Update `ml/train.py` to fit the calibrated pipeline and export `backend/models/jobshield_model.joblib`.
4. **Phase 4: Full Validation & Regression Run**: Run `run_ml_audit_cases.py`, `run_adversarial_ml_eval.py`, and the full 84-test pytest suite to verify all acceptance criteria.

---

> [!IMPORTANT]
> **Step 7 is strictly an architectural design phase.**
> No code was modified, no models were retrained, and no production configurations were altered. All existing 84 tests pass. We await user review and approval before proceeding to implementation.
