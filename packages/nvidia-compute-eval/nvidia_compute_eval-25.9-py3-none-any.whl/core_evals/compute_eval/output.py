import json
import pathlib
import re
import ast

from nemo_evaluator.api.api_dataclasses import EvaluationResult, MetricResult, Score, TaskResult, ScoreStats


# This is the only required function
def parse_output(output_dir: str) -> EvaluationResult:
    # Look for metrics.json file first
    metrics_file = pathlib.Path(output_dir) / "metrics.json"
    
    if not metrics_file.exists():
        # Fallback to looking for any JSON files
        result_files = list(pathlib.Path(output_dir).glob("*.json"))
        if not result_files:
            raise FileNotFoundError(f"Failed to find metrics.json or any JSON files in {output_dir}")
        if len(result_files) > 1:
            raise ValueError(
                f"More than 1 JSON files found and no metrics.json. `output_dir` must contain metrics.json or a single evaluation JSON file."
            )
        metrics_file = result_files[0]
    
    # Read and parse the metrics file
    with open(metrics_file, 'r') as fp:
        content = fp.read().strip()
    
    try:
        # Try to parse as JSON first
        results = json.loads(content)
    except json.JSONDecodeError:
        # If that fails, try to evaluate as Python literal (handles np.float64, etc.)
        try:
            results = ast.literal_eval(content)
        except (ValueError, SyntaxError):
            # If that also fails, try a more complex parsing approach
            # Handle numpy types by replacing them
            content = re.sub(r'np\.float64\((.*?)\)', r'\1', content)
            results = ast.literal_eval(content)
    
    # Convert numpy types to regular Python floats if needed
    def convert_numpy_types(obj):
        if hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(v) for v in obj]
        else:
            return obj
    
    results = convert_numpy_types(results)
    
    task_name = None
    run_config = pathlib.Path(output_dir) / "run_config.yml"
    if run_config.exists():
        with open(run_config, 'r') as fp:
            yaml_content = fp.read()
            # Extract task from config.params.task
            task_match = re.search(r'task:\s*(\w+)', yaml_content)
            if task_match:
                task_name = task_match.group(1)
    
    if not task_name:
        raise ValueError(f"Could not find task in run_config.yml in {output_dir}")
    
    # Create scores for each metric
    scores = {}
    for metric_name, value in results.items():
        scores[metric_name] = Score(
            value=float(value),
            stats=ScoreStats()  # Empty stats for now
        )
    
    # Create metric results
    metric_results = {}
    for metric_name in results.keys():
        metric_results[metric_name] = MetricResult(
            scores={"pass@1": scores[metric_name]}
        )
    
    task_result = TaskResult(metrics=metric_results)
    
    # Return evaluation result
    return EvaluationResult(
        tasks={task_name: task_result},
        groups={}
    )
