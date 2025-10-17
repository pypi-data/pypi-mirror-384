#!/bin/bash

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }

# Check if command exists
command_exists() {
    command -v "$1" \>/dev/null 2\>\&1
}

# Check Python version is 3.11+
check_python_version() {
    if python3 -c "import sys; exit(0 if sys.version_info \>\= (3, 11) else 1)" 2\>/dev/null; then
        return 0
    fi
    return 1
}

# Run stata-mcp with uv
run_with_uv() {
    green "Found uv, running stata-mcp with uvx..."
    yellow "Checking stata-mcp version..."
    if uvx stata-mcp --version; then
        green "Version check successful! Starting agent mode..."
        uvx stata-mcp -a
    else
        red "Version check failed, trying to install stata-mcp..."
        if uv pip install -e .; then
            green "Installation successful! Starting agent mode..."
            uvx stata-mcp -a
        else
            red "Installation failed, please check error messages"
            exit 1
        fi
    fi
}

# Run stata-mcp with Python
run_with_python() {
    green "Running stata-mcp with Python..."
    yellow "Checking stata-mcp version..."
    if stata-mcp --version; then
        green "Version check successful! Starting agent mode..."
        stata-mcp -a
    else
        red "stata-mcp not installed, installing..."
        if pip install -e .; then
            green "Installation successful! Starting agent mode..."
            stata-mcp -a
        else
            red "Installation failed, please check error messages"
            exit 1
        fi
    fi
}

# Install uv
install_uv() {
    yellow "Installing uv..."
    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Reload shell configuration
        source "$HOME/.cargo/env" 2\>/dev/null || true
    else
        red "Error: curl is required to install uv, please install curl first"
        exit 1
    fi
}

# Main function
main() {
    green "=== stata-mcp Startup Script ==="

    # Check if uv is available
    if command_exists uv; then
        run_with_uv
    else
        yellow "uv not found"
        read -r -p "Install uv? (y/n): " install_uv_choice

        if [[ "$install_uv_choice" =~ ^[Yy]$ ]]; then
            install_uv
            if command_exists uv; then
                run_with_uv
            else
                red "uv installation failed"
                exit 1
            fi
        else
            yellow "User chose not to install uv, checking Python environment..."
            if command_exists python3; then
                if check_python_version; then
                    green "Python 3.11+ is installed"
                    run_with_python
                else
                    red "Error: Python 3.11 or higher is required"
                    yellow "Please visit https://www.python.org/downloads/ to download the latest version"
                    open "https://www.python.org/downloads/" 2\>/dev/null || true
                    exit 1
                fi
            else
                red "Error: Python3 not found"
                yellow "Please visit https://www.python.org/downloads/ to download Python"
                open "https://www.python.org/downloads/" 2\>/dev/null || true
                exit 1
            fi
        fi
    fi
}

# Run main function
main