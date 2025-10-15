# MSBench Analysis MCP

This tool is designed to analyze MSBench log zip files, automatically extracting error information from nested logs and trajectory. After starting, open Copilot Chat and switch the mode to `agent mode`.
4. Check if the five tools provided by this server are recognized by Copilot:
   - `analyze_cls_errors_and_save_report` - Cls log analysis with Excel output
   - `analyze_cls_errors` - Cls log analysis with markdown output
   - `analyze_trajectory_errors_and_save_report` - Trajectory analysis with Excel output
   - `analyze_trajectory_errors` - Trajectory analysis with markdown output
   - `compare_two_zips_trajectory_analysis` - Compare two trajectory zip files with Excel output
5. You can now use Copilot Chat in conversation mode to analyze MSBench errors interactively. supports both cls log analysis and tool call trajectory analysis. It is intended for use as an MCP (Model Context Protocol) server, supporting integration with MCP clients such as Copilot Chat or mcp-inspector.

## Features
- **Cls Log Analysis:**
  - Recursively extracts and analyzes all inner zip files within a given MSBench log archive.
  - Only processes `cls.log` files located in the `output` directory of each inner zip.
  - Extracts error messages and error types from logs using regular expressions.
  - Aggregates error statistics by type and provides total error counts.
  - Tracks and reports the number of skipped (unreadable or broken) inner zip files and cls.log files.
  - Generates a detailed Excel report with error details and summary statistics.

- **Trajectory Data Analysis:**
  - Analyzes `fetchLog.json` files containing detailed tool call interaction data.
  - Processes step-by-step tool call sequences with assistant-tool message pairs.
  - Identifies failed tool calls with "Tool call failed with error:" patterns.
  - Extracts tool call error details including step number, tool call ID, tool name, and error messages.
  - Uses optimized single-pass analysis to efficiently collect all statistics without duplicate processing.
  - Provides comprehensive statistics including:
    - Total task counts and tool call counts
    - Average steps and tool calls per task
    - Tool usage statistics across all tasks
    - Per-task statistics with detailed tool usage breakdown
    - Error categorization by tool type and message prefix
    - Success rate and performance metrics
  - Automatically categorizes errors using predefined prefix patterns for better analysis.
  - Generates comprehensive Excel reports with 6 sheets:
    - `Summary` sheet (key metrics, success rate, and overview statistics),
    - `Task Statistics` sheet (per-task step counts, tool calls, status, and detailed tool usage),
    - `Tool Usage Stats` sheet (overall tool usage statistics across all tasks),
    - `Task Error Detail` sheet (one row per error; includes final response for non-success),
    - `Tool Error Stats` sheet (errors grouped by tool name),
    - `Error Prefix Stats` sheet (errors grouped by tool name and error message prefix combination).

- **Common Features:**
  - Provides both summary and detailed error information via MCP tools.
  - Supports saving results to Excel files or returning analysis in markdown format.
  - Tracks processing statistics including skipped files and error counts.

## MCP Tools

### Cls Log Analysis Tools

#### 1. `analyze_cls_errors_and_save_report(zipPath: str) -> str`
- **Description:**
  - Analyzes errors in MSBench cls log files and saves a detailed Excel report.
  - Extracts error messages, categorizes them by type, and generates comprehensive statistics.
  - Returns a summary string including the report path, total error count, error type breakdown, and the number of skipped files.
- **Output Example:**
  ```
  Report path: /path/to/msbench_cls_analysis_report.xlsx
  Total errors: 42
  Error type count: {"TypeError": 10, "ValueError": 32}
  Skipped inner zip: 1
  Skipped cls.log: 2
  ```

#### 2. `analyze_cls_errors(zipPath: str) -> str`
- **Description:**
  - Analyzes errors in MSBench cls log files and returns detailed analysis results in markdown format.
  - Extracts error messages, categorizes them by type, and provides comprehensive statistics.
  - Does not save results to file.
- **Output Example:**
  ```
  Total errors: 42
  Error type count: {"TypeA": 10, "TypeB": 32}
  Skipped inner zip: 1
  Skipped cls.log: 2

  | File Name | Error Information | Error Type |
  |-----------|------------------|------------|
  | foo.zip   | ...              | TypeA      |
  | bar.zip   | ...              | TypeB      |
  ```

### Trajectory Data Analysis Tools

#### 3. `analyze_trajectory_errors_and_save_report(zipPath: str) -> str`
- **Description:**
  - Analyzes tool call errors in MSBench trajectory data (fetchLog.json) and saves the report to an Excel file.
  - Processes step-by-step tool call interactions with assistant-tool message pairs.
  - Identifies failed tool calls, extracts error messages, and generates comprehensive statistics.
  - Uses unified single-pass analysis to efficiently process all data and collect statistics simultaneously.
  - Automatically categorizes errors using predefined prefix patterns including "Code mapper might be in a loop", "Error executing command", "Failed to read file", etc.
  - Provides comprehensive tool usage and task execution statistics.
  - Saves results to an Excel file with detailed data and comprehensive tool-prefix combination statistics.
- **Output Example:**
  ```
  Report path: /path/to/msbench_trajectory_analysis_report.xlsx
  Total tasks analyzed: 25
  Total tool calls: 150
  Average steps per task: 12.40
  Average tool calls per task: 6.00
  Tool call error count by type: {"run_in_terminal": 15, "read_file": 8, "write_file": 3}
  Tool call error count by prefix: {"Error executing command": 12, "Failed to read file": 7, "Code mapper might be in a loop": 4}
  Tool usage count: {"run_in_terminal": 45, "read_file": 38, "write_file": 25, "edit_file": 20}
  Skipped inner zip: 0
  Skipped trajectory log: 1
  ```

#### 4. `analyze_trajectory_errors(zipPath: str) -> str`
- **Description:**
  - Analyzes tool call errors in MSBench trajectory data (fetchLog.json) and returns detailed analysis results.
  - Processes step-by-step tool call interactions with assistant-tool message pairs.
  - Identifies failed tool calls, extracts error messages, and provides statistics by tool type.
  - Uses unified single-pass analysis for efficient processing and comprehensive error categorization.
  - Automatically categorizes errors using predefined prefix patterns for consistent analysis.
  - Does not save results to file.
- **Output Example:**
  ```
  Tool call error count by type: {"run_in_terminal": 15, "read_file": 8, "write_file": 3}
  Tool call error count by prefix: {"Error executing command": 12, "Failed to read file": 7, "Code mapper might be in a loop": 4}
  Skipped inner zip: 0
  Skipped trajectory log: 1

  | File Name | Total Steps | Failed Step | Failed Tool Call ID | Failed Tool Name | Error Message | Final Response Type | Final Response |
  |-----------|-------------|-------------|----------------------|------------------|---------------|---------------------|----------------|
  | task1.zip | 12          | 7           | abc123               | run_in_terminal  | Error executing command: Command failed with exit code 1... | success             |                |
  | task2.zip | 8           |             |                      |                  |               | error               | Task failed    |
  ```

#### 5. `compare_two_zips_trajectory_analysis(zipPath1: str, zipPath2: str) -> str`
- **Description:**
  - Compares two MSBench trajectory zip files and analyzes differences in task steps and tool usage.
  - Extracts task statistics including step counts and tool usage from both zip files.
  - Generates comprehensive comparison report with task step differences and tool usage statistics.
  - Calculates average steps per task for both zip files and provides summary statistics.
  - Saves results to an Excel file with two sheets: task step comparison and tool usage comparison.
- **Output Example:**
  ```
  Report path: /path/to/comparison_zip1_vs_zip2.xlsx
  Tasks in Zip1: 25, Average steps: 12.40
  Tasks in Zip2: 28, Average steps: 11.85
  Total unique tools found: 15
  Task comparisons: 30 tasks analyzed
  Tool comparisons: 15 tools compared
  ```

## Requirements 
- Python version **>= 3.10**
- [uv](https://github.com/astral-sh/uv) (Python package manager, recommended)
- Node.js and npx (required for MCP Inspector)

### Install uv (Python package manager)
- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS/Linux:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # If you don't have curl, you can use wget:
  wget -qO- https://astral.sh/uv/install.sh | sh
  ```

## Usage

### 1. VS Code Copilot Chat Configuration
1. Open VS Code, go to `Preferences` → `Settings`, search for `chat.mcp.discovery`, and set it to `enabled`.
2. Configure the MCP Server:
   - This tool is published on PyPI and can be launched directly using `uvx`.
   - In `Preferences` → `Settings`, search for `Mcp`, find the MCP settings, and edit  `settings.json` to add:
     ```json
     "msbench-analysis-mcp": {
         "command": "uvx",
         "args": [
             "msbench-analysis-mcp"
         ],
         "env": {}
     }
     ```
3. Click `Start` above the MCP configuration to launch the server.
4. After starting, open Copilot Chat and switch the mode to `agent mode`.
5. Check if the four tools provided by this server are recognized by Copilot:
   - `analyze_cls_errors_and_save_report` - Cls log analysis with Excel output
   - `analyze_cls_errors` - Cls log analysis with markdown output
   - `analyze_trajectory_errors_and_save_report` - Trajectory analysis with Excel output
   - `analyze_trajectory_errors` - Trajectory analysis with markdown output
6. You can now use Copilot Chat in conversation mode to analyze MSBench errors interactively.

### 2. MCP Inspector Configuration
- For more about MCP inspector. Please check https://modelcontextprotocol.io/docs/tools/inspector.
- The configuration is similar to Copilot Chat: ensure the MCP server is running and this tool is added.
- You can select this tool in MCP Inspector for interactive analysis.

**How to launch MCP Inspector:**
- You can start MCP Inspector directly using npx:
  ```bash
  npx @modelcontextprotocol/inspector
  ```

**Configuration steps:**
1. After launching, open the MCP Inspector UI in your browser.
2. In the UI, set up the MCP server as shown below:
   - **Transport Type:** STDIO
   - **Command:** `uvx`
   - **Arguments:** `msbench-analysis-mcp`
3. copy the token from the terminal output and paste it into the `configuration` section in the frontend.
4. It is highly recommended to increase the request timeout in the configuration, as the tools in this server may take a long time to run and could otherwise result in request timeouts.
5. In the "Tools" tab, click `List Tools` to display all available tools from the server. Click on any tool to invoke it interactively.

---

