# Password Manager Documentation

This directory contains the complete documentation for the Password Manager application, built with [Sphinx](https://www.sphinx-doc.org/).

## Documentation Structure

```
documentation/
├── source/                 # Source files (.rst, .md)
│   ├── api/               # API reference documentation
│   ├── user-guide/        # User guides and tutorials
│   ├── developer/         # Developer documentation
│   ├── conf.py            # Sphinx configuration
│   └── index.rst          # Documentation homepage
├── build/                 # Generated documentation (gitignored)
│   └── html/              # HTML output
├── Makefile               # Build commands (Unix/macOS)
├── make.bat               # Build commands (Windows)
└── README.md              # This file
```

## Building the Documentation

### Prerequisites

Install Sphinx and required extensions:

```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints myst-parser
```

### Build HTML Documentation

**On Windows:**

```bash
cd documentation
make.bat html
```

**On Unix/macOS:**

```bash
cd documentation
make html
```

### View Documentation

After building, open the documentation in your browser:

**Windows:**

```bash
start build\html\index.html
```

**macOS:**

```bash
open build/html/index.html
```

**Linux:**

```bash
xdg-open build/html/index.html
```

## Other Build Formats

Sphinx supports multiple output formats:

```bash
make html        # HTML pages (default)
make singlehtml  # Single HTML page
make latex       # LaTeX files
make pdf         # PDF (requires LaTeX)
make epub        # EPUB e-book
make man         # Manual pages
make text        # Plain text
```

## Documentation Sections

### User Guide

Comprehensive guides for end users:

* **Installation**: Setting up the application
* **Getting Started**: First-time setup and basic usage
* **Managing Passwords**: Advanced password management
* **Browser Extension**: Using the browser extension
* **Import/Export**: Backing up and restoring passwords
* **Settings**: Customizing the application

### API Reference

Auto-generated API documentation from code docstrings:

* **Core Modules**: Password manager, encryption, database
* **GUI Modules**: Windows, dialogs, and UI components
* **Utility Modules**: Logging, types, and helpers

### Developer Guide

Documentation for contributors and developers:

* **Architecture**: System design and architecture overview
* **Contributing**: How to contribute to the project
* **Testing**: Testing guidelines and procedures
* **Deployment**: Building and distributing the application

## Editing Documentation

### File Formats

* **reStructuredText (.rst)**: Primary format for Sphinx
* **Markdown (.md)**: Supported via MyST parser

### Adding New Pages

1. Create a new `.rst` or `.md` file in the appropriate directory
2. Add the file to the relevant `toctree` directive in `index.rst` or parent file
3. Rebuild the documentation

Example:

```rst
.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user-guide/installation
   user-guide/getting-started
   user-guide/your-new-page  # Add here
```

### Updating API Documentation

API documentation is auto-generated from docstrings. To update:

1. Edit docstrings in Python source files
2. Rebuild documentation: `make html`
3. Changes appear automatically

## Documentation Style Guide

### reStructuredText Formatting

**Headings:**

```rst
Page Title
==========

Section Heading
---------------

Subsection Heading
~~~~~~~~~~~~~~~~~~
```

**Code Blocks:**

```rst
.. code-block:: python

   def example():
       return "Hello, World!"
```

**Links:**

```rst
:doc:`relative-page`           # Link to other page
:ref:`anchor-name`             # Link to anchor
`External Link <url>`_         # External link
```

**Admonitions:**

```rst
.. note::
   This is a note.

.. warning::
   This is a warning.

.. danger::
   This is a danger notice.
```

### Docstring Format (Google Style)

```python
def function_name(param1: str, param2: int) -> bool:
    """Short one-line description.

    Longer description that provides more details about the function.
    Can span multiple lines.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is invalid.
        TypeError: When param2 is not an integer.

    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

## Troubleshooting

### Build Errors

**Error: "sphinx-build: command not found"**

Solution: Install Sphinx:

```bash
pip install sphinx sphinx-rtd-theme
```

**Error: Module import failures**

Solution: Make sure you're in the project root when building:

```bash
cd /path/to/Password-Manager-Local
cd documentation
make html
```

**Error: "WARNING: html_static_path entry '_static' does not exist"**

Solution: This is a harmless warning. The directory will be created automatically if needed.

### Fixing Warnings

**Docstring formatting warnings:**

* Fix indentation in docstrings
* Ensure code blocks are properly indented
* Check for proper blank lines

**Import errors for modules:**

* Ensure all dependencies are installed
* Check that module paths in `conf.py` are correct
* Some modules may be intentionally excluded

## Continuous Integration

Documentation is automatically built and deployed via GitHub Actions on every push to the main branch.

See `.github/workflows/docs.yml` for the CI/CD configuration.

## Hosting

Documentation can be hosted on:

* **GitHub Pages**: Free hosting for public repositories
* **Read the Docs**: Free hosting with automatic builds
* **Self-hosted**: Deploy HTML files to your own server

### GitHub Pages Setup

See `.github/workflows/docs.yml` for automatic deployment configuration.

Manual deployment:

```bash
# Build documentation
make html

# Deploy to gh-pages branch
git checkout gh-pages
cp -r build/html/* .
git add .
git commit -m "Update documentation"
git push origin gh-pages
```

Access at: `https://yourusername.github.io/password-manager/`

## Resources

* [Sphinx Documentation](https://www.sphinx-doc.org/)
* [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
* [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
* [Napoleon Extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) (Google/NumPy docstrings)

## Contributing to Documentation

Contributions to documentation are highly valued! To contribute:

1. Fork the repository
2. Create a branch for your documentation changes
3. Edit the relevant `.rst` files in `source/`
4. Build and preview your changes locally
5. Submit a pull request

See `source/developer/contributing.rst` for detailed contribution guidelines.

## License

Documentation is licensed under the same license as the Password Manager project (MIT License).
