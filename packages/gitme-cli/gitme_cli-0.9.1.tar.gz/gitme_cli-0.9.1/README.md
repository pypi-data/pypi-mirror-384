
<div align="center">

## Generate git actions without interrupting your coding flow.

```bash
git add . && git commit -am "ugh... I vide all the way, what did I do? what do I even say here?" && git push -u origin dev
```
### ⬇️ 
```bash
gitme -u <your-remote-branch>
```

</div>

![gitme-cli-generate](https://github.com/wangjing0/gitme/raw/main/images/gitmecommit.png)

```bash
gitme show
```

![gitme-cli-show](https://github.com/wangjing0/gitme/raw/main/images/gitmeshow.png)

## Prerequisites

- Python 3.8+
- At least one AI provider API key:
  - Anthropic API key for Claude models, default is `claude-haiku-4-5`
  - OpenAI API key for GPT models, `openai` Python package for OpenAI support, default is `gpt-4o-mini`
- Git, all gitme commands must be run from within a git repository directory. If you're not in a git repository, you'll see an error message prompting you to initialize a git repository with `git init`.

## Features

- Analyzes git diffs to generate contextually relevant commit messages
- Detects untracked files and prompts to add them
- Supports staged changes only or all modified files
- Streamline your git workflow: add files, commit and push to upstream branch with user confirmation on every step, extremely lightweight and fast.
- **User input**: Option to edit and then confirm the messages before committing
- **Multiple AI Providers**: Choose between Anthropic or OpenAI, default is Anthropic
- Model options for both providers
- File changes and commit message history for logging, search and review at local
- Repository-specific message storage

## Installation

Install from PyPI:

```bash
pip install gitme-cli --upgrade
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/wangjing0/gitme.git
```

Or develop locally:

```bash
git clone https://github.com/wangjing0/gitme.git
cd gitme
pip install -e .
```

### AI Provider Setup

Choose one or both providers:

**For Anthropic Claude (default):**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

**For OpenAI GPT (Optional):**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### Basic Usage

```bash
# Generate message for staged changes (default - uses Anthropic Claude)
gitme

# Generate message for all changes
gitme -a

# Generate message and commit
gitme -c

# Generate message and commit and push to remote branch
gitme -u <remote-branch>
```

```bash
# Use OpenAI instead of Anthropic (default)
gitme -p openai

# Use OpenAI with specific model
gitme -p openai -m gpt-4o

# Use Anthropic with specific model
gitme -m claude-3-5-haiku-latest

# Combine with other options
gitme -p openai -c  # Use OpenAI and commit
```

### Message history and modified files

```bash
# Show previous messages (includes provider/model info)
gitme show

# Show last 5 messages
gitme show -n 5

# Show from all repositories
gitme show -r

# Clear history
gitme show --clear
```

**Enhanced Message History Display:**
```
[1] 2025-09-30 07:48:32
    💬 Message:
    Update default AI model to Claude Sonnet 4
    
    - Modified README.md
    🤖 AI Provider: Anthropic (claude-sonnet-4-5)
    📝 Files changed: 1

[2] 2025-09-30 07:45:54
    💬 Message:
    Update documentation images and references
    
    - Modified README.md
    - Added images/gitmecommit.png
    - Added images/gitmeshow.png
    - Cleaned up src/gitme/cli.py
    🤖 AI Provider: Anthropic (claude-sonnet-4-5)
    📝 Files changed: 4
```

## Options

### Generate Options

- `-s, --staged`: Analyze only staged changes
- `-a, --all`: Analyze all changes (staged and unstaged)
- `-p, --provider`: Choose AI provider (`anthropic` or `openai`, default: anthropic)
- `-m, --model`: Model to use (provider-specific)
- `-c, --commit`: Create commit with generated message (uses `git commit -a -m "auto-generated message"`)
- `-u, --upstream`:Analyze all changes and create commit and push to upstream branch (specify branch name)

### Show Options

- `-n, --limit`: Number of messages to show
- `-r, --all-repos`: Show messages from all repositories
- `--clear`: Clear message history

### Available Models

**Anthropic Claude:**
- `claude-haiku-4-5` (default)
- `claude-sonnet-4-5`
- `claude-3-5-haiku-latest`

**OpenAI GPT:**
- `gpt-4o-mini` (default when using OpenAI)
- `gpt-4o`
- `gpt-4`

## Privacy & Security Notice

⚠️ **Important**: When using `gitme` or `gitme generate`, your code changes will be sent to the selected AI provider (Anthropic Claude or OpenAI GPT) for processing. The tool does NOT send your entire codebase - only the diff contents of changed files.

**Please exercise caution when using this tool:**
- Avoid using it with repositories containing sensitive information, credentials, or proprietary code
- Review your changes before running the command to ensure no sensitive data is included
- Consider using `.gitignore` to exclude sensitive files from git tracking
- Be aware that different providers have different data handling policies
- Both Anthropic and OpenAI have their own privacy policies and data retention practices

## New Release

```bash
chmod +x release.sh && ./release.sh <version>
```
then upload to PyPI
```bash
twine upload dist/*
```

## Roadmap

- [x] User feedback on the generated message and modify accordingly
- [x] Add a way to add custom prompt to the AI provider
- [ ] add features: search messages and return commit_id, rewind to a previous commit, redo the commit message, etc.
- [ ] Local models with Ollama support

## Contributing

Contributions are welcome! Please feel free to submit a pull request. ❤️ @wangjing0 

## License

MIT