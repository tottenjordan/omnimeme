# Code Standards & Engineering Guidelines

This document outlines the mandatory coding and development standards for this project.

## General Guidelines
- **No Co-Authored-By Trailers**: Never add `Co-Authored-By` trailers when making commits or submitting PRs.
- **Code Preservation**: Make surgical, targeted edits and preserve surrounding comments, configuration, and code.

## Python Development
- **Package Management**: Use `uv` exclusively for all package management (`uv add`, `uv remove`, `uv sync`, `uv run`). Never use bare `pip` or `python`.
- **Linting & Formatting**: Use `ruff` for linting and formatting (`uv run ruff check` and `uv run ruff format`). Never use `black`, `flake8`, or `isort`.
- **Type Checking**: Use `ty` for static type checking (`uv run ty check src/`).
- **Testing Framework**: Use `pytest` for unit/integration code correctness testing (`uv run pytest`). For LLM behavior validation, use `agents-cli eval`.
- **Standards Reference**: Refer to the `modern-python` skill for full tooling best practices.

## Agent Development & CLI
- **Framework**: Google Agent Development Kit (ADK).
- **CLI Tooling**: `google-agents-cli` (`agents-cli`) for scaffolding, running, evaluating, and deploying agents.
- **Evaluation**: Never write `pytest` tests that assert on LLM output content. Use `agents-cli eval` with LLM-as-judge criteria.
