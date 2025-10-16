# Lintro Documentation Hub

Welcome to the Lintro documentation! This hub provides comprehensive guides for using, configuring, and contributing to Lintro.

> **Quick Start**: If you're new to Lintro, start with the [main README](../README.md) for installation and basic usage, then return here for detailed guides.

## 📚 Documentation Structure

### For Users

**New to Lintro?** Start here:

- **[Getting Started](getting-started.md)** - Installation, first steps, and basic usage
- **[Configuration Guide](configuration.md)** - Tool configuration and customization
- **[Docker Usage](docker.md)** - Using Lintro with Docker

**Integration Guides:**

- **[GitHub Integration](github-integration.md)** - CI/CD setup with GitHub Actions
- **[Tool Analysis](tool-analysis/)** - Detailed tool comparisons and capabilities

### For Developers

**Contributing to Lintro:**

- **[Contributing Guide](contributing.md)** - Development setup and contribution guidelines

**Reference Documentation:**

- **[Style Guide](style-guide.md)** - Coding standards and best practices
- **[Coverage Setup](coverage-setup.md)** - Test coverage configuration reference
- **[Self-Use Documentation](lintro-self-use.md)** - How Lintro uses itself

## 🚀 Quick Links

### Most Common Tasks

| Task                 | Documentation                                                             |
| -------------------- | ------------------------------------------------------------------------- |
| **Install Lintro**   | [Main README → Installation](../README.md#installation)                   |
| **First time usage** | [Main README → Quick Start](../README.md#quick-start)                     |
| **Docker setup**     | [Docker Usage → Quick Start](docker.md#quick-start)                       |
| **GitHub Actions**   | [GitHub Integration → Quick Setup](github-integration.md#quick-setup)     |
| **Configure tools**  | [Configuration → Tool Configuration](configuration.md#tool-configuration) |
| **Add new tool**     | [Contributing → How to Add a Tool](contributing.md#how-to-add-a-new-tool) |

### By Use Case

**📋 Code Quality Checking:**

```bash
lintro check
```

→ [Main README → Basic Usage](../README.md#basic-usage)

**🛠️ Auto-fixing Issues:**

```bash
lintro format
```

→ [Main README → Advanced Usage](../README.md#advanced-usage)

**🐳 Containerized Development:**

```bash
./docker-lintro.sh check
```

→ [Docker Usage Guide](docker.md)

**⚙️ CI/CD Integration:**
→ [GitHub Integration Guide](github-integration.md)

## 📖 Documentation by Audience

### End Users

**Goal: Use Lintro effectively in projects**

1. [Main README](../README.md) - Quick start and basic usage
2. [Configuration](configuration.md) - Customize for your project
3. [Docker Usage](docker.md) - Containerized workflows (optional)
4. [GitHub Integration](github-integration.md) - CI/CD automation (optional)

### Project Maintainers

**Goal: Integrate Lintro into team workflows**

1. [GitHub Integration](github-integration.md) - Set up automated quality checks
2. [Configuration](configuration.md) - Project-wide configuration
3. [Tool Analysis](tool-analysis/) - Understand tool capabilities
4. [Docker Usage](docker.md) - Standardized environments

### Contributors & Developers

**Goal: Contribute to or extend Lintro**

1. [Contributing Guide](contributing.md) - Development setup and guidelines
2. [Style Guide](style-guide.md) - Code quality standards
3. [Tool Analysis](tool-analysis/) - Understanding tool integration patterns
4. [Self-Use Documentation](lintro-self-use.md) - How we use our own tool

## 🛠️ Supported Tools

| Tool           | Language/Format  | Purpose                 | Documentation                                              |
| -------------- | ---------------- | ----------------------- | ---------------------------------------------------------- |
| **Ruff**       | Python           | Linting & Formatting    | [Config Guide](configuration.md#ruff-configuration)        |
| **Black**      | Python           | Formatting (Post-check) | [Config Guide](configuration.md#post-checks-configuration) |
| **Darglint**   | Python           | Docstring Validation    | [Analysis](tool-analysis/darglint-analysis.md)             |
| **Bandit**     | Python           | Security Linting        | [Analysis](tool-analysis/bandit-analysis.md)               |
| **Prettier**   | JS/TS/JSON/CSS   | Code Formatting         | [Analysis](tool-analysis/prettier-analysis.md)             |
| **Yamllint**   | YAML             | Syntax & Style          | [Config Guide](configuration.md#yamllint-configuration)    |
| **Actionlint** | GitHub Workflows | Workflow Linting        | [Analysis](tool-analysis/actionlint-analysis.md)           |
| **Hadolint**   | Dockerfile       | Best Practices          | [Config Guide](configuration.md#hadolint-configuration)    |

## 📋 Command Reference

### Basic Commands

```bash
# Check code for issues
lintro check

# Auto-fix issues where possible
lintro format

# List available tools
lintro list-tools [OPTIONS]
```

### Common Options

```bash
--output-format grid        # Use grid output (recommended)
--tools ruff,prettier        # Run specific tools only
--output results.txt         # Save output to file
--group-by [file|code|auto]  # Group issues by type
--exclude "venv,node_modules" # Exclude patterns
```

### Docker Commands

```bash
# Using the shell script (recommended)
./docker-lintro.sh check

# Using docker directly
docker run --rm -v "$(pwd):/code" lintro:latest check
```

## 🔍 Finding Information

### Search by Topic

- **Installation:** [Getting Started](getting-started.md#installation)
- **Configuration:** [Configuration Guide](configuration.md)
- **Docker:** [Docker Usage](docker.md)
- **CI/CD:** [GitHub Integration](github-integration.md)
- **Contributing:** [Contributing Guide](contributing.md)
- **Tool Comparison:** [Tool Analysis](tool-analysis/)

### Search by Error/Issue

- **"Tool not found":** [Getting Started → Troubleshooting](getting-started.md#troubleshooting)
- **"Permission denied":** [Docker Usage → Troubleshooting](docker.md#troubleshooting)
- **"Configuration not working":** [Configuration → Troubleshooting](configuration.md#troubleshooting-configuration)
- **"Workflow not triggering":** [GitHub Integration → Troubleshooting](github-integration.md#troubleshooting)

## 🆕 Recent Updates

- **Security audit framework** - Comprehensive security verification for workflows and scripts
- **DRY consolidation** - Reduced duplicate patterns across workflows and actions
- **Shell-free design** - Moved inline shell commands to dedicated scripts
- **Environment standardization** - Consistent variable usage across all workflows
- **Documentation restructure** - Improved organization and navigation
- **Enhanced tool analysis** - Detailed comparisons with core tools

## 🤝 Contributing to Documentation

Found an issue with the documentation? Want to improve it?

1. **Small fixes:** Edit files directly and submit a PR
2. **New content:** Follow the [Contributing Guide](contributing.md)
3. **Feedback:** Open an issue with suggestions

### Documentation Standards

- **Clear headings** with consistent hierarchy
- **Code examples** for all instructions
- **Cross-references** between related topics
- **Up-to-date links** and accurate information

---

**Need help?** Check the specific guide for your use case, or open an issue on GitHub if you can't find what you're looking for! 🚀
