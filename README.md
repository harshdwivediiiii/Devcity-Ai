<div align="center">
  
  # 🌆 DevCity AI : ML-Powered Code Health Map

  <img width="350" height=auto alt="Screenshot from 2026-06-10 16-52-32" src="https://github.com/user-attachments/assets/5a31d50d-24f8-4d18-a250-39fc0db8448e" />
  
  <br>
  
  **DevCity AI transforms GitHub repositories into interactive 3D city visualizations, augmented with data-driven risk and anomaly scoring. Engineered as an end-to-end machine learning system, this project demonstrates production-grade data engineering, predictive modeling, and full-stack architecture for real-world software analytics.**
  
  ### 🚀 Live Demo: https://devcity-ai-1.onrender.com/

</div>

---

## 📖 System Overview

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

<img width="500" height=auto alt="Screenshot from 2026-06-10 16-55-46" src="https://github.com/user-attachments/assets/a1021e51-522f-4164-8696-21c54741d9a7" />

---

## 🔐 Authentication & Security

DevCity AI features segmented authorization using secure GitHub OAuth integration.

### Public Access

Unauthenticated users can:
- analyze public repositories
- explore generated code cities
- inspect architecture metrics

### Authenticated Access

Authenticated users gain access to:
- saved analysis dashboard
- historical snapshots
- timeline comparisons
- future premium analytics

---

## ⚙️ Environment Variables

Configure the following variables inside `.env`:

```env
SECRET_KEY=your_secret_key
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

### Optional Configuration

```env
GITHUB_OAUTH_SCOPES=read:user
```

> ⚠️ Never commit `.env` files or secrets to GitHub.

---

## 🛠 Local Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/devcity-ai.git
cd devcity-ai
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Development Server

```bash
python app.py
```

Once initialized, the dashboard becomes available at:

```txt
http://localhost:5100
```

---

## 🧠 Core Tech Stack

### Backend
- ![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
- ![SQLite](https://img.shields.io/badge/SQLite-074D5B?style=for-the-badge&logo=sqlite&logoColor=white)
- ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
- ![GitHub OAuth](https://img.shields.io/badge/GitHub%20OAuth-181717?style=for-the-badge&logo=github&logoColor=white)

### Frontend
- ![Three.js](https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.dot.js&logoColor=white)
- ![WebGL](https://img.shields.io/badge/WebGL-990000?style=for-the-badge&logo=webgl&logoColor=white)
- ![JavaScript](https://img.shields.io/badge/Vanilla%20JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

### Machine Learning
- ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
- ![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
- ![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
- Anomaly Detection Pipelines

### Visualization
- 3D code city rendering
- Real-time metric overlays
- Interactive repository exploration

---

## 🚀 Planned Features

- AI architecture copilot
- PR intelligence engine
- architecture drift detection
- technical debt heatmaps
- multi-repository visualization
- dependency risk scanning
- time-travel architecture replay
- CI/CD architecture analytics

---

## 🤝 Contributing

We welcome contributions from:
- developers
- ML engineers
- UI/UX designers
- security researchers
- open-source contributors

Before contributing, please read our contribution guidelines:

👉 [CONTRIBUTING.md](https://github.com/harshdwivediiiii/Devcity-Ai/blob/main/Contributor.md)

---

## 🎯 Contribution Rules

- Do **not** work on issues that are not assigned to you.
- Request assignment before starting implementation.
- Unassigned pull requests may be closed without review.

### Recommended Workflow

```txt
1. Find an open issue
2. Request assignment
3. Wait for approval
4. Create feature branch
5. Start development
```
---

## 🌿 Branch Naming Convention

```bash
feature/ai-risk-heatmap
bugfix/render-timeout-fix
docs/readme-update
```

---

## 📝 Commit Convention

Use Conventional Commits:

```bash
feat: add anomaly scoring engine
fix: resolve rendering memory leak
docs: improve setup guide
refactor: optimize repository parser
```

---

## 🧪 Running Tests

### Backend

```bash
pytest
```

### Frontend

```bash
npm test
```

---

## 🔒 Security Policy

Please responsibly disclose vulnerabilities.

Examples:
- path traversal
- OAuth bypass
- token leakage
- sandbox escape
- SSRF vulnerabilities

Do not publicly expose security issues before maintainers review them.

---

## 📦 Dependency Management

Always pin dependency versions:

```txt
Flask==3.0.2
pandas==2.2.1
scikit-learn==1.4.0
```

---

## 🏗 Architecture Principles

DevCity AI follows these engineering principles:

### Async-First Processing
Heavy analysis must never block request threads.

### Security by Default
Untrusted repositories must be sandboxed.

### Explainable AI
AI recommendations should include:
- confidence scores
- reasoning
- traceability

### Scalable Visualization
Rendering pipelines should support massive repositories efficiently.

### Developer Experience First
Fast, intuitive workflows matter.

---

## 🌟 Recognition

Contributors are recognized through:
- Release notes
- Contributor sections
- Major feature acknowledgements

---

## ❤️ Thank You

Thanks for helping improve DevCity AI and pushing the future of intelligent software architecture visualization! 🚀
