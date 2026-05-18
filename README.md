# DevCity AI – ML-Powered Code Health Map

DevCity AI transforms GitHub repositories into interactive 3D city visualizations, augmented with data-driven risk and anomaly scoring. Engineered as an end-to-end machine learning system, this project demonstrates production-grade data engineering, predictive modeling, and full-stack architecture for real-world software analytics.

🚀 Live Demo: https://devcity-ai-1.onrender.com/

---

# 🌆 System Overview

The core pipeline automatically engineers features from raw source code to surface actionable machine learning insights:

- **Automated Feature Engineering**  
  Scans GitHub repositories to extract and compute complex per-file metrics:
  - file size
  - component structure
  - software complexity
  - dependency relationships

- **Data Persistence**  
  Maintains historical snapshot state and file-level metrics inside a centralized SQLite database.

- **Data Science Sandbox**  
  Includes Jupyter notebooks for:
  - Exploratory Data Analysis (EDA)
  - Risk prediction model training
  - Anomaly detection experiments

- **Risk Classification Model**  
  Predicts:
  - architectural bottlenecks
  - unstable modules
  - high-risk technical debt zones

- **Anomaly Detection Engine**  
  Flags:
  - abnormal structures
  - suspicious complexity spikes
  - hidden architecture deviations

- **Real-Time ML Inference**  
  Serves trained ML models directly through Flask APIs to dynamically generate:
  - `risk_score`
  - `anomaly_score`

- **3D Interactive Visualization**  
  Converts repositories into interactive code cities powered by:
  - Three.js
  - real-time analytics
  - machine learning overlays

---

# 🔐 Authentication & Security

DevCity AI features segmented authorization using secure GitHub OAuth integration.

## Public Access

Unauthenticated users can:
- analyze public repositories
- explore generated code cities
- inspect architecture metrics

## Authenticated Access

Authenticated users gain access to:
- saved analysis dashboard
- historical snapshots
- timeline comparisons
- future premium analytics

---

# ⚙️ Environment Variables

Configure the following variables inside `.env`:

```env
SECRET_KEY=your_secret_key
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

## Optional Configuration

```env
GITHUB_OAUTH_SCOPES=read:user
```

> ⚠️ Never commit `.env` files or secrets to GitHub.

---

# 🛠 Local Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/devcity-ai.git
cd devcity-ai
```

## 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Start Development Server

```bash
python app.py
```

Once initialized, the dashboard becomes available at:

```txt
http://localhost:5100
```

---

# 🧠 Core Tech Stack

## Backend
- Flask
- SQLite
- SQLAlchemy
- GitHub OAuth

## Frontend
- Three.js
- WebGL
- Vanilla JavaScript

## Machine Learning
- scikit-learn
- pandas
- NumPy
- anomaly detection pipelines

## Visualization
- 3D code city rendering
- real-time metric overlays
- interactive repository exploration

---

# 🚀 Planned Features

- AI architecture copilot
- PR intelligence engine
- architecture drift detection
- technical debt heatmaps
- multi-repository visualization
- dependency risk scanning
- time-travel architecture replay
- CI/CD architecture analytics

---

# 🤝 Contributing

We welcome contributions from:
- developers
- ML engineers
- UI/UX designers
- security researchers
- open-source contributors

Before contributing, please read our contribution guidelines:

👉 [CONTRIBUTING.md](https://github.com/harshdwivediiiii/Devcity-Ai/blob/main/Contributor.md)

---

# 🎯 Contribution Rules

- Do **not** work on issues that are not assigned to you.
- Request assignment before starting implementation.
- Unassigned pull requests may be closed without review.

## Recommended Workflow

```txt
1. Find an open issue
2. Request assignment
3. Wait for approval
4. Create feature branch
5. Start development
```
---

# 🌿 Branch Naming Convention

```bash
feature/ai-risk-heatmap
bugfix/render-timeout-fix
docs/readme-update
```

---

# 📝 Commit Convention

Use Conventional Commits:

```bash
feat: add anomaly scoring engine
fix: resolve rendering memory leak
docs: improve setup guide
refactor: optimize repository parser
```

---

# 🧪 Running Tests

## Backend

```bash
pytest
```

## Frontend

```bash
npm test
```

---

# 🔒 Security Policy

Please responsibly disclose vulnerabilities.

Examples:
- path traversal
- OAuth bypass
- token leakage
- sandbox escape
- SSRF vulnerabilities

Do not publicly expose security issues before maintainers review them.

---

# 📦 Dependency Management

Always pin dependency versions:

```txt
Flask==3.0.2
pandas==2.2.1
scikit-learn==1.4.0
```

---

# 🏗 Architecture Principles

DevCity AI follows these engineering principles:

## Async-First Processing
Heavy analysis must never block request threads.

## Security by Default
Untrusted repositories must be sandboxed.

## Explainable AI
AI recommendations should include:
- confidence scores
- reasoning
- traceability

## Scalable Visualization
Rendering pipelines should support massive repositories efficiently.

## Developer Experience First
Fast, intuitive workflows matter.

---

# 🌟 Recognition

Contributors are recognized through:
- release notes
- contributor sections
- major feature acknowledgements

---

# ❤️ Thank You

Thanks for helping improve DevCity AI and pushing the future of intelligent software architecture visualization 🚀