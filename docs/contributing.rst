.. _contributing:

============
Contributing
============

We welcome contributions! This document explains how to contribute to GeoHealth Pipeline.

Code of Conduct
===============

- Be respectful and inclusive
- Provide constructive feedback
- No harassment or discrimination
- Report issues to maintainers

Getting Started
===============

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a virtual environment
4. Install development dependencies

::

    git clone https://github.com/YOUR_USERNAME/geohealth-pipeline.git
    cd geohealth-pipeline
    python -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"

Development Workflow
====================

1. **Create a branch:**

   ::

       git checkout -b feature/your-feature-name
       # or for bugs:
       git checkout -b bugfix/issue-description

2. **Make changes** with tests

3. **Run tests locally:**

   ::

       pytest -v
       pytest --cov  # with coverage

4. **Format and lint:**

   ::

       black .
       isort .
       flake8 .

5. **Commit with clear messages:**

   ::

       git commit -m "Add feature X"
       git commit -m "Fix issue #123"

6. **Push and create Pull Request**

   ::

       git push origin feature/your-feature-name

Testing
=======

**Run all tests:**

::

    pytest -v

**Test specific file:**

::

    pytest test_geohealth_pipeline.py -v

**With coverage:**

::

    pytest --cov=geohealth_pipeline_Project --cov-report=html

**Generate coverage report:**

Coverage report in ``htmlcov/index.html``

Test Requirements
=================

- All new features must have tests
- Minimum coverage: 80%
- Tests must pass on Python 3.8, 3.9, 3.10, 3.11

Code Style
==========

We follow PEP 8 with these tools:

**Black (code formatting):**

::

    black geohealth_pipeline_Project.py

**isort (import sorting):**

::

    isort .

**flake8 (style checking):**

::

    flake8 .

**mypy (type checking):**

::

    mypy geohealth_pipeline_Project.py --ignore-missing-imports

Type Hints
==========

Add type hints to new functions:

::

    def load_data(path: str) -> pd.DataFrame:
        """Load CSV data from file."""
        return pd.read_csv(path)

Docstrings
==========

Use Google-style docstrings:

::

    def compute_rate(numerator: pd.Series, denominator: pd.Series, per: int = 1000) -> pd.Series:
        """Compute per-capita rate.

        Args:
            numerator: Series with event counts
            denominator: Series with population
            per: Base for rate calculation (default 1000)

        Returns:
            Series with computed rates

        Raises:
            ValueError: If denominator contains zeros

        Examples:
            >>> rates = compute_rate(counts, population)
        """
        return (numerator / denominator) * per

Pull Request Process
====================

1. **Update documentation** if needed
2. **Add tests** for your changes
3. **Update CHANGELOG.md** with your additions
4. **Link related issues** in PR description
5. **Provide clear PR description:**

   ::

       ## Description
       Brief description of changes

       ## Related Issue
       Fixes #123

       ## Type of Change
       - [ ] Bug fix
       - [ ] New feature
       - [ ] Breaking change
       - [ ] Documentation update

       ## How to Test
       Steps to verify changes

       ## Checklist
       - [ ] Tests pass
       - [ ] Code formatted (black)
       - [ ] Type hints added
       - [ ] Docstrings updated
       - [ ] CHANGELOG updated

Documentation
=============

Contributions to docs are welcomed!

**Build docs locally:**

::

    pip install sphinx sphinx-rtd-theme myst-parser
    cd docs
    make html
    # View in browser: _build/html/index.html

**Edit documentation:**

- ``docs/*.rst`` - Main docs (Sphinx reStructuredText)
- ``docs/*.md`` - Markdown docs (MyST parser)
- Docstrings in code - API reference

Reporting Issues
================

**Before reporting:**

1. Search existing issues
2. Check documentation
3. Try reproducing with minimal example

**Report format:**

::

    **Title:** Clear, concise title

    **Description:** What you tried, what happened

    **Expected behavior:** What should happen

    **Steps to reproduce:**
    1. ...
    2. ...
    3. ...

    **Environment:**
    - OS: [e.g., Ubuntu 22.04]
    - Python: [e.g., 3.11]
    - Version: [e.g., 1.0.0]

    **Logs:**
    (Paste error logs/traceback)

Feature Requests
================

**Template:**

::

    **Problem:** What problem does this solve?

    **Solution:** Describe the desired feature

    **Alternatives:** Other approaches considered

    **Example usage:**
    ```python
    # Show how you'd use this feature
    ```

Release Process
===============

Maintainers only:

1. Update version in ``pyproject.toml`` and ``__init__.py``
2. Update CHANGELOG.md
3. Create git tag: ``git tag v1.0.1``
4. Push to GitHub
5. GitHub Actions builds and publishes to PyPI

Commit Message Guidelines
=========================

Use conventional commit format:

::

    type(scope): subject

    body (optional)

    footer (optional)

**Types:**

- ``feat`` - New feature
- ``fix`` - Bug fix
- ``docs`` - Documentation
- ``style`` - Format/style
- ``refactor`` - Code refactoring
- ``perf`` - Performance improvement
- ``test`` - Test files
- ``ci`` - CI configuration
- ``chore`` - Maintenance

**Examples:**

::

    feat(pipeline): add crosswalk generation
    fix(api): handle null geometry correctly
    docs(deployment): add production guide
    refactor: simplify rate calculation

Resources
=========

- `GitHub Issues <https://github.com/your-org/geohealth-pipeline/issues>`_
- `Discussions <https://github.com/your-org/geohealth-pipeline/discussions>`_
- `Developer Docs <https://geohealth-pipeline.readthedocs.io>`_
- `Python Style Guide <https://pep8.org/>`_
- `Git Documentation <https://git-scm.com/doc>`_

Getting Help
============

- Ask questions in GitHub Discussions
- Create issues for bugs
- Email maintainers: support@example.com
- Check existing documentation

Thank You!
==========

Thank you for contributing to make GeoHealth Pipeline better!
