# AI JobShield — Application Screenshots

This directory organizes visual screenshots representing the primary views and user interactions within **AI JobShield**.

---

## Visual Tour of the Application

### 1. Landing Page
* **Path**: `/`
* **Features**: Modern cybersecurity aesthetic, dark theme, interactive feature showcases, quick scam warning indicators, and direct access to sign-in or registration.

### 2. User Authentication & OTP Verification
* **Path**: `/auth`
* **Features**: Tabbed login and registration interface, client-side validation, password strength feedback, and automated 6-digit OTP verification powered by Gmail SMTP.

### 3. Security Dashboard
* **Path**: `/dashboard`
* **Features**: Live aggregate scan metrics (Total Analyses, Low Risk, Medium Risk, High Risk), Recharts risk distribution donut chart, 14-day analysis activity histogram, and quick action launchpads.

### 4. Job Opportunity Analysis
* **Path**: `/analyze`
* **Features**: Comprehensive job parameter input form, instant sample pre-loaders (Legitimate enterprise vs. Scam posting), and field-level validation.

### 5. OCR Screenshot Scanner
* **Path**: `/ocr`
* **Features**: Drag-and-drop image upload area, image preview thumbnail, client-side metadata pre-fill, OCR processing progress spinner, and job relevance gatekeeper feedback.

### 6. Multi-Dimensional Analysis Result
* **Path**: `/result/:id`
* **Features**:
  * Color-coded interactive SVG Trust Gauge (0–100)
  * 5-Dimensional visual scoring breakdown cards with progress indicators
  * Detected red flags with direct quotes of extracted evidence
  * Natural language explainability summary detailing company verification reasons and risk factors
  * Stored job parameters and expandable raw OCR text viewer

### 7. Persistent Analysis History
* **Path**: `/history`
* **Features**: User-scoped paginated history table, risk level filtering, direct navigation to past results, live refresh button, and safe individual record deletion.

### 8. User Profile
* **Path**: `/profile`
* **Features**: User identity badge, verified account status, registration date, aggregate risk breakdown, and cybersecurity security architecture notes.
