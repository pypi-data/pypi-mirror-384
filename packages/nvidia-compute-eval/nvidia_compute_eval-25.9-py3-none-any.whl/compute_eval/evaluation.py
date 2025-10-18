# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Portions of this file from human-eval (https://github.com/openai/human-eval/).
#
# The MIT License
#
# Copyright (c) OpenAI (https://openai.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import itertools
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import tqdm
from tabulate import tabulate

from compute_eval.data import (
    read_problems,
    stream_jsonl,
    write_completions_to_dir,
    write_jsonl,
)
from compute_eval.execution import check_correctness

WARNING_MSG = """===================
     WARNING
===================

Evaluation of correctness or performance will execute untrusted model-generated
code.

Although it is highly unlikely that model-generated code will do something
overtly malicious in response to this test suite, model-generated code may act
destructively due to a lack of model capability or alignment.

Users are strongly encouraged to sandbox this evaluation suite so that it does
not perform destructive actions on their host or network.

In order to execute this code you must explicitly pass the --allow-execution flag.
"""


def estimate_pass_at_k(
    num_samples: Union[int, List[int], np.ndarray],
    num_correct: Union[List[int], np.ndarray],
    k: int,
) -> np.ndarray:
    """
    Estimates pass@k of each problem and returns them in an array.
    """

    def estimator(n: int, c: int, k: int) -> float:
        """
        Calculates 1 - comb(n - c, k) / comb(n, k).
        """
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    return np.array(
        [estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)]
    )


def get_cli_args(problem: Dict[str, Dict]):
    cc_flags = problem.get("cc_flags")
    ld_flags = problem.get("ld_flags")

    cli_args = ""
    if cc_flags is not None:
        cli_args += " " + cc_flags
    if ld_flags is not None:
        cli_args += " " + ld_flags

    return cli_args


def evaluate_functional_correctness(
    sample_file: str,
    problem_file: str,
    allow_execution: bool = False,
    k: Tuple[int] = (1, 10, 100),
    n_workers: int = 4,
    timeout: float = 60.0,
    save_completions_dir: str = "",
    metrics_output_file: str = "",
    limit_samples: Optional[int] = None,
):
    """
    Evaluates the functional correctness of generated samples, and writes
    results to f"{sample_file}_correctness_results.jsonl".
    """
    
    print(f"=== Starting Evaluation ===")
    print(f"Sample file: {sample_file}")
    print(f"Problem file: {problem_file}")
    print(f"Timeout: {timeout} seconds")
    print(f"Number of workers: {n_workers}")
    print(f"K values: {k}")
    print(f"Limit samples: {limit_samples}")
    print(f"Save completions dir: {save_completions_dir}")
    print(f"Metrics output file: {metrics_output_file}")
    print(f"Allow execution: {allow_execution}")
    print(f"=========================")

    if not allow_execution:
        print(WARNING_MSG)
        sys.exit(1)

    # Check if only one k value was passed in (as an integer)
    if isinstance(k, int):
        k_vals = [k]
    else:
        # Multiple k values (tuple) is converted to a list of int
        k_vals = list(k)

    # If the user wants to save completions, check that the directory exists
    if save_completions_dir != "":
        assert os.path.exists(
            os.path.abspath(save_completions_dir)
        ), "You must have created the directory where the temporary completions will go"

    problems = read_problems(problem_file)
    num_problems = len(problems)
    print(f"Loaded {num_problems} problems from {problem_file}")

    # Handle limiting samples per problem
    sample_limit_per_problem = None
    if limit_samples is not None:
        sample_limit_per_problem = max(1, limit_samples // num_problems)
        print(f"Using limit_samples={limit_samples} with {num_problems} problems = {sample_limit_per_problem} samples per problem")
    else:
        print(f"No sample limit specified - will process all samples")

    # Check the generated samples against test suites.
    print(f"Starting evaluation with {n_workers} workers...")
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        completion_id = Counter()
        n_samples = 0
        results = defaultdict(list)
        skipped_samples = 0

        print("Reading and submitting samples for evaluation...")
        for sample in tqdm.tqdm(stream_jsonl(sample_file)):
            task_id = sample["task_id"]
            
            # Apply sample limiting per problem if specified
            if sample_limit_per_problem is not None and completion_id[task_id] >= sample_limit_per_problem:
                skipped_samples += 1
                continue
                
            compilable_code = sample["compilable_code"]

            problem = problems[task_id]

            cli_args = get_cli_args(problem)

            cuda_version = problem.get("cuda_version")

            args = (
                problem,
                compilable_code,
                timeout,
                completion_id[task_id],
                cli_args,
                cuda_version,
            )
            future = executor.submit(check_correctness, *args)
            futures.append(future)
            completion_id[task_id] += 1
            n_samples += 1

        print(f"Submitted {n_samples} samples for evaluation")
        if skipped_samples > 0:
            print(f"Skipped {skipped_samples} samples due to limit_samples constraint")

        # make sure that solved all the problems (at least once)
        assert len(completion_id) == len(problems), "Some problems are not attempted."

        print("Processing evaluation results...")
        completed_results = 0
        passed_results = 0
        failed_results = 0
        skipped_results = 0
        error_summary: Dict[str, int] = {}
        
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            results[result["task_id"]].append((result["completion_id"], result))
            
            completed_results += 1
            if result["skipped"]:
                skipped_results += 1
            elif result["passed"]:
                passed_results += 1
            else:
                failed_results += 1
                # Track error types for debugging
                error_msg = result["result"]
                if error_msg.startswith("Failed to compile"):
                    error_type = "compilation_error"
                elif error_msg.startswith("Failed to run"):
                    error_type = "runtime_error"
                elif error_msg.startswith("Timed out"):
                    error_type = "timeout"
                else:
                    error_type = "other_error"
                
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
                
            # Log progress every 20 completed results to reduce spam
            if completed_results % 20 == 0:
                print(f"Progress: {completed_results}/{len(futures)} completed (Passed: {passed_results}, Failed: {failed_results}, Skipped: {skipped_results})")
        
        print(f"Evaluation completed: {completed_results} total, {passed_results} passed, {failed_results} failed, {skipped_results} skipped")
        if failed_results > 0:
            print("Error breakdown:")
            for error_type, count in error_summary.items():
                print(f"  {error_type}: {count}")
            
            # Show a few sample error messages for debugging
            print("\nSample error messages:")
            sample_errors_shown = 0
            for task_id, result_list in results.items():
                for completion_id, result in result_list:
                    if not result["passed"] and not result["skipped"] and sample_errors_shown < 3:
                        error_msg = result['result']
                        # Truncate long error messages
                        if len(error_msg) > 200:
                            error_msg = error_msg[:200] + "..."
                        print(f"  Task {task_id}, Completion {completion_id}: {error_msg}")
                        sample_errors_shown += 1
                        if sample_errors_shown >= 3:
                            break
                if sample_errors_shown >= 3:
                    break

    # Calculate pass@k.
    print("Calculating pass@k metrics...")
    total, correct = [], []
    problems_processed = 0
    problems_skipped = 0
    
    for task_id, result in results.items():
        result.sort()
        passed = [r[1]["passed"] for r in result if not r[1]["skipped"]]

        # If all test cases are skipped, we skip the problem.
        if len(passed) == 0:
            print(
                f"Skipping problem {task_id}, it would be ignored while calculating pass@k. Possible reasons maybe incompatible GPU architecture."
            )
            problems_skipped += 1
            continue
        total.append(len(passed))
        correct.append(sum(passed))
        problems_processed += 1
        
    print(f"Processed {problems_processed} problems for pass@k calculation")
    if problems_skipped > 0:
        print(f"Skipped {problems_skipped} problems due to all samples being skipped")
        
    total = np.array(total)
    correct = np.array(correct)

    pass_at_k = {}
    for k in k_vals:
        if (total >= k).all():
            pass_at_k[f"pass@{k}"] = estimate_pass_at_k(total, correct, k).mean()
            print(f"pass@{k}: {pass_at_k[f'pass@{k}']:.4f}")
        else:
            print(f"pass@{k}: Not calculated (insufficient samples)")

    # Finally, save the results in one file:
    print("Preparing final results for output...")
    sample_results = []
    samples_processed = 0
    samples_with_errors = 0
    
    for sample in stream_jsonl(sample_file):
        task_id = sample["task_id"]
        
        # Check if we have results for this sample (due to limit_samples, some may not have been processed)
        if task_id in results and len(results[task_id]) > 0:
            result = results[task_id].pop(0)
            sample["result"] = result[1]["result"]
            sample["skipped"] = result[1]["skipped"]
            sample["passed"] = result[1]["passed"]
            sample["completion_id"] = result[1]["completion_id"]
            
            # Add error message if the execution didn't pass
            if not result[1]["passed"] and not result[1]["skipped"]:
                sample["error_message"] = result[1]["result"]
                samples_with_errors += 1
            else:
                sample["error_message"] = None
                
            sample_results.append(sample)
            samples_processed += 1
        else:
            # Sample was not processed due to limit_samples, skip it
            continue
            
        # Stop if we've processed all the limited samples  
        if sample_limit_per_problem is not None and samples_processed >= n_samples:
            break
    
    print(f"Prepared {samples_processed} samples for output")
    if samples_with_errors > 0:
        print(f"Found {samples_with_errors} samples with error messages")

    out_file = (
        os.path.splitext(os.path.basename(sample_file))[0]
        + "_correctness_results.jsonl"
    )
    print(f"Writing {len(sample_results)} results to {out_file}...")
    write_jsonl(out_file, sample_results)
    print(f"Results successfully written to {out_file}")

    if save_completions_dir != "":
        print(f"Saving the completions to {os.path.abspath(save_completions_dir)}...")
        write_completions_to_dir(save_completions_dir, sample_results)
        print(f"Completions successfully saved to {save_completions_dir}")
    
    print("=== Final Results ===")
    print(pass_at_k)
    print("===================")
    
    if metrics_output_file:
        import json
        print(f"Saving metrics to {metrics_output_file}...")
        # Convert numpy types to regular Python types for JSON serialization
        metrics_for_json = {}
        for key, value in pass_at_k.items():
            if hasattr(value, 'item'):  # numpy scalar
                metrics_for_json[key] = value.item()
            else:
                metrics_for_json[key] = float(value)
        
        os.makedirs(os.path.dirname(metrics_output_file), exist_ok=True)
        with open(metrics_output_file, 'w') as f:
            json.dump(metrics_for_json, f, indent=2)
        print(f"Metrics successfully saved to {metrics_output_file}")
    
    print("=== Evaluation Complete ===")
