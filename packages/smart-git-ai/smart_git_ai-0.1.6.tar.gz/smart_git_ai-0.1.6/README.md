# smartgit

<div align="center">

**AI-powered git commit message generator and intelligent git utility toolkit**

> Package: `smart-git-ai` | Command: `smartgit`

[![PyPI version](https://badge.fury.io/py/smart-git-ai.svg)](https://badge.fury.io/py/smart-git-ai)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/SifatIbna/smart-git-ai/workflows/CI/badge.svg)](https://github.com/SifatIbna/smart-git-ai/actions)
[![codecov](https://codecov.io/gh/SifatIbna/smart-git-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/SifatIbna/smart-git-ai)

*Never write commit messages manually again. Let Claude AI understand your changes and generate meaningful, conventional commit messages.*

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## Table of Contents

- [Why smartgit?](#why-smartgit)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Generate Commit Messages](#generate-commit-messages)
  - [Git Hooks Integration](#git-hooks-integration)
  - [Git Utilities](#git-utilities)
  - [Configuration](#configuration)
- [Configuration Files](#configuration-files)
- [Commit Message Format](#commit-message-format)
- [Examples](#examples)
- [Requirements](#requirements)
- [Development](#development)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Why smartgit?

Writing good commit messages is hard and time-consuming. `smartgit` solves this by:

- **Understanding your code changes** using Claude AI to analyze diffs
- **Following best practices** automatically with Conventional Commits format
- **Saving time** by generating messages in seconds
- **Maintaining consistency** across your entire team
- **Providing helpful utilities** to manage your git workflow

---

## Features

### 🤖 AI-Powered Commit Messages

- **Intelligent Analysis**: Claude AI reads your staged changes and understands context
- **Conventional Commits**: Automatically formatted with proper type, scope, and description
- **Multiple Providers**: Support for Anthropic Claude and OpenAI models
- **Customizable**: Add context, configure styles, and adjust behavior

### 🔗 Seamless Git Integration

- **Git Hooks**: Install `prepare-commit-msg` hook for automatic message generation
- **Native Workflow**: Works with standard `git commit` commands
- **Editor Support**: Opens your default git editor for review and editing
- **Safe and Reversible**: Easy to install/uninstall hooks with backups

### 🛠️ Powerful Git Utilities

When you need more than commits, `smartgit` provides helpful utilities:

| Utility | Description |
|---------|-------------|
| `undo` | Safely undo last commit (keep or discard changes) |
| `cleanup` | Remove local branches that have been merged |
| `stale` | Find branches not updated in N days |
| `large-files` | Locate files above size threshold |
| `suggest-gitignore` | Auto-suggest .gitignore entries for untracked files |
| `force-push-safe` | Force push with lease to prevent overwriting |
| `fixup` | Create fixup commits for autosquashing |
| `worktree` | Manage git worktrees for parallel development |

---

## Installation

### From PyPI (Recommended)

```bash
pip install smart-git-ai
```

### From Source

```bash
git clone https://github.com/SifatIbna/smart-git-ai.git
cd smart-git-ai
pip install -e .
```

### Verify Installation

```bash
smartgit --version
```

---

## Quick Start

### 1️⃣ Set up your API key

Get your API key from [Anthropic Console](https://console.anthropic.com/):

**Option 1: Export environment variable (recommended)**
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export ANTHROPIC_API_KEY="your_api_key_here"
```

**Option 2: Use .smartgit.yml config file**
```bash
# Create config file in your project
echo "api_key: your_api_key_here" > .smartgit.yml
```

**Option 3: Use .env with SMARTGIT_API_KEY**
```bash
# Works for both Anthropic and OpenAI
echo "SMARTGIT_API_KEY=your_api_key_here" > .env
```

### 2️⃣ Generate your first AI commit

```bash
# Stage your changes
git add .

# Generate and commit with AI
smartgit generate

# Or preview without committing
smartgit generate --dry-run
```

### 3️⃣ Install git hooks (optional but recommended)

```bash
# Install prepare-commit-msg hook
smartgit install

# Now regular git commit will use AI automatically
git commit
```

That's it! 🎉 You're now using AI-powered commit messages.

---

## Usage

### Generate Commit Messages

```bash
# Generate AI commit message for staged changes
smartgit generate

# Add context to help the AI understand your changes
smartgit generate --context "Refactored authentication to use JWT"

# Preview without committing
smartgit generate --dry-run

# Skip editor confirmation and commit immediately
smartgit generate --no-edit
```

### Git Hooks Integration

```bash
# Install hooks
smartgit install

# Install with force (overwrite existing hooks)
smartgit install --force

# Check installation status
smartgit status

# Uninstall hooks
smartgit uninstall

# Uninstall and restore previous backup
smartgit uninstall --restore
```

### Git Utilities

```bash
# Undo last commit (keep changes staged)
smartgit utils undo

# Undo last commit and discard changes
smartgit utils undo --hard

# Clean up merged branches
smartgit utils cleanup

# Find stale branches (not updated in 30 days)
smartgit utils stale
smartgit utils stale --days 60

# Find large files (>10MB)
smartgit utils large-files
smartgit utils large-files --size 5.0

# Suggest .gitignore entries for untracked files
smartgit utils suggest-gitignore

# Safe force push (force-with-lease)
smartgit utils force-push-safe

# Create fixup commit
smartgit utils fixup <commit-hash>

# Get help for any utility
smartgit utils --help
```

### Configuration

```bash
# View current configuration
smartgit config show

# Set configuration values
smartgit config set provider anthropic
smartgit config set model claude-3-5-sonnet-20241022
smartgit config set commit_style conventional

# Set global configuration (applies to all repos)
smartgit config set provider anthropic --global

# Reset configuration to defaults
smartgit config reset
```

---

## Configuration Files

`smartgit` supports hierarchical configuration (in order of priority):

1. **Repository Config** (highest priority): `.smartgit.yml` in your repo root
2. **User Config**: `~/.config/smartgit/config.yml`
3. **Environment Variables**: Shell exports or `.env` file

### Example Configuration

Create a `.smartgit.yml` file in your repository:

```yaml
# AI Provider Configuration
provider: anthropic  # or openai
api_key: your_api_key_here  # optional, can use env var instead
model: claude-3-5-sonnet-20241022

# Commit Message Settings
commit_style: conventional  # or simple
max_subject_length: 72
context_lines: 3

# Behavior Settings
auto_add: false
hook_enabled: true
max_diff_size: 10000
```

### Environment Variables

**Recommended: Provider-specific API keys (export only)**
```bash
# For Anthropic (default provider)
export ANTHROPIC_API_KEY=your_anthropic_api_key

# For OpenAI (if using OpenAI provider)
export OPENAI_API_KEY=your_openai_key
export SMARTGIT_PROVIDER=openai
```

**Alternative: Generic SMARTGIT_* variables (works in .env files)**
```bash
# In .env file or export
SMARTGIT_API_KEY=your_api_key_here
SMARTGIT_PROVIDER=anthropic  # or openai
SMARTGIT_MODEL=claude-3-5-sonnet-20241022
SMARTGIT_COMMIT_STYLE=conventional
```

> **Note**: Provider-specific keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) work best when exported as environment variables. Use `SMARTGIT_API_KEY` if you prefer `.env` files.

---

## Commit Message Format

`smartgit` generates commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add JWT authentication` |
| `fix` | Bug fix | `fix(api): handle null response from endpoint` |
| `docs` | Documentation changes | `docs(readme): add installation instructions` |
| `style` | Code style changes | `style(components): format with prettier` |
| `refactor` | Code refactoring | `refactor(db): optimize query performance` |
| `perf` | Performance improvements | `perf(api): cache frequent database queries` |
| `test` | Adding or updating tests | `test(auth): add unit tests for login flow` |
| `build` | Build system changes | `build(deps): upgrade to webpack 5` |
| `ci` | CI configuration changes | `ci(github): add automated release workflow` |
| `chore` | Maintenance tasks | `chore(deps): update dependencies` |

---

## Examples

### Example 1: Feature Addition

```bash
$ git add src/auth.py
$ smartgit generate

✨ Analyzing staged changes...

Generated Commit Message:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ feat(auth): add JWT token authentication         ┃
┃                                                   ┃
┃ Implement JWT-based authentication system with   ┃
┃ token generation and validation.                  ┃
┃                                                   ┃
┃ - Add token generation utility                   ┃
┃ - Add token validation middleware                ┃
┃ - Add refresh token support                      ┃
┃ - Configure token expiration settings            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Create commit with this message? (y/n): y
✓ Commit created successfully!
```

### Example 2: Using Utilities

```bash
$ smartgit utils stale --days 30

🔍 Finding stale branches...

Branches not updated in 30 days:
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Branch                ┃ Last Updated  ┃ Days Ago  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ feature/old-api       │ 2024-11-15    │ 45        │
│ bugfix/temp-fix       │ 2024-11-20    │ 40        │
│ experiment/new-design │ 2024-10-10    │ 80        │
└───────────────────────┴───────────────┴───────────┘

💡 Tip: Use 'git branch -D <branch>' to delete local branches
```

### Example 3: Status Check

```bash
$ smartgit status

📊 Git AI Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Repository: smartgit
Branch: main
Status: Clean ✓

Git Hooks:
  ✓ prepare-commit-msg installed
  Location: .git/hooks/prepare-commit-msg

AI Configuration:
  Provider: anthropic
  Model: claude-3-5-sonnet-20241022
  Commit Style: conventional

API Key: ✓ Found
```

---

## Requirements

- **Python**: 3.8 or higher
- **Git**: 2.0 or higher
- **API Key**: [Anthropic API key](https://console.anthropic.com/) (or OpenAI if using that provider)

---

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/SifatIbna/smart-git-ai.git
cd smart-git-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=smartgit --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_repository.py
```

### Code Quality

```bash
# Format code
python -m ruff format src tests

# Lint code
python -m ruff check src tests

# Type check
python -m mypy src

# Run all checks (what CI runs)
python -m ruff check --fix src tests && \
python -m ruff format src tests && \
python -m mypy src && \
pytest --cov=smartgit
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Detailed getting started guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[RELEASING.md](RELEASING.md)** - Release process

---

## Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Run tests and linting** (`pytest && ruff check .`)
5. **Commit your changes** (use `smartgit generate` 😉)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Development Philosophy

- **Quality over Speed**: We prioritize well-tested, maintainable code
- **User First**: Features should solve real problems for real developers
- **Keep It Simple**: Prefer simple solutions over complex abstractions
- **Document Everything**: Code should be self-documenting, but docs help

---

## Troubleshooting

### "Not a git repository" error

Make sure you're inside a git repository:
```bash
git init  # Initialize a new repository if needed
```

### "API key not found" error

Ensure your API key is properly set:
```bash
# Check if it's set
echo $ANTHROPIC_API_KEY

# Option 1: Export as environment variable (recommended)
export ANTHROPIC_API_KEY="your_key_here"

# Option 2: Add to .smartgit.yml
echo "api_key: your_key_here" > .smartgit.yml

# Option 3: Use SMARTGIT_API_KEY in .env
echo "SMARTGIT_API_KEY=your_key_here" > .env
```

### Hook not working

Reinstall hooks with force flag:
```bash
smartgit uninstall
smartgit install --force
```

### "Large diff" warning

If your changes are too large:
```bash
# Commit in smaller chunks
git add specific-file.py
smartgit generate

# Or increase the limit
smartgit config set max_diff_size 20000
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/SifatIbna/smart-git-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SifatIbna/smart-git-ai/discussions)
- **Email**: sifatibna@gmail.com

---

## Roadmap

- [ ] Support for more AI providers (Google Gemini, local models)
- [ ] Interactive mode for commit message editing
- [ ] Commit message templates and customization
- [ ] Integration with GitHub CLI for PR descriptions
- [ ] VS Code extension
- [ ] Commit message translation to different languages
- [ ] Team collaboration features (shared configs, style guides)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Powered by** [Anthropic's Claude](https://www.anthropic.com/) - State-of-the-art AI for understanding code
- **Inspired by** [Conventional Commits](https://www.conventionalcommits.org/) - A specification for meaningful commit messages
- **Built with**:
  - [Click](https://click.palletsprojects.com/) - Beautiful command line interfaces
  - [Rich](https://rich.readthedocs.io/) - Rich text and formatting in terminal
  - [GitPython](https://gitpython.readthedocs.io/) - Git interface library
  - [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) - Official Anthropic API client

---

<div align="center">

**Made with ❤️ by Master Shifu, for developers**

If you find this project helpful, please consider giving it a ⭐️ on GitHub!

[⬆ Back to Top](#smartgit)

</div>
