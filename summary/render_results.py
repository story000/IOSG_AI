import json
import os
from pathlib import Path
import re
from datetime import datetime

def load_test_result(file_path):
    """Load a single test result JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_file_info(filename):
    """Extract information from filename"""
    # Remove .json extension
    name = filename.replace('.json', '')
    
    # Pattern: scenario_model_temp_topk_topp_timestamp
    parts = name.split('_')
    
    if len(parts) >= 6:
        scenario = parts[0]
        model = '_'.join(parts[1:-4])  # Handle models with underscores
        temp = parts[-4]
        topk = parts[-3] 
        topp = parts[-2]
        timestamp = parts[-1]
        
        return {
            'scenario': scenario,
            'model': model,
            'temperature': temp,
            'top_k': topk,
            'top_p': topp,
            'timestamp': timestamp
        }
    return None

def render_single_result_markdown(result_data, output_file):
    """Render a single test result as markdown"""
    
    md_content = []
    
    # Header
    settings = result_data.get('settings', {})
    scenario = result_data.get('scenario', 'Unknown')
    
    md_content.append(f"# Test Result: {scenario}")
    md_content.append("")
    
    # Test Information
    md_content.append("## Test Information")
    md_content.append("")
    md_content.append(f"- **Scenario**: {scenario}")
    md_content.append(f"- **Model**: {settings.get('model', 'Unknown')}")
    md_content.append(f"- **Temperature**: {settings.get('temperature', 'N/A')}")
    md_content.append(f"- **Top-K**: {settings.get('top_k', 'N/A')}")
    md_content.append(f"- **Top-P**: {settings.get('top_p', 'N/A')}")
    md_content.append(f"- **Max Tokens**: {settings.get('max_tokens', 'N/A')}")
    md_content.append(f"- **Timestamp**: {result_data.get('timestamp', 'N/A')}")
    md_content.append(f"- **Status**: {result_data.get('status', 'Unknown')}")
    md_content.append("")
    
    # API Response Information
    api_response = result_data.get('api_response', {})
    if api_response:
        md_content.append("## API Response Information")
        md_content.append("")
        
        if 'response_time' in api_response:
            md_content.append(f"- **Response Time**: {api_response['response_time']:.2f} seconds")
        
        if 'usage' in api_response:
            usage = api_response['usage']
            md_content.append(f"- **Tokens Used**: {usage}")
            
        if 'actual_settings' in api_response:
            actual = api_response['actual_settings']
            md_content.append(f"- **Actual Settings Used**: {actual}")
            
        md_content.append("")
    
    # Prompt Used
    prompt_data = result_data.get('prompt', {})
    if prompt_data:
        md_content.append("## System Prompt")
        md_content.append("")
        md_content.append("```")
        md_content.append(prompt_data.get('system', 'No system prompt'))
        md_content.append("```")
        md_content.append("")
        
        md_content.append("## User Prompt")
        md_content.append("")
        md_content.append("```")
        md_content.append(prompt_data.get('user', 'No user prompt'))
        md_content.append("```")
        md_content.append("")
    
    # Model Response
    if api_response and 'response' in api_response:
        md_content.append("## Model Response")
        md_content.append("")
        md_content.append(api_response['response'])
        md_content.append("")
    elif api_response and 'error' in api_response:
        md_content.append("## Error")
        md_content.append("")
        md_content.append(f"```")
        md_content.append(f"Error: {api_response['error']}")
        md_content.append(f"```")
        md_content.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))

def render_comparison_markdown(results_dir, output_file):
    """Render a comparison view of all test results"""
    
    results_dir = Path(results_dir)
    # Look for both .json files and files ending with _json
    json_files = list(results_dir.glob('*.json')) + list(results_dir.glob('*_json'))
    
    # Filter out summary files
    test_files = [f for f in json_files if not f.name.startswith('test_summary')]
    
    if not test_files:
        print("No test result files found")
        return
    
    # Load all results
    all_results = []
    for file_path in test_files:
        try:
            result = load_test_result(file_path)
            result['filename'] = file_path.name
            all_results.append(result)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    # Sort by model and settings
    all_results.sort(key=lambda x: (
        x.get('settings', {}).get('model', ''),
        x.get('settings', {}).get('temperature', 0)
    ))
    
    md_content = []
    
    # Header
    md_content.append("# Test Results Comparison")
    md_content.append("")
    md_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append(f"Total tests: {len(all_results)}")
    md_content.append("")
    
    # Summary table
    md_content.append("## Summary Table")
    md_content.append("")
    md_content.append("| Model | Temperature | Top-K | Top-P | Status | Response Time | Tokens |")
    md_content.append("|-------|-------------|-------|-------|---------|---------------|---------|")
    
    for result in all_results:
        settings = result.get('settings', {})
        api_response = result.get('api_response', {})
        
        model = settings.get('model', 'Unknown')
        temp = settings.get('temperature', 'N/A')
        top_k = settings.get('top_k', 'N/A')
        top_p = settings.get('top_p', 'N/A')
        status = "✅" if result.get('status') == 'completed' else "❌"
        
        response_time = api_response.get('response_time', 0)
        time_str = f"{response_time:.1f}s" if response_time else "N/A"
        
        usage = api_response.get('usage', {})
        if isinstance(usage, dict):
            total_tokens = usage.get('total_tokens', usage.get('totalTokens', 'N/A'))
        else:
            total_tokens = 'N/A'
        
        md_content.append(f"| {model} | {temp} | {top_k} | {top_p} | {status} | {time_str} | {total_tokens} |")
    
    md_content.append("")
    
    # Detailed results by model
    md_content.append("## Detailed Results")
    md_content.append("")
    
    current_model = None
    for result in all_results:
        settings = result.get('settings', {})
        model = settings.get('model', 'Unknown')
        
        if model != current_model:
            current_model = model
            md_content.append(f"### {model}")
            md_content.append("")
        
        # Settings info
        temp = settings.get('temperature', 'N/A')
        top_k = settings.get('top_k', 'N/A')
        top_p = settings.get('top_p', 'N/A')
        
        md_content.append(f"#### Settings: T={temp}, K={top_k}, P={top_p}")
        md_content.append("")
        
        api_response = result.get('api_response', {})
        
        if result.get('status') == 'completed':
            # Response time and usage
            if 'response_time' in api_response:
                md_content.append(f"**Response Time**: {api_response['response_time']:.2f}s")
                md_content.append("")
            
            # Model response (full content)
            if 'response' in api_response:
                response_text = api_response['response']
                
                md_content.append("**Response**:")
                md_content.append("")
                md_content.append(response_text)
                md_content.append("")
        else:
            # Error information
            if 'error' in api_response:
                md_content.append(f"**Error**: {api_response['error']}")
                md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))

def render_analysis_markdown(results_dir, output_file):
    """Render analysis and insights from test results"""
    
    results_dir = Path(results_dir)
    # Look for both .json files and files ending with _json
    json_files = list(results_dir.glob('*.json')) + list(results_dir.glob('*_json'))
    test_files = [f for f in json_files if not f.name.startswith('test_summary')]
    
    # Load all results
    all_results = []
    for file_path in test_files:
        try:
            result = load_test_result(file_path)
            all_results.append(result)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    if not all_results:
        return
    
    md_content = []
    
    # Header
    md_content.append("# Test Results Analysis")
    md_content.append("")
    md_content.append(f"Analysis generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append("")
    
    # Success rate analysis
    successful_tests = [r for r in all_results if r.get('status') == 'completed']
    failed_tests = [r for r in all_results if r.get('status') == 'failed']
    
    md_content.append("## Success Rate Analysis")
    md_content.append("")
    md_content.append(f"- **Total Tests**: {len(all_results)}")
    md_content.append(f"- **Successful**: {len(successful_tests)} ({len(successful_tests)/len(all_results)*100:.1f}%)")
    md_content.append(f"- **Failed**: {len(failed_tests)} ({len(failed_tests)/len(all_results)*100:.1f}%)")
    md_content.append("")
    
    # Response time analysis
    if successful_tests:
        response_times = []
        for result in successful_tests:
            rt = result.get('api_response', {}).get('response_time')
            if rt:
                response_times.append(rt)
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            md_content.append("## Response Time Analysis")
            md_content.append("")
            md_content.append(f"- **Average Response Time**: {avg_time:.2f} seconds")
            md_content.append(f"- **Fastest Response**: {min_time:.2f} seconds")
            md_content.append(f"- **Slowest Response**: {max_time:.2f} seconds")
            md_content.append("")
    
    # Model performance comparison
    model_stats = {}
    for result in successful_tests:
        model = result.get('settings', {}).get('model', 'Unknown')
        response_time = result.get('api_response', {}).get('response_time', 0)
        
        if model not in model_stats:
            model_stats[model] = []
        model_stats[model].append(response_time)
    
    if model_stats:
        md_content.append("## Model Performance Comparison")
        md_content.append("")
        md_content.append("| Model | Avg Response Time | Tests Count |")
        md_content.append("|-------|-------------------|-------------|")
        
        for model, times in model_stats.items():
            if times:
                avg_time = sum(times) / len(times)
                md_content.append(f"| {model} | {avg_time:.2f}s | {len(times)} |")
        
        md_content.append("")
    
    # Failed tests analysis
    if failed_tests:
        md_content.append("## Failed Tests Analysis")
        md_content.append("")
        
        error_counts = {}
        for result in failed_tests:
            error = result.get('api_response', {}).get('error', 'Unknown error')
            # Extract main error type
            if 'Unsupported parameter' in error:
                error_type = 'Unsupported parameter'
            elif 'invalid_request_error' in error:
                error_type = 'Invalid request'
            elif 'API key' in error:
                error_type = 'API key error'
            else:
                error_type = 'Other error'
                
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            md_content.append(f"- **{error_type}**: {count} failures")
        
        md_content.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))

def main():
    """Main function to render results"""
    results_dir = "prompt_test_results2"
    
    if not os.path.exists(results_dir):
        print(f"Results directory '{results_dir}' not found")
        return
    
    print("🎨 Rendering test results to markdown...")
    
    # Create markdown output directory
    md_output_dir = "markdown_results2"
    os.makedirs(md_output_dir, exist_ok=True)
    
    # Render comparison view
    comparison_file = os.path.join(md_output_dir, "comparison.md")
    render_comparison_markdown(results_dir, comparison_file)
    print(f"📊 Comparison view: {comparison_file}")
    
    # Render analysis view
    analysis_file = os.path.join(md_output_dir, "analysis.md") 
    render_analysis_markdown(results_dir, analysis_file)
    print(f"📈 Analysis view: {analysis_file}")
    
    # Render individual result files
    results_path = Path(results_dir)
    # Look for both .json files and files ending with _json
    json_files = list(results_path.glob('*.json')) + list(results_path.glob('*_json'))
    test_files = [f for f in json_files if not f.name.startswith('test_summary')]
    
    individual_dir = os.path.join(md_output_dir, "individual")
    os.makedirs(individual_dir, exist_ok=True)
    
    for json_file in test_files:
        try:
            result_data = load_test_result(json_file)
            md_filename = json_file.stem + ".md"
            md_filepath = os.path.join(individual_dir, md_filename)
            render_single_result_markdown(result_data, md_filepath)
        except Exception as e:
            print(f"Error rendering {json_file}: {e}")
    
    print(f"📝 Individual results: {individual_dir}/")
    print("✅ Markdown rendering complete!")

if __name__ == "__main__":
    main()