"""
MSBench Analysis MCP Server

It exposes tools for analyzing errors and generating reports.
"""

import json
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Handle both relative and absolute imports
try:
    from .utils import table_markdown, CLS_COLUMNS, TRAJECTORY_COLUMNS, COMPARISON_TASK_COLUMNS, COMPARISON_TOOL_COLUMNS
    from .cls_log_analysis import generate_cls_error_report
    from .trajectory_log_analysis import generate_trajectory_error_report, compare_two_zips_and_save_report
except ImportError:
    # If relative imports fail, add the parent directory to sys.path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    from utils import table_markdown, CLS_COLUMNS, TRAJECTORY_COLUMNS, COMPARISON_TASK_COLUMNS, COMPARISON_TOOL_COLUMNS
    from cls_log_analysis import generate_cls_error_report
    from trajectory_log_analysis import generate_trajectory_error_report, compare_two_zips_and_save_report


mcp = FastMCP("msbench_analysis_mcp")

@mcp.tool()
def analyze_cls_errors_and_save_report(zipPath: str) -> str:
    """
    Analyze errors in MSBench cls log files and save the report to an Excel file.
    
    The cls log files contain error information from MSBench execution logs.
    This function extracts error messages, categorizes them by type, and generates comprehensive statistics.
    Saves results to an Excel file with detailed error data.
    
    Args:
        zipPath: Path to the zip file containing MSBench cls log files
        
    Returns:
        Summary of analysis results including total errors, error counts by type and report file path
    """
    result = generate_cls_error_report(zipPath, True)
    info = [
        f"Report path: {result['report_path']}",
        f"Total errors: {result['total_errors']}",
        f"Error type count: {json.dumps(result['by_type'], ensure_ascii=False)}",
        f"Skipped inner zip: {result['skipped_inner_zip']}",
        f"Skipped cls.log: {result['skipped_cls_log']}"
    ]
    return "\n".join(info)

@mcp.tool()
def analyze_cls_errors(zipPath: str) -> str:
    """
    Analyze errors in MSBench cls log files and return detailed analysis results.
    
    The cls log files contain error information from MSBench execution logs.
    This function extracts error messages, categorizes them by type, and provides comprehensive statistics.
    Does not save results to file.
    
    Args:
        zipPath: Path to the zip file containing MSBench cls log files
        
    Returns:
        Detailed error analysis in markdown table format with error counts by type
    """
    result = generate_cls_error_report(zipPath, False)
    info = [
        f"Total errors: {result['total_errors']}",
        f"Error type count: {json.dumps(result['by_type'], ensure_ascii=False)}",
        f"Skipped inner zip: {result['skipped_inner_zip']}",
        f"Skipped cls.log: {result['skipped_cls_log']}"
    ]
    if result.get('errors'):
        info.append(table_markdown(result['errors'], CLS_COLUMNS))
    return "\n".join(info)


@mcp.tool()
def analyze_trajectory_errors_and_save_report(zipPath: str) -> str:
    """
    Analyze tool call errors in MSBench trajectory data (fetchLog.json) and save the report to an Excel file.
    
    The trajectory data contains step-by-step tool call interactions with assistant-tool message pairs.
    This function identifies failed tool calls, extracts error messages, and generates comprehensive statistics.
    Saves results to an Excel file with detailed data and tool error statistics.
    
    Args:
        zipPath: Path to the zip file containing MSBench trajectory data
        
    Returns:
        Summary of analysis results including error counts by tool type and report file path
    """
    result = generate_trajectory_error_report(zipPath, True)
    info = [
        f"Report path: {result['report_path']}",
        f"Total tasks analyzed: {result['total_tasks']}",
        f"Total tool calls: {result['total_tool_calls']}",
        f"Average steps per task: {result['avg_steps_per_task']:.2f}",
        f"Average tool calls per task: {result['avg_tool_calls_per_task']:.2f}",
        f"Tool call error count by tool: {json.dumps(result['by_tool'], ensure_ascii=False)}",
        f"Tool call error count by prefix: {json.dumps(result['by_prefix'], ensure_ascii=False)}",
        f"Tool usage count: {json.dumps(result['tool_usage_count'], ensure_ascii=False)}",
        f"Skipped inner zip: {result['skipped_inner_zip']}",
        f"Skipped trajectory log: {result['skipped_trajectory_log']}"
    ]
    return "\n".join(info)

@mcp.tool()
def analyze_trajectory_errors(zipPath: str) -> str:
    """
    Analyze tool call errors in MSBench trajectory data (fetchLog.json) and return a summary of the analysis results.
    
    The trajectory data contains step-by-step tool call interactions with assistant-tool message pairs.
    This function identifies failed tool calls, extracts error messages, and provides statistics by tool type.
    Does not save results to file.
    
    Args:
        zipPath: Path to the zip file containing MSBench trajectory data
        
    Returns:
        Summary of tool call error analysis including error counts by tool type
    """
    result = generate_trajectory_error_report(zipPath, False)
    info = [
        f"Total tasks analyzed: {result['total_tasks']}",
        f"Total tool calls: {result['total_tool_calls']}",
        f"Average steps per task: {result['avg_steps_per_task']:.2f}",
        f"Average tool calls per task: {result['avg_tool_calls_per_task']:.2f}",
        f"Tool call error count by tool: {json.dumps(result['by_tool'], ensure_ascii=False)}",
        f"Tool call error count by prefix: {json.dumps(result['by_prefix'], ensure_ascii=False)}",
        f"Tool usage count: {json.dumps(result['tool_usage_count'], ensure_ascii=False)}",
        f"Skipped inner zip: {result['skipped_inner_zip']}",
        f"Skipped trajectory log: {result['skipped_trajectory_log']}"
    ]
    if result.get('errors'):
        info.append(table_markdown(result['errors'], TRAJECTORY_COLUMNS))
    return "\n".join(info)

@mcp.tool()
def compare_two_zips_trajectory_analysis(zipPath1: str, zipPath2: str) -> str:
    """
    Compare two MSBench trajectory zip files and analyze differences in task steps and tool usage.
    
    This function analyzes two zip files containing MSBench trajectory data and generates a comprehensive
    comparison report including task step counts, tool usage statistics, and average metrics.
    Saves results to an Excel file with detailed comparison data.
    
    Args:
        zipPath1: Path to the first zip file for comparison
        zipPath2: Path to the second zip file for comparison
        
    Returns:
        Summary of comparison results including task counts, average steps, and report file path
    """
    result = compare_two_zips_and_save_report(zipPath1, zipPath2)
    info = [
        f"Report path: {result['report_path']}",
        f"Tasks in Zip1: {result['task_count_zip1']}, Average steps: {result['avg_steps_zip1']:.2f}",
        f"Tasks in Zip2: {result['task_count_zip2']}, Average steps: {result['avg_steps_zip2']:.2f}",
        f"Total unique tools found: {result['total_tools']}",
        f"Task comparisons: {len(result['task_comparison'])} tasks analyzed",
        f"Tool comparisons: {len(result['tool_comparison'])} tools compared"
    ]
    return "\n".join(info)

def runServer() -> None:
    """
    Main function to run the MCP server.
    """
    mcp.run(transport='stdio')

if __name__ == "__main__":
    runServer()
