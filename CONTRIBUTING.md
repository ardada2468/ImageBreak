# Contributing to ImageBreak

Thank you for your interest in contributing to ImageBreak! This document provides guidelines for contributing to the project.

## Code of Conduct

This project is dedicated to providing a harassment-free experience for everyone. We do not tolerate harassment of participants in any form.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
5. Install in development mode: `pip install -e .[dev]`

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Add tests if applicable
4. Run tests: `pytest`
5. Run linting: `black . && flake8 .`
6. Commit your changes: `git commit -m "Description of changes"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Types of Contributions

### Bug Reports

When filing an issue, make sure to answer these questions:
- What version of ImageBreak are you using?
- What operating system and Python version are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

### Feature Requests

We welcome feature requests! Please provide:
- A clear description of the feature
- The motivation/use case for the feature
- How it fits into the project's goals

### Code Contributions

- Follow PEP 8 style guidelines
- Add docstrings to all public functions and classes
- Include type hints where appropriate
- Write tests for new functionality
- Update documentation as needed

## Adding New Models

To add support for a new AI model:

1. Create a new file in `imagebreak/models/`
2. Inherit from `BaseModel`
3. Implement required methods:
   - `generate_text()`
   - `generate_image()` (if supported)
   - `generate_violating_prompt()`
   - `generate_alternate_prompt()`
4. Add proper error handling and logging
5. Update `__init__.py` exports
6. Add tests
7. Update documentation

## Testing

- All tests are in the `tests/` directory
- Use pytest for testing
- Aim for good test coverage
- Mock external API calls
- Test both success and failure cases

## Documentation

- Keep the README.md up to date
- Add docstrings to all public interfaces
- Include examples in docstrings
- Update the API documentation

## Security Considerations

Given the nature of this project:
- Never commit API keys or credentials
- Be mindful of the content being generated
- Follow responsible disclosure practices
- Ensure all generated content is properly handled

## Questions?

Feel free to open an issue for discussion or reach out to the maintainers.

Thank you for contributing! 