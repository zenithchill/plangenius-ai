# Contributing to PlanGenius AI

Thank you for your interest in contributing to PlanGenius AI! We welcome bug fixes, documentation improvements, and architectural enhancements.

## Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/zenithchill/plangenius-ai.git
   cd plangenius-ai
   ```

2. **Set Up Python Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Run the Application**:
   ```bash
   python3 app.py
   ```
   Access the UI at `http://127.0.0.1:5000`.

4. **Run the Test Suites**:
   ```bash
   pytest test_backend.py test_integration.py -v
   ```

## Pull Request Guidelines

1. Create a descriptive feature branch (`git checkout -b feature/amazing-feature`).
2. Follow PEP 8 style standards with type hints for Python code and standard ES6+ conventions for JavaScript.
3. Ensure all automated tests pass before submitting.
4. Add new test cases for new endpoints or state modifications.
5. Provide a clear PR description detailing your changes and test coverage.
