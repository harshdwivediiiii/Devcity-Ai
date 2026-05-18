🤝 Contributing to DevCity AI

First off, thank you for considering contributing to DevCity AI 🚀
We welcome contributions from developers, designers, AI engineers, DevOps engineers, technical writers, and open-source enthusiasts.

---

📌 Table of Contents

- "Code of Conduct" (#-code-of-conduct)
- "Ways to Contribute" (#-ways-to-contribute)
- "Development Setup" (#-development-setup)
- "Environment Variables" (#-environment-variables)
- "Issue Assignment Policy" (#-issue-assignment-policy)
- "Branch Naming Convention" (#-branch-naming-convention)
- "Commit Message Guidelines" (#-commit-message-guidelines)
- "Pull Request Process" (#-pull-request-process)
- "Coding Standards" (#-coding-standards)
- "Testing Guidelines" (#-testing-guidelines)
- "Issue Guidelines" (#-issue-guidelines)
- "Security Policy" (#-security-policy)
- "Feature Requests" (#-feature-requests)
- "Architecture Principles" (#-architecture-principles)

---

📜 Code of Conduct

By participating in this project, you agree to:

- Be respectful and inclusive
- Provide constructive feedback
- Avoid harassment or toxic behavior
- Collaborate professionally

Any abusive behavior may result in restricted repository access.

---

🚀 Ways to Contribute

You can contribute by:

🐛 Reporting Bugs

- UI issues
- Rendering problems
- Performance bottlenecks
- Security vulnerabilities

✨ Adding Features

Examples:

- AI architecture analysis
- 3D visualization improvements
- PR intelligence
- Dependency scanning
- CI/CD integrations

📚 Improving Documentation

- README improvements
- Architecture diagrams
- Setup instructions
- API docs

⚡ Performance Optimization

- Three.js optimization
- GPU rendering improvements
- Async worker queues
- DB optimization

---

🛠 Development Setup

1. Fork the Repository

git clone https://github.com/your-username/devcity-ai.git
cd devcity-ai

2. Create Virtual Environment

python -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

---

🔐 Environment Variables

Create a ".env" file in the project root:

SECRET_KEY=your_secret_key
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

«⚠️ Never commit ".env" files or secrets to GitHub.
Add ".env" to ".gitignore".»

---

🎯 Issue Assignment Policy

To maintain organized collaboration and avoid duplicate work:

- Do not work on issues that are not assigned to you.
- Unassigned pull requests may be closed without review.
- Before starting work:
  1. Comment on the issue
  2. Request assignment
  3. Wait for maintainer approval

Why This Policy Exists

This helps:

- prevent duplicate work
- avoid conflicting PRs
- improve collaboration
- maintain clean project management

Exceptions

Small fixes such as:

- typo fixes
- documentation improvements
- minor UI changes

may not require assignment unless maintainers specify otherwise.

Recommended Workflow

1. Find an issue
2. Request assignment
3. Wait for approval
4. Create branch
5. Start development

---

🌿 Branch Naming Convention

Use descriptive branch names:

feature/ai-risk-heatmap
bugfix/render-timeout-fix
hotfix/oauth-session-bug
docs/readme-update

---

📝 Commit Message Guidelines

Follow Conventional Commits:

feat: add PR intelligence engine
fix: resolve websocket reconnect issue
docs: improve deployment instructions
refactor: optimize repository parser

---

🔄 Pull Request Process

Before Submitting

- Ensure code builds successfully
- Run tests locally
- Verify linting passes
- Keep PRs focused and atomic

PR Requirements

Include:

- clear description
- screenshots/videos (if UI-related)
- linked issue number
- testing notes

Example PR Template

## Description
Added async worker queue support for repository analysis.

## Changes
- Integrated Redis queue
- Added task progress endpoint
- Updated frontend polling logic

## Related Issue
Closes #42

---

💻 Coding Standards

Backend

- Follow PEP8
- Use type hints
- Keep functions modular
- Avoid monolithic route handlers

Frontend

- Reusable components only
- Avoid hardcoded values
- Optimize WebGL rendering
- Use lazy loading where possible

AI Systems

- Avoid hallucinated outputs
- Add confidence scoring
- Include explainability metadata

---

🧪 Testing Guidelines

Backend Tests

pytest

Frontend Tests

npm test

Performance Validation

Ensure:

- FPS remains stable
- no memory leaks
- async jobs do not block server

---

📦 Dependency Management

Always pin versions:

Flask==3.0.2
pandas==2.2.1
scikit-learn==1.4.0

Do not introduce unnecessary dependencies.

---

🐞 Issue Guidelines

Good Bug Reports Include

- reproduction steps
- screenshots/logs
- browser/environment info
- expected behavior

Example

### Bug
3D city crashes on repositories larger than 1000 files.

### Steps to Reproduce
1. Open app
2. Analyze large monorepo
3. Orbit camera rapidly

### Expected Behavior
Stable rendering without GPU crash.

---

🔒 Security Policy

Please DO NOT publicly disclose security vulnerabilities.

Instead:

- create a private security advisory
- contact maintainers directly

Examples:

- path traversal
- auth bypass
- token leakage
- SSRF vulnerabilities

---

💡 Feature Requests

Feature proposals should include:

- problem statement
- proposed solution
- architecture impact
- UI/UX implications
- scalability considerations

---

🏗 Architecture Principles

DevCity AI follows these principles:

1. Async-First Processing

Heavy repository analysis must never block request threads.

2. Scalable Visualization

Rendering systems should support very large repositories efficiently.

3. Security by Default

Untrusted repositories must always be sandboxed.

4. Explainable AI

AI recommendations should include:

- reasoning
- confidence
- traceability

5. Developer Experience First

Fast, intuitive, production-grade workflows matter.

---

🌟 Recognition

All contributors will be recognized in:

- contributors section
- release notes
- major feature acknowledgements

---

❤️ Thank You

Your contributions help make DevCity AI better for developers worldwide.

Happy Building 🚀