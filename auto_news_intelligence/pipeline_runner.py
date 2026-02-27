"""Pipeline runner with live log streaming for Streamlit UI"""
import subprocess
import sys
import json
import re
from pathlib import Path
from typing import Generator


def stream_pipeline() -> Generator[str, None, dict]:
    """
    Run the full pipeline (download + process) and stream logs line by line.
    
    Yields:
        Log lines as strings
    
    Returns:
        Final stats dict: {total_input, total_automobile, unique_stories, categories}
    """
    # Stage 1: Download articles
    yield "[DOWNLOAD] Starting article download...\n"
    
    download_script = Path('download_new_articles.py')
    if not download_script.exists():
        yield f"[ERROR] {download_script} not found\n"
        return {'error': 'Download script not found'}
    
    try:
        proc = subprocess.Popen(
            [sys.executable, str(download_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in proc.stdout:
            yield f"[DOWNLOAD] {line}"
        
        proc.wait()
        if proc.returncode != 0:
            yield f"[DOWNLOAD] ✗ Failed with exit code {proc.returncode}\n"
            return {'error': f'Download failed: exit code {proc.returncode}'}
        
        yield "[DOWNLOAD] ✓ Complete\n\n"
    
    except Exception as e:
        yield f"[DOWNLOAD] ✗ Exception: {e}\n"
        return {'error': str(e)}
    
    # Stage 2: Run main pipeline
    yield "[PIPELINE] Starting main processing pipeline...\n"
    
    runner_script = Path('runner.py')
    if not runner_script.exists():
        yield f"[ERROR] {runner_script} not found\n"
        return {'error': 'Runner script not found'}
    
    try:
        proc = subprocess.Popen(
            [sys.executable, str(runner_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Track stage labels
        stage_map = {
            'html_loader': '[LOAD]',
            'auto_filter': '[FILTER]',
            'embedder': '[EMBED]',
            'classifier': '[CLASSIFY]',
            'deduplicator': '[DEDUP]',
            'summarizer': '[SUMMARIZE]',
        }
        
        log_lines = []
        for line in proc.stdout:
            log_lines.append(line)
            
            # Add stage labels based on module name
            labeled = line
            for module, label in stage_map.items():
                if module in line:
                    labeled = line.replace(module, label)
                    break
            
            yield labeled
        
        proc.wait()
        if proc.returncode != 0:
            yield f"[PIPELINE] ✗ Failed with exit code {proc.returncode}\n"
            return {'error': f'Pipeline failed: exit code {proc.returncode}'}
        
        yield "\n[DONE] ✓ Pipeline complete\n"
    
    except Exception as e:
        yield f"[PIPELINE] ✗ Exception: {e}\n"
        return {'error': str(e)}
    
    # Parse final stats from output
    stats = parse_stats_from_logs(log_lines)
    
    # Also read from results.json if available
    results_file = Path('output/results.json')
    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                stats['total_input'] = data['stats']['total_input']
                stats['total_automobile'] = data['stats']['total_automobile']
                stats['unique_sources'] = data['stats']['unique_sources']
                stats['categories'] = len(data['categories'])
                stats['unique_stories'] = sum(
                    cat_data['unique_stories'] 
                    for cat_data in data['categories'].values()
                )
        except Exception as e:
            yield f"[WARNING] Could not parse results.json: {e}\n"
    
    return stats


def parse_stats_from_logs(log_lines: list[str]) -> dict:
    """Extract summary stats from pipeline logs."""
    stats = {
        'total_input': 0,
        'total_automobile': 0,
        'unique_stories': 0,
        'categories': 8,
        'unique_sources': 0
    }
    
    for line in log_lines:
        # Look for final stats lines
        if 'INPUT:' in line and 'total articles' in line:
            match = re.search(r'(\d+)\s+total articles', line)
            if match:
                stats['total_input'] = int(match.group(1))
        
        if 'AUTO FILTER:' in line and 'automobile articles' in line:
            match = re.search(r'(\d+)\s+automobile articles', line)
            if match:
                stats['total_automobile'] = int(match.group(1))
        
        if 'STORIES:' in line and 'unique stories' in line:
            match = re.search(r'(\d+)\s+unique stories', line)
            if match:
                stats['unique_stories'] = int(match.group(1))
    
    return stats
