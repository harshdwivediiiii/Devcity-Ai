# DevCity AI – ML-Powered Code Health Map

DevCity AI transforms GitHub repositories into interactive 3D city visualizations, augmented with data-driven risk and anomaly scoring. Engineered as an end-to-end machine learning system, this project demonstrates production-grade data engineering, predictive modeling, and full-stack architecture for real-world software analytics.

This project is now live at: https://devcity-ai-1.onrender.com/

## System Overview

The core pipeline automatically engineers features from raw source code to surface actionable machine learning insights:

- **Automated Feature Engineering**: Scans GitHub repositories to extract and compute complex per-file metrics (size, component structure, software complexity).
- **Data Persistence**: Maintains historical snapshot state and file-level metrics inside a centralized SQLite database.
- **Data Science Sandbox**: Provides a suite of Jupyter notebooks for exploratory data analysis and model training:
  - A supervised **Risk Classification Model** to predictably identify architectural bottlenecks and high-risk technical debt.
  - An **Anomaly Detection Model** robustly tuned to flag critical structural deviations.
- **Real-Time ML Inference**: Serves custom machine learning models directly through the Flask backend infrastructure to attach a `risk_score` and `anomaly_score` dynamically to every compiled file.
- **3D Interactive Insights**: Aggregates the respective machine learning predictions and repository scaling data into a modern, responsive 3D visualization dashboard.

## Authentication & Security

DevCity AI features segmented authorization via secure **GitHub OAuth integration**:

- **Public Access**: Unauthenticated users maintain robust access to trigger the underlying analysis pipeline on public-facing repositories.
- **Authenticated Access**: Advanced features—including the custom saved analyses dashboard, historical timeline slider, and comparative snapshot diffs—are securely gated behind GitHub identity verification.

To enable OAuth in your environment, configure the following keys:

- `GITHUB_CLIENT_ID`: Your registered GitHub application client ID.
- `GITHUB_CLIENT_SECRET`: Your registered GitHub application secret.
- `SECRET_KEY`: Cryptographically secure string for establishing stable session persistence (falls back to a random key rotation per-run if omitted).

*Optional Configuration:*
- `GITHUB_OAUTH_SCOPES`: Expand or restrict permission access (default: `read:user`).

## Local Installation

Prepare the environment dependencies and launch the inference server locally:

```bash
pip install -r requirements.txt
python app.py
```

Once initialized, the graphical dashboard will be available at `http://localhost:5100`.
