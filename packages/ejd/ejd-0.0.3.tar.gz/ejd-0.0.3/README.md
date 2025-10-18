# SDLC-Automation
Graduation project - CLI Backend for Static Issue Analysis and Fixing

## Overview
This project provides a command-line interface (CLI) tool called `ejd` that helps developers analyze and fix static issues in their code using configurable rule sets and LLM integration.

## Installation

```bash
pip install -e .
```

## Usage

### Basic Command Structure
```bash
ejd -si fix "path/to/your/file.py"
```

### Interactive Workflow
1. Run the command with your source file path
2. The tool will prompt you to enter a rule set file path
3. Both files are validated and loaded into variables
4. The data is prepared for LLM processing

### Example Usage
```bash
# Fix static issues in a Python file
ejd -si fix "src/main.py"

# The tool will then prompt:
# 📋 Please enter the path to the rule set file: rules/python_rules.txt
```

## Features

- ✅ File validation for both source and rule set files
- 🔧 Interactive rule set path input with validation
- 💾 Automatic loading of file contents into variables
- 🤖 Ready-to-use data structure for LLM integration
- � Non-destructive workflow - creates fixed files while preserving originals
- �🚀 Extensible architecture for future enhancements

## Gemini Flash 2.5 Integration

This tool is integrated with Google's Gemini Flash 2.5 model for intelligent static code analysis and automated fixing.

### Setup

1. **Install dependencies** (automatically handled during installation):
   ```bash
   pip install -e .
   ```

2. **Get your Gemini API key**:
   - Visit: https://aistudio.google.com/app/apikey
   - Sign in with your Google account
   - Create a new API key
   - Copy the generated key

3. **Configure the API key** (choose one method):
   
   **Option A: Using the setup script (Recommended)**
   ```bash
   python setup_gemini.py
   ```
   
   **Option B: Manual configuration**
   ```bash
   # Create a .env file in the project root
   echo "GOOGLE_API_KEY=your_actual_api_key_here" > .env
   ```
   
   **Option C: Environment variable**
   ```bash
   # Windows PowerShell
   $env:GOOGLE_API_KEY="your_actual_api_key_here"
   
   # Windows CMD
   set GOOGLE_API_KEY=your_actual_api_key_here
   ```

### How It Works

1. **Analysis**: Gemini analyzes your source code against the provided rules
2. **Issue Detection**: Identifies code quality, security, and performance issues
3. **Automated Fixing**: Generates corrected code that addresses all issues
4. **Interactive Review**: Shows you what issues were found and asks for confirmation before applying fixes

### Example Analysis Results

The tool provides detailed analysis including:
- **Issues Found**: Line-by-line breakdown of problems
- **Issue Types**: Code quality, security vulnerabilities, performance issues
- **Rule Violations**: Which specific rules were violated
- **Fixed Code**: Complete corrected version of your code
- **Best Practice Suggestions**: Additional recommendations for improvement
- **Markdown Report**: Comprehensive analysis saved as a formatted markdown file

### Markdown Report Features

Each analysis generates a detailed markdown report with:
- **Structured Summary**: Overview of all changes and improvements
- **Issues Table**: Organized table with line numbers, types, descriptions, and violated rules
- **Complete Fixed Code**: Full corrected source code in syntax-highlighted blocks
- **Additional Suggestions**: Best practice recommendations and improvement tips
- **Timestamped Documentation**: Generated date/time and source file information

Reports are automatically saved with timestamps (e.g., `test_file_analysis_report_20251017_153045.md`) for easy tracking and review.

### Sample Output
```
🤖 Preparing to send data to Gemini Flash 2.5...
🔗 Testing connection to Gemini...
✅ Connected to Gemini successfully!
🎉 Analysis completed successfully!
📊 Issues found: 8
📄 Detailed markdown report saved to: test_file_analysis_report_20251017_153045.md

🐛 Issues identified:
   1. Line 2: Unused import 'sys' - Remove unused imports
   2. Line 15: SQL injection vulnerability - Use parameterized queries
   3. Line 25: Missing type hints - Add type annotations for better code clarity
   4. Line 30: Class name should be capitalized - Follow PEP 8 naming conventions
   5. Line 45: Use list comprehension for better performance

� Preview of fixed code (first 200 characters):
   # Fixed Python file - all static issues resolved
   import os
   import requests
   from typing import List, Optional
   import sqlite3
   
   def calculate_total(items: List[int]) -> int:...

�💡 Would you like to create a fixed version? (y/n): y
✅ Fixed version created: test_file-fixed.py
📁 Original file preserved: test_file.py
📝 Summary: Fixed 8 issues including security vulnerabilities and code quality improvements

💡 Additional suggestions:
   1. Consider adding docstrings to all functions and classes
   2. Use more descriptive variable names where possible
   3. Add error handling for file operations and user inputs
```

## File Structure
```
ejad/
├── __init__.py
├── cli.py           # Main CLI entry point
└── static_issue.py  # Static issue fixing logic
``` 
