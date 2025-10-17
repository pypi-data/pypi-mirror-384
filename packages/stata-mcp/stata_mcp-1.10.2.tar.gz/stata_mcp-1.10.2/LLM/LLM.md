# Stata-MCP - AI Assistant Project Introduction

## 🎯 Project Overview

Stata-MCP is a Stata statistical analysis assistant based on the MCP (Model Context Protocol) that enables AI to help users complete regression analysis and data statistics tasks. The project provides standardized tools and interfaces that allow AI to understand, generate, and execute Stata code.

**Core Value**: Enable LLMs to use Stata like professional statistical analysts for data analysis.

## 🏗️ Project Architecture

### Main Module Structure
```
stata-mcp/
├── src/stata_mcp/
│   ├── __init__.py              # Main module entry, MCP server configuration
│   ├── core/                    # Core functionality modules
│   │   ├── data_info/           # Data file analysis (CSV, DTA)
│   │   ├── rag/                 # RAG (Retrieval-Augmented Generation) system
│   │   └── stata/               # Stata-related core functionality
│   │       ├── stata_controller/ # Stata controller
│   │       ├── stata_do/        # Stata executor
│   │       └── stata_finder/    # Stata installation finder
│   ├── utils/                   # Utility modules
│   │   ├── Installer/          # Installer
│   │   ├── Prompt/             # Prompt management
│   │   └── usable.py           # Usability check
│   ├── cli/                    # Command line interface
│   ├── mode/                   # Different operation modes
│   │   ├── langchain_agent.py  # LangChain-based agent mode
│   │   └── pmp/                # Prompt-based mode
│   ├── agent_as_tool/          # Agent as tool integration
│   ├── evaluate/               # LLM evaluation module
│   └── sandbox/                # Sandbox environment
│       ├── core/               # Sandbox core
│       └── jupyter_manager/    # Jupyter kernel management
├── agent_examples/             # Agent mode examples
│   ├── openai/                 # OpenAI agent examples
│   ├── langchain/              # LangChain agent examples
│   └── task_prompt/            # Task prompt examples
├── main.py                     # Application entry
└── pyproject.toml             # Project configuration
```

### Core Functional Components

1. **StataFinder** (`src/stata_mcp/core/stata/stata_finder/`): Cross-platform Stata installation detection
   - macOS: Find through system paths
   - Windows: Find through registry and program files
   - Linux: Support custom path configuration

2. **StataController** (`src/stata_mcp/core/stata/stata_controller/`): Stata process control
   - Command execution management
   - Session state maintenance
   - Error handling mechanism

3. **StataDo** (`src/stata_mcp/core/stata/stata_do/`): Do file executor
   - Cross-platform do file execution
   - Log file management
   - Result output processing

4. **Prompt Management System** (`src/stata_mcp/utils/Prompt/`): AI prompt management
   - Multi-language support (English/Chinese)
   - Role definition and strategy prompts
   - Dynamic prompt generation

5. **Agent Mode** (`src/stata_mcp/mode/`): Autonomous analysis agents
   - `langchain_agent.py`: LangChain-based agent framework
   - `pmp/`: Prompt-based agent mode
   - Multi-turn conversation support

6. **Agent as Tool** (`src/stata_mcp/agent_as_tool/`): Tool integration
   - `StataAgent`: Embeddable Stata agent
   - Integration with other agent frameworks
   - Custom model configuration

7. **Evaluation Module** (`src/stata_mcp/evaluate/`): LLM performance evaluation
   - Automated scoring system
   - Quality assessment tools
   - Benchmark evaluation framework

8. **RAG System** (`src/stata_mcp/core/rag/`): Knowledge retrieval
   - Document indexing and search
   - Context-aware response generation
   - Statistical knowledge base

## 🛠️ How to Use

### Basic Configuration

Add to AI client configuration file:
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

### Core Tool Functions

AI can interact with Stata through the following tools:

1. **`stata_do(dofile_path, is_read_log=True)`** - Execute Stata do file
2. **`write_dofile(content)`** - Write Stata code to do file
3. **`append_dofile(original_dofile_path, content)`** - Append code to existing do file
4. **`get_data_info(data_path, vars_list=None, encoding="utf-8")`** - Get data file information
5. **`ssc_install(command, is_replace=True)`** - Install SSC package
6. **`help(cmd)`** - Get Stata command help
7. **`mk_dir(path)`** - Create directory
8. **`load_figure(figure_path)`** - Load figure
9. **`read_file(file_path, encoding="utf-8")`** - Read file contents

### Agent Mode Usage

#### Interactive Agent Mode
```bash
# Run agent mode with interactive interface
stata-mcp --agent

# Or use uvx
uvx stata-mcp --agent
```

#### Agent as Tool Integration
```python
from agents import Agent, Runner
from stata_mcp.agent_as_tool import StataAgent

# Initialize Stata agent
stata_agent = StataAgent()
sa_tool = stata_agent.as_tool()

# Create main agent with Stata tool
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    tools=[sa_tool],
)

# Run the agent
async def main(task: str):
    result = await Runner.run(agent, input=task)
    return result
```

### Evaluation System

The project includes a comprehensive LLM evaluation system:
- **Automated Scoring**: Rate analysis quality and accuracy
- **Benchmark Testing**: Standardized evaluation datasets
- **Performance Metrics**: Response time, accuracy, completeness
- **Comparative Analysis**: Model performance comparison

### RAG Integration

Knowledge retrieval capabilities:
- **Document Search**: Find relevant statistical literature
- **Context Awareness**: Provide domain-specific context
- **Knowledge Base**: Curated statistical methods and examples

### Prompt System

Built-in professional prompt templates:
- `stata_assistant_role()` - Stata assistant role definition
- `stata_analysis_strategy()` - Stata analysis strategy guide

## 🧩 Code Contribution Guide

### Development Environment Setup

1. Clone the project:
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Run tests:
```bash
uv run pytest tests/
```

### Code Standards

- **Type Annotations**: All functions must include complete type annotations
- **Documentation Comments**: Each function requires detailed English documentation comments
- **Naming Conventions**: Use descriptive variable names, follow PEP 8 standards
- **Error Handling**: Comprehensive exception handling and error messages

### Adding New Features

1. **New Tool Functions**: Add `@stata_mcp.tool()` decorator in `src/stata_mcp/__init__.py`
2. **New Prompts**: Add multi-language prompts in `src/stata_mcp/utils/Prompt/string.py`
3. **Platform Support**: Add implementations in corresponding platform modules

### Testing Requirements

- Unit tests covering core functionality
- Cross-platform compatibility testing
- Error scenario testing

## 🌟 Key Features

### Cross-Platform Support
- **macOS**: Automatic Stata installation path detection
- **Windows**: Support registry lookup and program file scanning
- **Linux**: Support custom path configuration

### Smart Data Parsing
- Support multiple data formats (.dta, .csv, .xlsx, .xls)
- Automatic data statistical analysis
- Missing value detection and panel data structure identification

### Professional Prompt System
- Multi-language role definitions
- Statistical analysis strategy guidance
- Error handling and debugging suggestions

## 🔧 Technology Stack

- **Python 3.11+**: Core programming language
- **MCP Protocol**: AI interaction protocol
- **LangChain**: Agent framework and tool integration
- **OpenAI Agents**: Advanced agent orchestration
- **pandas**: Data processing and analysis
- **pexpect**: Cross-platform process control
- **pathvalidate**: Security validation for file paths
- **dotenv**: Environment configuration management
- **FastMCP**: High-performance MCP server framework

## 🚀 Quick Start Example

```python
# AI can interact with Stata-MCP in the following ways

# 1. Create analysis do file
dofile_content = """
use "data.dta"
summarize
regress y x1 x2 x3
outreg2 using "results.txt", replace
"""

dofile_path = write_dofile(dofile_content)

# 2. Execute analysis
result = stata_do(dofile_path, is_read_log=True)
print(result["log_content"])

# 3. Get data information
data_info = get_data_info("data.dta")
print(data_info)
```

## 📊 Project Status

- ✅ macOS support (Completed)
- ✅ Windows support (Completed)
- 🔄 Linux support (In development)
- 🔄 More LLM integrations (Planned)
- 🔄 Performance optimization (Ongoing)

## 🤝 Contribution Methods

1. **Report Issues**: Submit bug reports or feature requests in GitHub Issues
2. **Submit Code**: Fork the project and submit Pull Requests
3. **Documentation Improvement**: Help improve documentation and examples
4. **Testing Verification**: Help test compatibility across different platforms

## 📞 Contact Information

- **Author**: Sepine Tam
- **Email**: sepinetam@gmail.com
- **GitHub**: https://github.com/sepinetam

## 📄 License

Apache License 2.0 - See [LICENSE](../LICENSE) file for details

---

**Stata-MCP**: Making AI your professional statistical analyst assistant!