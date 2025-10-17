# BookBridge-MCP

[![GitHub](https://img.shields.io/badge/GitHub-BookBridge--MCP--Server-blue?logo=github)](https://github.com/Polly2014/BookBridge-MCP-Server)
[![PyPI](https://img.shields.io/pypi/v/bookbridge-mcp?logo=pypi&logoColor=white)](https://pypi.org/project/bookbridge-mcp/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue?logo=poetry)](https://python-poetry.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12.2+-green)](https://github.com/pydantic/fastmcp)
[![uv](https://img.shields.io/badge/uv-compatible-green?logo=python)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🎉 **Now available on PyPI!** Install with one simple command:
> ```bash
> uvx bookbridge-mcp
> ```
> 
> Or run directly from GitHub:
> ```bash
> uvx --from git+https://github.com/Polly2014/BookBridge-MCP-Server bookbridge-mcp
> ```

A powerful Model Context Protocol (MCP) server for Chinese-to-English book translation and document processing, built with FastMCP framework.

## 🌉 Overview

BookBridge-MCP provides a comprehensive solution for translating Chinese books and documents to English while preserving formatting and structure. The server follows a **client-side LLM architecture**, where the MCP server handles document processing and provides translation resources, while LLM interactions are performed on the client side.

## ✨ Key Features

- **📦 Available on PyPI**: Install with `uvx bookbridge-mcp`
- **Zero Installation Required**: Run directly from PyPI or GitHub using `uvx`
- **Document Processing**: Convert between Word (.docx) and Markdown formats
- **Smart Resource Management**: Organize and track translation projects
- **Professional Translation Prompts**: Specialized prompts for different content types
- **Client-Side LLM Architecture**: Clean separation between document processing and AI inference
- **Batch Processing**: Handle multiple documents efficiently
- **Format Preservation**: Maintain original document structure and formatting

## 🏗️ Architecture

```
┌─────────────────┐    MCP Protocol    ┌─────────────────┐
│                 │◄──────────────────►│                 │
│   MCP Client    │                    │  BookBridge     │
│                 │                    │  MCP Server     │
│  + LLM Calls    │                    │                 │
│  + UI/Logic     │                    │  + Tools        │
│                 │                    │  + Resources    │
│                 │                    │  + Prompts      │
└─────────────────┘                    └─────────────────┘
         │                                       │
         │                                       │
         v                                       v
┌─────────────────┐                    ┌─────────────────┐
│   OpenAI API    │                    │   Document      │
│   (Client-side) │                    │   Processing    │
│                 │                    │   (Server-side) │
└─────────────────┘                    └─────────────────┘
```

## ⚡ Quick Start

### Method 1: Using PyPI with uvx (Recommended! 🌟)

**The easiest way - published on PyPI!**

```bash
# Run directly from PyPI - simple and clean!
uvx bookbridge-mcp
```

**Update your MCP configuration** (`mcp.json`):
```json
{
  "servers": {
    "Book-Bridge-MCP": {
      "command": "uvx",
      "args": ["bookbridge-mcp"],
      "type": "stdio"
    }
  }
}
```

**Advantages:**
- ✅ Published on PyPI - stable releases
- ✅ No installation needed
- ✅ Automatic dependency management
- ✅ Fast and reliable
- ✅ Simple one-line configuration

---

### Method 2: Run Directly from GitHub (Latest Code)

**Always get the latest development version:**

```bash
# Run directly from GitHub
uvx --from git+https://github.com/Polly2014/BookBridge-MCP-Server bookbridge-mcp
```

**Update your MCP configuration** (`mcp.json`):
```json
{
  "servers": {
    "Book-Bridge-MCP": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Polly2014/BookBridge-MCP-Server",
        "bookbridge-mcp"
      ],
      "type": "stdio"
    }
  }
}
```

**Advantages:**
- ✅ Always the latest code
- ✅ No local installation required
- ✅ Automatic dependency management via uv
- ✅ Great for testing new features

---

### Method 3: Local Development Installation

#### 1. Install Dependencies
```bash
# Clone the repository
git clone https://github.com/Polly2014/BookBridge-MCP-Server.git
cd BookBridge-MCP-Server

# Automated setup (recommended)
python setup_poetry.py

# Or if Poetry is already installed
poetry install
```

#### 2. Test Environment  
```bash
# Verify installation
poetry run python test_environment.py

# Test MCP functionality
poetry run python test_simple.py
```

#### 3. Start Server
```bash
# Start the MCP server
poetry run python start.py
```

#### 4. Run Client Example
```bash
# Test with client example
poetry run python examples/client_example.py
```

#### 5. Development Commands
```bash
# Run tests: poetry run pytest
# Format code: poetry run black .
# Type checking: poetry run mypy src/
# All checks: make check (or make.bat check on Windows)
```

---

## 📦 Installation Methods Comparison

| Method | Command | Use Case | Installation Time |
|--------|---------|----------|-------------------|
| **PyPI** 🌟 | `uvx bookbridge-mcp` | General use, production | ⚡ Fastest |
| **GitHub** | `uvx --from git+https://... bookbridge-mcp` | Latest features, testing | ⚡ Fast |
| **Local** | `poetry install && poetry run ...` | Development, contributions | 🐢 Requires setup |

---

### Method 4: Traditional pip Install (Alternative)

If you prefer traditional pip installation:

```bash
# Install from PyPI
pip install bookbridge-mcp

# Run the server (both commands work)
bookbridge-mcp
# or
bookbridge-server
```

**Note**: With `uvx`, you don't need to manually install - it handles everything automatically!

---

## 🚀 Detailed Installation

### 1. Prerequisites

- Python 3.10 or higher
- Poetry (recommended) or pip

### 2. Installation

#### Option A: Using Poetry (Recommended)

```bash
git clone https://github.com/your-repo/BookBridge-MCP.git
cd BookBridge-MCP

# Automated setup (installs Poetry if needed)
python setup_poetry.py

# Or manual setup if Poetry is already installed
poetry install --with dev --with client
```

#### Option B: Using pip

```bash
git clone https://github.com/your-repo/BookBridge-MCP.git
cd BookBridge-MCP
pip install -r requirements.txt
```

### 3. Start the MCP Server

#### Using Poetry:
```bash
poetry run python start.py
# or
poetry run bookbridge-server
# or using make commands
make run              # Unix/Linux/Mac
make.bat run          # Windows
```

#### Using pip:
```bash
python start.py
```

The server will start and listen for MCP connections on the configured port.

### 3. Client-Side Integration

The MCP server provides tools, resources, and prompts. Your client application handles the LLM interactions:

```python
from examples.client_example import BookBridgeClient

# Initialize client with your OpenAI API key
client = BookBridgeClient(api_key="your_openai_api_key")

# Translate a document
result = await client.translate_document(
    file_path="./my_chinese_book.docx",
    content_type="academic"  # or "general", "technical", "creative"
)

# Save the translation
output_path = await client.save_translation(
    result, 
    "./output/translated_book.md"
)
```

## 🛠️ MCP Server Capabilities

### Tools

1. **`process_document`** - Convert documents between Word and Markdown formats
2. **`list_documents`** - List and manage documents in the project
3. **`get_document_info`** - Get detailed information about a specific document
4. **`create_translation_project`** - Set up new translation projects
5. **`get_translation_metrics`** - Calculate translation quality metrics

### Resources

- **Document Registry** - Track all processed documents
- **Project Files** - Access source and output documents
- **Translation History** - View previous translations

### Prompts

- **General Translation** - For everyday content
- **Academic Translation** - For scholarly and research texts
- **Technical Translation** - For documentation and manuals
- **Creative Translation** - For literary and creative works

## 📁 Project Structure

```
BookBridge-MCP/
├── server.py                 # Main MCP server
├── start.py                  # Server startup script
├── requirements.txt          # Dependencies
├── config.env               # Configuration
├── src/
│   ├── document_processor.py # Document conversion
│   ├── resource_manager.py   # File and project management
│   ├── prompts.py            # Translation prompts
│   └── translator.py         # Translation utilities
├── examples/
│   └── client_example.py     # Client implementation example
├── input_documents/          # Source documents
├── output_documents/         # Translated documents
└── temp_documents/           # Temporary files
```

## 🔧 Configuration

### MCP Client Configuration

You can configure your MCP client in three ways:

#### Option 1: Using uvx with GitHub (Recommended)

Edit your `mcp.json` file:

```json
{
  "servers": {
    "Book-Bridge-MCP": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Polly2014/BookBridge-MCP-Server",
        "bookbridge-server"
      ],
      "type": "stdio"
    }
  }
}
```

**Advantages:**
- ✅ No local installation required
- ✅ Always runs the latest version from GitHub
- ✅ Automatic dependency management via uv
- ✅ Clean and simple configuration

#### Option 2: Using Local Installation

```json
{
  "servers": {
    "Book-Bridge-MCP": {
      "command": "python",
      "args": [
        "D:\\path\\to\\BookBridge-MCP\\server.py"
      ],
      "cwd": "D:\\path\\to\\BookBridge-MCP",
      "type": "stdio"
    }
  }
}
```

#### Option 3: Using npx-like syntax (if published to PyPI)

```json
{
  "servers": {
    "Book-Bridge-MCP": {
      "command": "uvx",
      "args": ["bookbridge-mcp"],
      "type": "stdio"
    }
  }
}
```

### Server Configuration

Edit `config.env` to customize settings:

```env
# Document Processing Settings
INPUT_DIR=./input_documents
OUTPUT_DIR=./output_documents
TEMP_DIR=./temp_documents

# Translation Settings (for client reference)
SOURCE_LANGUAGE=chinese
TARGET_LANGUAGE=english

# MCP Server Settings
SERVER_NAME=BookBridge-MCP
SERVER_VERSION=1.0.0
```

## �️ Development Workflow

### Using Poetry (Recommended)

Poetry provides better dependency management and development workflow:

```bash
# Complete development setup
poetry install --with dev --with client
poetry run pre-commit install

# Development commands using Poetry
poetry run python start.py          # Start server
poetry run pytest                   # Run tests  
poetry run pytest --cov=src         # Tests with coverage
poetry run black .                  # Format code
poetry run isort .                  # Sort imports
poetry run flake8 src/              # Lint code
poetry run mypy src/                # Type checking
```

### Using Make Commands

For convenience, use the provided Makefile (Unix/Linux/Mac) or make.bat (Windows):

```bash
# Unix/Linux/Mac
make dev-setup      # Complete development setup
make run            # Start server
make test           # Run tests
make format         # Format code
make lint           # Lint code
make type-check     # Type checking
make check          # Run all checks
make clean          # Clean temporary files

# Windows
make.bat dev-setup  # Complete development setup
make.bat run        # Start server
make.bat test       # Run tests
make.bat format     # Format code
make.bat lint       # Lint code
make.bat type-check # Type checking
make.bat check      # Run all checks
make.bat clean      # Clean temporary files
```

### Package Management

```bash
# Add new dependency
poetry add package_name

# Add development dependency
poetry add --group dev package_name

# Add client dependency (optional for client usage)
poetry add --group client package_name

# Update dependencies
poetry update

# Show installed packages
poetry show

# Environment information
poetry env info
```

## �💡 Usage Examples

### Basic Document Translation

```python
# Process and translate a Word document
result = await client.translate_document(
    file_path="./books/chinese_novel.docx",
    content_type="creative"
)

print(f"Translated {result['summary']['original_words']} words")
print(f"Used {result['summary']['token_usage']} tokens")
```

### Batch Processing

```python
# Process multiple documents
documents = ["doc1.docx", "doc2.md", "doc3.docx"]

for doc in documents:
    result = await client.translate_document(doc, "academic")
    await client.save_translation(result, f"./output/{doc}_translated.md")
```

### Custom Content Types

You can request specific translation prompts from the server:

```python
# Get specialized prompt for technical content
prompt = await client.get_translation_prompt("technical")

# Use prompt for custom translation
translation = await client.translate_content(
    content="技术文档内容...",
    content_type="technical"
)
```

## 🎯 Client-Side LLM Benefits

1. **Flexibility**: Clients can use any LLM provider or model
2. **Security**: API keys stay on the client side
3. **Scalability**: Server focuses on document processing
4. **Customization**: Clients can customize translation parameters
5. **Cost Control**: Clients manage their own LLM usage

## 📊 Translation Quality Features

- **Smart Chunking**: Preserve document structure when splitting large texts
- **Format Preservation**: Maintain headers, lists, and emphasis
- **Metrics Calculation**: Analyze translation quality and completeness
- **Content-Type Optimization**: Specialized prompts for different text types

## 🧪 Testing

### Running Tests

Using Poetry:

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
poetry run pytest tests/test_document_processor.py

# Run tests in verbose mode
poetry run pytest -v

# Quick test (stop on first failure)
poetry run pytest -x
```

Using Make commands:

```bash
# Unix/Linux/Mac
make test
make test-coverage
make quick-test

# Windows  
make.bat test
make.bat test-coverage
make.bat quick-test
```

### Running Examples

Test the client example:

```bash
# Using Poetry
poetry run python examples/client_example.py

# Using Make
make client-example        # Unix/Linux/Mac
make.bat client-example    # Windows
```

### Development Testing

```bash
# Run architecture tests
poetry run python test_architecture.py

# Test individual components
poetry run python test_components.py
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/BookBridge-MCP.git
   cd BookBridge-MCP
   ```
3. Set up development environment:
   ```bash
   # Complete setup with Poetry
   make dev-setup           # Unix/Linux/Mac
   make.bat dev-setup       # Windows
   
   # Or manually
   poetry install --with dev --with client
   poetry run pre-commit install
   ```

### Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run quality checks:
   ```bash
   make check              # Unix/Linux/Mac
   make.bat check          # Windows
   ```
4. Add tests for new functionality
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to your fork: `git push origin feature/your-feature`
7. Submit a pull request

### Code Quality

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **pytest** for testing
- **pre-commit** for automated checks

All checks must pass before merging.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **PyPI Package**: https://pypi.org/project/bookbridge-mcp/
- **GitHub Repository**: https://github.com/Polly2014/BookBridge-MCP-Server
- **Issues**: https://github.com/Polly2014/BookBridge-MCP-Server/issues
- **Discussions**: https://github.com/Polly2014/BookBridge-MCP-Server/discussions

## 🆘 Support

For issues and questions:

1. Check the [examples directory](examples/) for usage patterns
2. Review the [installation guide](INSTALLATION.md) for detailed setup instructions
3. Check [MCP configuration examples](MCP_CONFIG_EXAMPLES.md) for different setups
4. Review the MCP server logs for debugging
5. Open an [issue on GitHub](https://github.com/Polly2014/BookBridge-MCP-Server/issues) for bugs or feature requests

## 📚 Documentation

- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [Quick Start](QUICKSTART.md) - Quick reference card
- [MCP Configuration Examples](MCP_CONFIG_EXAMPLES.md) - Configuration examples
- [Changelog](CHANGELOG.md) - Version history
- [Publishing Guide](PYPI_PUBLISHING.md) - For maintainers

## ⭐ Show Your Support

If you find BookBridge-MCP helpful, please consider:
- ⭐ Starring the [GitHub repository](https://github.com/Polly2014/BookBridge-MCP-Server)
- 📢 Sharing with others who might benefit
- 🐛 Reporting issues or suggesting features
- 🤝 Contributing code or documentation

---

**BookBridge-MCP**: Bridging languages, preserving meaning. 🌉📚
