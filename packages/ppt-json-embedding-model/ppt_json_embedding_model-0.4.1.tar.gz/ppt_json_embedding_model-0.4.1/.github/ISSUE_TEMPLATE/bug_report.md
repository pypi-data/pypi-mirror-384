---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Training command used: `python -m embedding_model.cli.train ...`
2. Data format/size: 
3. Error occurred during: [training/embedding/search]
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Error message/traceback**
```
Paste the full error message and traceback here
```

**Environment (please complete the following information):**
 - OS: [e.g. Ubuntu 20.04, macOS, Windows 10]
 - Python version: [e.g. 3.10.5]
 - PyTorch version: [e.g. 2.2.0]
 - Package version: [e.g. 0.3.0]
 - GPU/CPU: [e.g. NVIDIA RTX 3080, CPU only]

**Training data info (if relevant):**
 - Number of JSON records: [e.g. 5000]
 - Average JSON size: [e.g. ~500 characters]
 - JSON structure: [e.g. has nested objects, mostly flat, etc.]

**Additional context**
Add any other context about the problem here. If this is a training issue, please include:
- Training parameters used (epochs, batch size, etc.)
- Hardware specifications
- Whether training was interrupted or completed
