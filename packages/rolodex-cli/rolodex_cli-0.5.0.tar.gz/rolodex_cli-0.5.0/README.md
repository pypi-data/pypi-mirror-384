# Rolodex

![License](https://img.shields.io/github/license/meddlin/rolodex)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)


A simple CRM for use at work.

## 🔥 Features
- ✅ Fast local database with SQLite
- 📝 Markdown-powered note taking
- 🔍 Rich search functionality
- 🎨 Colorful output with Rich
- 🏷️ Tag people with categories


![rolodex](./rolodex.png)

# Getting Started

Create virtual environment

- `python3 -m venv rolo`
- `source ./rolo/bin/activate`
- `pip install -r requirements.txt`

# Testing

Run this to fill the database with test data.

> `python3 db_load.py`

## Development

### Running tests

This project uses a src-layout. Install in editable mode, then run pytest:

```bash
python -m pip install -e .
pytest
```
