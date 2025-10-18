# Code Review Plus

A Python toolkit for automated code review and CI/CD pipeline analysis. Supports parsing and validating Dockerfiles, GitLab CI configurations, and more.

## Features

- Parse and validate GitLab CI rules
- Extract and analyze Dockerfile `FROM` statements
- Linting and code quality checks
- Test coverage reporting

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (for building and publishing)
- [pytest](https://pytest.org/)
- [ruff](https://github.com/astral-sh/ruff)

## Installation

Clone the repository:

```bash
git clone git@github.com:luiscberrocal/code-review-plus.git
cd code-review-plus