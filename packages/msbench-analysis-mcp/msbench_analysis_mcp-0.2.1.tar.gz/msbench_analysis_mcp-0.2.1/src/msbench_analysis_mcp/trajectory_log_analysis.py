""" functions for processing fetchLog.json """
import json
import re
import sys
from typing import List, Dict
from datetime import datetime, date
import pandas as pd
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path

# Handle both relative and absolute imports
try:
    from .utils import (TRAJECTORY_COLUMNS, TRAJECTORY_OUTPUT_REPORT, TRAJECTORY_TOOL_CALL_ERROR_PREFIX, 
                       norm_path, safe_extract, ZipNotFoundError, ERROR_PREFIXES, 
                       extract_error_prefix_from_message, COMPARISON_TASK_COLUMNS, COMPARISON_TOOL_COLUMNS)
except ImportError:
    # If relative imports fail, add the parent directory to sys.path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    from utils import (TRAJECTORY_COLUMNS, TRAJECTORY_OUTPUT_REPORT, TRAJECTORY_TOOL_CALL_ERROR_PREFIX, 
                      norm_path, safe_extract, ZipNotFoundError, ERROR_PREFIXES,
                      extract_error_prefix_from_message, COMPARISON_TASK_COLUMNS, COMPARISON_TOOL_COLUMNS)


def clean_error_message(error_message: str) -> str:
    """Clean error message to avoid LaTeX parsing issues and other problematic characters"""
    if not isinstance(error_message, str):
        return str(error_message)
    
    # Replace problematic patterns that can cause Excel issues
    # Replace document/node references that might cause worksheet errors
    error_message = re.sub(r'nodes?\.document\([^)]*\)', '[DOCUMENT_NODE]', error_message)
    error_message = re.sub(r'document\._init[^\s]*', '[DOCUMENT_INIT]', error_message)
    
    # Replace LaTeX-like patterns that might trigger sympy parsing
    # Replace \frac{}{} patterns
    error_message = re.sub(r'\\frac\{[^}]*\}\{[^}]*\}', '[MATH_EXPRESSION]', error_message)
    
    # Replace other LaTeX commands
    error_message = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '[LATEX_COMMAND]', error_message)
    
    # Replace problematic function call patterns
    error_message = re.sub(r'[a-zA-Z_][a-zA-Z0-9_]*\.__init__\([^)]*\)', '[INIT_CALL]', error_message)
    error_message = re.sub(r'TypeError: [^\n]*__init__[^\n]*', 'TypeError: [INIT_ERROR]', error_message)
    
    # Replace backslashes that might be interpreted as escape sequences
    error_message = error_message.replace('\\', '\\\\')
    
    # Remove or replace characters that are problematic in Excel
    # Replace control characters and non-printable characters
    error_message = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', error_message)
    
    # Replace Excel formula indicators to prevent formula injection
    if error_message.startswith(('=', '+', '-', '@')):
        error_message = "'" + error_message
    
    # Limit message length to prevent extremely long error messages
    if len(error_message) > 500:
        error_message = error_message[:500] + "..."
    
    return error_message


def analyze_trajectory_errors_unified(rows: List[list]) -> Dict[str, any]:
    """
    analyze trajectory error data in a unified way, performing all statistics in one pass.
    
    Args:
        rows: Error data row list, formatted as [File Name, Total Steps, Failed Step, Failed Tool Call ID, Failed Tool Name, Error Message, Final Response Type, Final Response]

    Returns:
        A dictionary containing all statistics
    """
    # Initialize statistics dictionary
    tool_error_count = {}
    prefix_error_count = {}
    
    for row in rows:
        if len(row) >= 6: 
            tool_name = clean_error_message(str(row[4])) if row[4] else "UNKNOWN"  # Failed Tool Name
            error_message = clean_error_message(str(row[5])) if row[5] else ""     # Error Message
            if error_message == "":
                continue

            # Extract error prefix
            error_prefix = extract_error_prefix_from_message(error_message)

            # Count tool errors
            tool_error_count[tool_name] = tool_error_count.get(tool_name, 0) + 1
            
            # Count prefix errors
            prefix_key = tool_name + "-" + error_prefix
            prefix_error_count[prefix_key] = prefix_error_count.get(prefix_key, 0) + 1

    tool_stats = [
        {'Tool Name': tool_name, 'Error Count': count}
        for tool_name, count in sorted(tool_error_count.items(), key=lambda x: (-x[1], x[0]))
    ]

    prefix_stats = []
    for prefix_key, count in sorted(prefix_error_count.items(), key=lambda x: (-x[1], x[0])):
        tool_name, error_prefix = prefix_key.split("-", 1)
        prefix_stats.append({
            'Error Prefix': error_prefix,
            'Tool Name': tool_name,
            'Error Count': count
        })
    
    return {
        'tool_stats': tool_stats,
        'prefix_stats': prefix_stats,
        'tool_error_count': tool_error_count,
        'prefix_error_count': prefix_error_count
    }


def process_trajectory_file(trajectory_file: Path) -> Dict[str, any]:
        """Process a fetchLog.json file and extract detailed trajectory data.

        Previous implementation only inspected the *last* tool message per snapshot
        and then blindly associated it with the *first* tool call of the nearest
        preceding assistant message. That logic breaks when:
            1. An assistant message contains multiple ``tool_calls`` (normal in the
                 OpenAI-style schema) – only the first tool call was ever attributed.
            2. Multiple tool messages appear in a single snapshot (we skipped all but
                 the last one) – intermediate tool calls were never counted.
            3. A tool message needed to be mapped to its specific tool call by
                 ``tool_call_id`` – we ignored the id and always chose index 0.

        Updated logic:
            * Walk every message in every snapshot.
            * For each ``role == 'tool'`` message, if its ``tool_call_id`` has not
                been seen, attempt a backwards search to find the closest preceding
                assistant message whose ``tool_calls`` array contains a matching id.
            * Extract the exact function name from that tool call entry. Fallbacks:
                    - If no matching id is found but the assistant has a single
                        tool_call, use that one.
                    - Else label tool as ``unknown``.
            * Deduplicate globally on ``tool_call_id`` so that later snapshots that
                include the same historical messages do not inflate counts.
        """
        try:
            with open(trajectory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return {
                "total_steps": 0,
                "tool_call_errors": [],
                "final_response_type": "ERROR",
                "final_response": f"Failed to parse JSON: {str(e)}",
                "total_tool_calls": 0,
                "tool_usage": {}
            }

        if not isinstance(data, list) or len(data) == 0:
            return {
                "total_steps": 0,
                "tool_call_errors": [],
                "final_response_type": "EMPTY",
                "final_response": "Empty or invalid trajectory data",
                "total_tool_calls": 0,
                "tool_usage": {}
            }

        # Aggregates
        step_counter = 0  # counts unique assistant+tool pairs
        total_tool_calls = 0
        tool_usage: Dict[str, int] = {}
        tool_call_errors: List[Dict[str, str]] = []
        seen_tool_call_ids: set[str] = set()

        # Determine final response from the last snapshot when possible
        final_response_type = "UNKNOWN"
        final_response_content = ""
        last_snapshot = data[-1]
        if isinstance(last_snapshot, dict) and 'response' in last_snapshot:
            final_response = last_snapshot['response']
            if isinstance(final_response, dict):
                final_response_type = final_response.get('type', 'UNKNOWN')
                if final_response_type.lower() != 'success':
                    for field in ['value', 'reason', 'error']:
                        if field in final_response:
                            final_response_content = final_response[field]
                            break
                    else:
                        final_response_content = str(final_response)

        # Walk all snapshots; inspect every new tool message and map it precisely
        for snap_index, snapshot in enumerate(data):
            if not isinstance(snapshot, dict):
                continue
            messages = snapshot.get('messages')
            if not isinstance(messages, list):
                continue

            for msg_index, msg in enumerate(messages):
                if not (isinstance(msg, dict) and msg.get('role') == 'tool' and 'content' in msg):
                    continue

                # Derive a stable id
                fallback_id = f"{snap_index}:{msg_index}:{hash(str(msg.get('content')))}"
                tool_call_id = msg.get('tool_call_id') or fallback_id
                if tool_call_id in seen_tool_call_ids:
                    continue  # Already processed in an earlier snapshot

                # Attempt to find the matching assistant/tool_call entry
                matched_tool_name = 'unknown'
                # Search backwards for nearest assistant
                for back_idx in range(msg_index - 1, -1, -1):
                    am = messages[back_idx]
                    if not (isinstance(am, dict) and am.get('role') == 'assistant'):
                        continue
                    tool_calls = am.get('tool_calls', [])
                    if not isinstance(tool_calls, list) or not tool_calls:
                        continue
                    # Try exact id match first
                    chosen = None
                    for tc in tool_calls:
                        if isinstance(tc, dict) and tc.get('id') == tool_call_id:
                            chosen = tc
                            break
                    # Fallback: if only one tool call, assume it's the one
                    if chosen is None and len(tool_calls) == 1:
                        chosen = tool_calls[0]
                    if chosen is not None:
                        fn = chosen.get('function', {}) if isinstance(chosen, dict) else {}
                        matched_tool_name = fn.get('name', 'unknown')
                        break
                    # If not matched, continue searching previous assistant messages

                # Register this tool call
                seen_tool_call_ids.add(tool_call_id)
                step_counter += 1
                total_tool_calls += 1
                tool_usage[matched_tool_name] = tool_usage.get(matched_tool_name, 0) + 1

                # Error extraction
                tool_content = msg.get('content')
                if isinstance(tool_content, str) and TRAJECTORY_TOOL_CALL_ERROR_PREFIX in tool_content:
                    start = tool_content.find(TRAJECTORY_TOOL_CALL_ERROR_PREFIX)
                    err_segment = tool_content[start + len(TRAJECTORY_TOOL_CALL_ERROR_PREFIX):].strip()
                    err = clean_error_message(err_segment)
                    tool_call_errors.append({
                        "failed_step": step_counter,
                        "failed_tool_call_id": clean_error_message(str(tool_call_id)),
                        "failed_tool_name": clean_error_message(str(matched_tool_name)),
                        "error_message": err
                    })

        # Always stringify and truncate final response to ensure Excel-safe values
        resp_str = str(final_response_content) if final_response_content is not None else ""
        if len(resp_str) > 500:
            resp_str = resp_str[:500] + "..."

        # Clean final response using the same cleaning function
        resp_str = clean_error_message(resp_str)

        return {
            # Keep +1 to align with prior semantics (assistant wrap-up)
            "total_steps": step_counter + 1,
            "tool_call_errors": tool_call_errors,
            "final_response_type": final_response_type,
            "final_response": resp_str,
            "total_tool_calls": total_tool_calls,
            "tool_usage": tool_usage
        }


def write_trajectory_error_report(rows: list, out_xlsx: Path, extra_stats: dict = None) -> None:
    """Write fetchLog.json errors to an excel file with detailed data and comprehensive statistics."""

    analysis_result = analyze_trajectory_errors_unified(rows)
    
    # Clean all string data in rows to prevent Excel issues
    cleaned_rows = []
    for row in rows:
        cleaned_row = []
        for item in row:
            if isinstance(item, str):
                cleaned_row.append(clean_error_message(item))
            else:
                cleaned_row.append(item)
        cleaned_rows.append(cleaned_row)

    df_detail = pd.DataFrame(cleaned_rows, columns=TRAJECTORY_COLUMNS)
    df_tool_stats = pd.DataFrame(analysis_result['tool_stats'])
    df_prefix_stats = pd.DataFrame(analysis_result['prefix_stats'])
    
    # Prepare additional statistics if provided
    df_task_stats = pd.DataFrame()
    df_tool_usage = pd.DataFrame()
    df_summary = pd.DataFrame()
    
    if extra_stats:
        # Task statistics with detailed tool usage
        if 'task_statistics' in extra_stats:
            task_stats_data = []
            for task in extra_stats['task_statistics']:
                # Convert tool usage dict to string for Excel
                tools_str = ", ".join([f"{tool}:{count}" for tool, count in task['tool_usage'].items()]) if task['tool_usage'] else "None"
                task_stats_data.append([
                    clean_error_message(str(task['task_name'])),
                    task['total_steps'], 
                    task['total_tool_calls'],
                    'Yes' if task['has_errors'] else 'No',
                    clean_error_message(str(task['final_response_type'])),
                    clean_error_message(tools_str)
                ])
            df_task_stats = pd.DataFrame(task_stats_data, columns=[
                'Task Name', 'Total Steps', 'Total Tool Calls', 'Has Errors', 'Final Response Type', 'Tool Usage Details'
            ])
        
        # Tool usage statistics
        if 'tool_usage_stats' in extra_stats:
            df_tool_usage = pd.DataFrame(extra_stats['tool_usage_stats'])
        
        # Summary statistics
        if all(key in extra_stats for key in ['total_tasks', 'total_tool_calls', 'avg_steps_per_task', 'avg_tool_calls_per_task']):
            summary_data = [
                ['Total Tasks', extra_stats['total_tasks']],
                ['Total Tool Calls', extra_stats['total_tool_calls']],
                ['Average Steps per Task', f"{extra_stats['avg_steps_per_task']:.2f}"],
                ['Average Tool Calls per Task', f"{extra_stats['avg_tool_calls_per_task']:.2f}"],
                ['Total Unique Tools', len(extra_stats.get('tool_usage_count', {}))],
                ['Tasks with Errors', sum(1 for task in extra_stats.get('task_statistics', []) if task['has_errors'])],
                ['Success Rate (%)', f"{(1 - sum(1 for task in extra_stats.get('task_statistics', []) if task['has_errors']) / max(extra_stats['total_tasks'], 1)) * 100:.1f}%"]
            ]
            df_summary = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
    
    with pd.ExcelWriter(out_xlsx, engine='openpyxl') as writer:
        # Write summary first (most important sheet)
        if not df_summary.empty:
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Write task statistics
        if not df_task_stats.empty:
            df_task_stats.to_excel(writer, sheet_name='Task Statistics', index=False)
        
        # Write tool usage statistics
        if not df_tool_usage.empty:
            df_tool_usage.to_excel(writer, sheet_name='Tool Usage Stats', index=False)
        
        # Write detailed error data
        if not df_detail.empty:
            df_detail.to_excel(writer, sheet_name='Task Error Detail', index=False)

        # Write tool error statistics
        if not df_tool_stats.empty:
            df_tool_stats.to_excel(writer, sheet_name='Tool Error Stats', index=False)

        # Write combined tool-prefix statistics
        if not df_prefix_stats.empty:
            df_prefix_stats.to_excel(writer, sheet_name='Error Prefix Stats', index=False)



def generate_trajectory_error_report(zip_path: Path, need_write: bool = False) -> dict:
    """unzip outer zip, recursively process all inner zips, output fetchLog.json error result"""
    zip_path = norm_path(zip_path)
    if not zip_path.exists():
        raise ZipNotFoundError(f"Zip file not found: {zip_path}")
    
    rows = []
    skipped_inner_zip = 0
    skipped_trajectory_log = 0
    
    # Statistics for tool usage
    total_tool_calls = 0
    tool_usage_count = {}  # tool_name -> count
    task_statistics = []   # List of task stats
    all_steps = []        # List of all step counts for average calculation
    
    with TemporaryDirectory(prefix="msbench_") as tmp:
        tmp_dir = Path(tmp)
        with zipfile.ZipFile(zip_path) as z:
            safe_extract(z, tmp_dir)

        for inner in tmp_dir.rglob("*.zip"):
            try:
                with zipfile.ZipFile(inner) as z:
                    safe_extract(z, tmp_dir/inner.stem, ignore_error=False)
            except Exception as e:
                skipped_inner_zip += 1
                continue

            # only process fetchLog.json files in the output directory
            output_dir = tmp_dir/inner.stem/"output"
            if output_dir.exists() and output_dir.is_dir():
                for traj in output_dir.rglob("fetchLog.json"):
                    try:
                        result = process_trajectory_file(traj)
                        tool_call_errors = result["tool_call_errors"]
                        final_response_type = result["final_response_type"]
                        final_response = result["final_response"]
                        
                        # Update global statistics
                        task_tool_calls = result["total_tool_calls"]
                        task_tool_usage = result["tool_usage"]
                        
                        total_tool_calls += task_tool_calls
                        for tool_name, count in task_tool_usage.items():
                            tool_usage_count[tool_name] = tool_usage_count.get(tool_name, 0) + count
                        
                        # Record task statistics
                        task_stats = {
                            "task_name": inner.name,
                            "total_steps": result["total_steps"],
                            "total_tool_calls": task_tool_calls,
                            "tool_usage": task_tool_usage,
                            "has_errors": len(tool_call_errors) > 0,
                            "final_response_type": final_response_type
                        }
                        task_statistics.append(task_stats)
                        all_steps.append(result["total_steps"])
                        
                        # Skip if no errors and final response is success
                        if (not tool_call_errors and 
                            final_response_type.lower() == 'success'):
                            continue
                        
                        # If there are tool call errors, create one row per error
                        if tool_call_errors:
                            for error in tool_call_errors:
                                rows.append([
                                    clean_error_message(str(inner.name)), 
                                    result["total_steps"],                    # Total Steps
                                    error["failed_step"],                     # Step
                                    clean_error_message(str(error["failed_tool_call_id"])), # Tool Call ID
                                    clean_error_message(str(error["failed_tool_name"])),    # Tool Name
                                    clean_error_message(str(error["error_message"])),       # Error Message
                                    clean_error_message(str(final_response_type)),          # Final Response Type
                                    clean_error_message(str(final_response))                # Final Response (only for non-success)
                                ])
                        else:
                            # If no errors but response is not success, create one row for the task
                            rows.append([
                                clean_error_message(str(inner.name)),         # File Name
                                result["total_steps"],                         # Total Steps
                                "",                                            # Step (empty for non-error cases)
                                "",                                            # Tool Call ID (empty)
                                "",                                            # Tool Name (empty)
                                "",                                            # Error Message (empty)
                                clean_error_message(str(final_response_type)), # Final Response Type
                                clean_error_message(str(final_response))       # Final Response
                            ])
                        
                    except Exception as e:
                        skipped_trajectory_log += 1
                        continue

    # Calculate averages and statistics
    total_tasks = len(task_statistics)
    avg_steps_per_task = sum(all_steps) / total_tasks if total_tasks > 0 else 0
    avg_tool_calls_per_task = total_tool_calls / total_tasks if total_tasks > 0 else 0
    
    # Create tool usage statistics
    tool_usage_stats = [
        {'Tool Name': tool_name, 'Usage Count': count}
        for tool_name, count in sorted(tool_usage_count.items(), key=lambda x: (-x[1], x[0]))
    ]

    out_xlsx = zip_path.with_name(TRAJECTORY_OUTPUT_REPORT) if need_write else None
    if need_write and rows:  # Only write if there are rows to write
        # Prepare extra statistics for Excel report
        extra_stats = {
            "task_statistics": task_statistics,
            "tool_usage_stats": tool_usage_stats,
            "total_tasks": total_tasks,
            "total_tool_calls": total_tool_calls,
            "avg_steps_per_task": avg_steps_per_task,
            "avg_tool_calls_per_task": avg_tool_calls_per_task,
            "tool_usage_count": tool_usage_count
        }
        write_trajectory_error_report(rows, out_xlsx, extra_stats)

    analysis_result = analyze_trajectory_errors_unified(rows)

    return {
        "report_path": str(out_xlsx) if (need_write and rows) else "",
        "skipped_inner_zip": skipped_inner_zip,
        "skipped_trajectory_log": skipped_trajectory_log,
        "by_tool": analysis_result['tool_error_count'],
        "by_prefix": analysis_result['prefix_error_count'],
        "errors": rows,
        # New statistics
        "total_tasks": total_tasks,
        "total_tool_calls": total_tool_calls,
        "avg_steps_per_task": avg_steps_per_task,
        "avg_tool_calls_per_task": avg_tool_calls_per_task,
        "tool_usage_stats": tool_usage_stats,
        "tool_usage_count": tool_usage_count,
        "task_statistics": task_statistics
    }


def extract_task_statistics(zip_path: Path) -> Dict[str, Dict]:
    """
    Extract task statistics from zip file including step counts and tool usage.
    
    Args:
        zip_path: Path to the zip file
        
    Returns:
        Dictionary containing task statistics and tool usage counts
    """
    zip_path = norm_path(zip_path)
    if not zip_path.exists():
        raise ZipNotFoundError(f"Zip file not found: {zip_path}")
    
    task_stats = {}  # task_name -> {"steps": int, "tools": {tool_name: count}}
    total_tool_usage = {}  # tool_name -> total_count
    
    with TemporaryDirectory(prefix="msbench_compare_") as tmp:
        tmp_dir = Path(tmp)
        with zipfile.ZipFile(zip_path) as z:
            safe_extract(z, tmp_dir)

        for inner in tmp_dir.rglob("*.zip"):
            try:
                with zipfile.ZipFile(inner) as z:
                    safe_extract(z, tmp_dir/inner.stem, ignore_error=False)
            except Exception:
                continue

            # Process fetchLog.json files in the output directory
            output_dir = tmp_dir/inner.stem/"output"
            if output_dir.exists() and output_dir.is_dir():
                for traj in output_dir.rglob("fetchLog.json"):
                    try:
                        result = process_trajectory_file(traj)
                        task_name = inner.stem
                        
                        # Use the data from process_trajectory_file directly
                        task_stats[task_name] = {
                            "steps": result["total_steps"],
                            "tools": result["tool_usage"]
                        }
                        
                        # Update total tool usage
                        for tool_name, count in result["tool_usage"].items():
                            total_tool_usage[tool_name] = total_tool_usage.get(tool_name, 0) + count
                        
                    except Exception:
                        continue
    
    return {
        "task_stats": task_stats,
        "total_tool_usage": total_tool_usage
    }


def compare_two_zips_and_save_report(zip_path1: str, zip_path2: str) -> dict:
    """
    Compare two zip files and generate a comparison report with step counts and tool usage.
    
    Args:
        zip_path1: Path to the first zip file
        zip_path2: Path to the second zip file
        
    Returns:
        Dictionary containing comparison results and report path
    """
    zip1 = Path(zip_path1)
    zip2 = Path(zip_path2)
    
    # Extract statistics from both zip files
    stats1 = extract_task_statistics(zip1)
    stats2 = extract_task_statistics(zip2)
    
    # Prepare comparison data
    task_comparison_rows = []
    tool_usage_rows = []
    
    # Get all unique task names
    all_tasks = set(stats1["task_stats"].keys()) | set(stats2["task_stats"].keys())
    
    # Compare task steps
    total_steps1 = 0
    total_steps2 = 0
    task_count1 = 0
    task_count2 = 0
    
    for task_name in sorted(all_tasks):
        task1 = stats1["task_stats"].get(task_name, {"steps": 0, "tools": {}})
        task2 = stats2["task_stats"].get(task_name, {"steps": 0, "tools": {}})
        
        steps1 = task1["steps"]
        steps2 = task2["steps"]
        step_diff = steps2 - steps1
        
        status1 = "Present" if task_name in stats1["task_stats"] else "Missing"
        status2 = "Present" if task_name in stats2["task_stats"] else "Missing"
        
        task_comparison_rows.append([
            task_name,
            steps1,
            steps2,
            step_diff,
            status1,
            status2
        ])
        
        if status1 == "Present":
            total_steps1 += steps1
            task_count1 += 1
        if status2 == "Present":
            total_steps2 += steps2
            task_count2 += 1
    
    # Calculate averages
    avg_steps1 = total_steps1 / task_count1 if task_count1 > 0 else 0
    avg_steps2 = total_steps2 / task_count2 if task_count2 > 0 else 0
    
    # Compare tool usage
    all_tools = set(stats1["total_tool_usage"].keys()) | set(stats2["total_tool_usage"].keys())
    
    for tool_name in sorted(all_tools):
        usage1 = stats1["total_tool_usage"].get(tool_name, 0)
        usage2 = stats2["total_tool_usage"].get(tool_name, 0)
        usage_diff = usage2 - usage1
        
        tool_usage_rows.append([
            tool_name,
            usage1,
            usage2,
            usage_diff
        ])
    
    # Create DataFrames
    task_df = pd.DataFrame(task_comparison_rows, columns=COMPARISON_TASK_COLUMNS)
    
    tool_df = pd.DataFrame(tool_usage_rows, columns=COMPARISON_TOOL_COLUMNS)
    
    # Add summary row to task comparison
    summary_row = pd.DataFrame([[
        "SUMMARY",
        total_steps1,
        total_steps2,
        total_steps2 - total_steps1,
        f"Avg: {avg_steps1:.2f}",
        f"Avg: {avg_steps2:.2f}"
    ]], columns=task_df.columns)
    
    task_df = pd.concat([task_df, summary_row], ignore_index=True)
    
    # Generate output file name
    output_name = f"comparison_{zip1.stem}_vs_{zip2.stem}.xlsx"
    out_xlsx = zip1.parent / output_name
    
    # Write to Excel
    with pd.ExcelWriter(out_xlsx, engine='openpyxl') as writer:
        task_df.to_excel(writer, sheet_name='Task Step Comparison', index=False)
        tool_df.to_excel(writer, sheet_name='Tool Usage Comparison', index=False)
    
    return {
        "report_path": str(out_xlsx),
        "task_count_zip1": task_count1,
        "task_count_zip2": task_count2,
        "avg_steps_zip1": avg_steps1,
        "avg_steps_zip2": avg_steps2,
        "total_tools": len(all_tools),
        "task_comparison": task_comparison_rows,
        "tool_comparison": tool_usage_rows
    }