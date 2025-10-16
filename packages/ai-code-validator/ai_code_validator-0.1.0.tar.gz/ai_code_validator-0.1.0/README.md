# 🤖 AI Code Validator

**Catch AI-generated code mistakes before they cause problems.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ashishmahawal/ai-code-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/ashishmahawal/ai-code-validator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ashishmahawal/ai-code-validator/branch/master/graph/badge.svg)](https://codecov.io/gh/ashishmahawal/ai-code-validator)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> A CLI tool that analyzes AI-generated code for hallucinations, security vulnerabilities, and outdated patterns. Get a confidence score before you commit!

---

## 🎯 The Problem

**66%** of developers are frustrated with AI-generated code that's "almost right, but not quite"

**45%** say debugging AI code is more time-consuming than writing it themselves

**20%** of AI-generated code suggests non-existent packages (creating "slopsquatting" security risks)

**62%** of AI code contains security vulnerabilities, even from the latest models

**AI Code Validator** solves this by automatically detecting:
- 🔍 **Hallucinated functions & APIs** that don't actually exist
- 📦 **Fake dependencies** before you `pip install` or `npm install` them
- 🔒 **Security vulnerabilities** like SQL injection, XSS, and command injection
- ⚠️ **Missing input validation** (AI's #1 mistake)
- 📅 **Outdated patterns** from old training data
- 🔑 **Hardcoded secrets** that shouldn't be in code

---

## ⚡ Quick Start

### Installation

```bash
pip install ai-code-validator
```

### Basic Usage

```bash
# Check a single file
aivalidate check myfile.py

# Check entire directory
aivalidate check src/

# Check with JSON output (for CI/CD)
aivalidate check . --format json

# Install git pre-commit hook
aivalidate install-hook
```

---

## 📊 Example Output

```
==================================================================
🤖 AI CODE VALIDATOR - RESULTS
==================================================================

Confidence Score: 67/100 (FAIR)
Total Issues: 5
  Critical: 2 | High: 1 | Medium: 1 | Low: 1

Recommendation:
  ⚠️  CRITICAL: Hallucinated dependencies detected! Do NOT install these packages.

==================================================================
🚨 CRITICAL ISSUES (2)
==================================================================

[HALLUCINATED_DEPENDENCY]
  File: app.py:3
  Package "ai-utils-helper" does not exist on PyPI
  💡 Suggestion: AI may have hallucinated this package. This creates a "slopsquatting" security risk.

[SQL_INJECTION]
  File: database.py:45
  Potential SQL injection: String concatenation in SQL query
  💡 Suggestion: Use parameterized queries or prepared statements instead

==================================================================
⚠️  HIGH SEVERITY ISSUES (1)
==================================================================

[MISSING_INPUT_VALIDATION]
  File: api.py:23
  User input without validation detected
  💡 Suggestion: AI often omits input validation. Add validation before using user input.
```

---

## ✨ Features

### 🔍 **AI Hallucination Detection**
- Detects non-existent functions and methods
- Identifies fake API endpoints
- Spots missing call sites and dependencies

### 📦 **Dependency Validation**
- Checks if packages exist on PyPI, npm, etc.
- Prevents "slopsquatting" attacks
- Validates imports in real-time

### 🔒 **Security Scanning**
- SQL injection detection
- XSS vulnerability checks
- Command injection patterns
- Hardcoded secrets detection
- Missing input validation (AI's most common mistake)

### 📊 **Confidence Scoring**
- 0-100 score based on issue severity
- Clear ratings: EXCELLENT → CRITICAL
- Actionable recommendations

### 🎨 **Beautiful Output**
- Color-coded severity levels
- Clear issue descriptions
- Helpful suggestions for fixes
- JSON output for CI/CD integration

### 🔧 **Git Integration**
- One-command pre-commit hook installation
- Automatic validation on every commit
- Only checks staged files

---

## 🚀 Usage Examples

### Basic File Checking

```bash
# Single file
aivalidate check app.py

# Multiple files
aivalidate check app.py utils.py models.py

# Entire directory (recursively)
aivalidate check src/

# Current directory
aivalidate check .
```

### Filtering by Severity

```bash
# Only critical issues
aivalidate check . --severity critical

# Critical and high only
aivalidate check . --severity high

# All issues (default)
aivalidate check . --severity all
```

### Output Formats

```bash
# Human-readable colored output (default)
aivalidate check .

# JSON output for parsing
aivalidate check . --format json
```

### Speed Optimization

```bash
# Skip dependency checking (faster, but less thorough)
aivalidate check . --no-deps
```

### Git Integration

```bash
# Install pre-commit hook
aivalidate install-hook

# Now runs automatically on git commit!

# To bypass (not recommended):
git commit --no-verify
```

---

## 🏗️ How It Works

AI Code Validator uses a multi-layer analysis approach:

1. **AST Parsing** - Analyzes code structure using Abstract Syntax Trees
2. **Pattern Matching** - Detects common AI hallucination patterns
3. **Dependency Verification** - Checks package registries (PyPI, npm) in real-time
4. **Security Analysis** - Scans for OWASP Top 10 vulnerabilities
5. **Scoring Algorithm** - Calculates confidence score with severity weighting
6. **Smart Reporting** - Groups and prioritizes issues for quick fixes

### Supported Languages

- ✅ Python (`.py`)
- ✅ JavaScript (`.js`, `.jsx`)
- ✅ TypeScript (`.ts`, `.tsx`)
- ✅ Java (`.java`)
- ✅ Kotlin (`.kt`)
- 🚧 More coming soon!

---

## 🔗 CI/CD Integration

### GitHub Actions

```yaml
name: AI Code Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install AI Code Validator
        run: pip install ai-code-validator
      - name: Run validation
        run: aivalidate check . --format json --severity high
```

### GitLab CI

```yaml
ai-validation:
  image: python:3.9
  script:
    - pip install ai-code-validator
    - aivalidate check . --format json --severity high
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** - Open an issue describing the problem
2. **Suggest features** - What would make this tool more useful?
3. **Add language support** - Help us support more languages
4. **Improve detection** - Add more AI hallucination patterns
5. **Write documentation** - Help others use the tool

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ashishmahawal/ai-code-validator.git
cd ai-code-validator

# Initialize development environment (installs deps + pre-commit hooks)
make init

# Or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install

# Run tests
make test
# or: pytest tests/

# Run tests with coverage
make test-cov

# Run linters
make lint

# Format code
make format
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⭐ Support

If this tool saved you from debugging AI-generated code, give it a star! ⭐

It helps others discover the project and motivates continued development.

---

## 🙏 Acknowledgments

Built based on research into AI code generation issues:
- [METR Study on AI Developer Productivity](https://metr.org/)
- [Endor Labs Security Research](https://www.endorlabs.com/)
- [CSET Georgetown Cybersecurity Research](https://cset.georgetown.edu/)

---

## 📚 Learn More

- **Research**: Why do AI tools generate buggy code? Read our [blog post](https://github.com/yourusername/ai-code-validator/wiki)
- **Best Practices**: [Using AI Coding Tools Safely](https://github.com/yourusername/ai-code-validator/wiki/best-practices)
- **FAQ**: [Frequently Asked Questions](https://github.com/yourusername/ai-code-validator/wiki/faq)

---

**Made with ❤️ by developers frustrated with AI hallucinations**

**Don't let AI fool you. Validate before you commit!**
