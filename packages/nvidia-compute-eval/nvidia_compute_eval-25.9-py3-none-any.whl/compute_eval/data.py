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

import gzip
import json
import os
import sys
from typing import Dict, Iterable

ROOT = os.path.dirname(os.path.abspath(__file__))


def resolve_data_file_path(filename: str) -> str:
    """
    Resolve the path to a data file, handling both packaged and development scenarios.
    
    This function checks for data files in the following order:
    1. If the filename starts with 'data/', look for the file in the packaged data directory
    2. Try the filename as provided (relative to current working directory)
    3. Try looking in common development locations
    
    Args:
        filename: The filename/path to resolve
        
    Returns:
        str: The resolved absolute path to the file
        
    Raises:
        FileNotFoundError: If the file cannot be found in any location
    """
    # If filename starts with 'data/', try to find it in the packaged data
    if filename.startswith('data/'):
        # Extract just the filename without the 'data/' prefix
        basename = filename[5:]  # Remove 'data/' prefix
        
        # Try to find the data directory in the package installation
        # This checks for data installed alongside the package
        package_root = os.path.dirname(os.path.dirname(ROOT))  # Go up from compute_eval to package root
        package_data_path = os.path.join(package_root, 'data', basename)
        
        if os.path.exists(package_data_path):
            return package_data_path
            
        # Try site-packages data directory (for installed packages)
        try:
            import site
            for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
                if site_dir:
                    site_data_path = os.path.join(site_dir, 'data', basename)
                    if os.path.exists(site_data_path):
                        return site_data_path
        except:
            pass
    
    # Try the filename as provided (relative to current working directory)
    if os.path.exists(filename):
        return os.path.abspath(filename)
    
    # Try common development locations
    common_locations = [
        os.path.join(os.getcwd(), filename),
        os.path.join(ROOT, '..', filename),  # One level up from compute_eval module
        os.path.join(ROOT, '..', '..', filename),  # Two levels up (package root)
        '/workspace/' + filename,  # CI environment
    ]
    
    for location in common_locations:
        if os.path.exists(location):
            return os.path.abspath(location)
    
    # If we still can't find it, raise an error with helpful information
    search_locations = [filename] + common_locations
    if filename.startswith('data/'):
        search_locations.insert(0, package_data_path)
    
    raise FileNotFoundError(
        f"Could not find data file: {filename}\n"
        f"Searched in the following locations:\n" + 
        "\n".join(f"  - {loc}" for loc in search_locations) +
        f"\n\nCurrent working directory: {os.getcwd()}\n"
        f"Python path: {sys.path}"
    )


def read_problems(evalset_file: str) -> Dict[str, Dict]:
    resolved_path = resolve_data_file_path(evalset_file)
    return {task["task_id"]: task for task in stream_jsonl(resolved_path)}


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    # Resolve the path if it hasn't been resolved already
    if not os.path.isabs(filename):
        filename = resolve_data_file_path(filename)
        
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, "rt") as fp:
                for line in fp:
                    if any(not x.isspace() for x in line):
                        yield json.loads(line, strict=False)
    else:
        with open(filename, "r") as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line, strict=False)


def write_completions_to_dir(dir_path: str, data: Iterable[Dict]):
    """
    Writes the prompt, pass / fail and the completion of each provided sample
    to a specific directory.

    REQUIRES: Each dict in the data iterable must have the keys "prompt",
    "completion", "completion_id" and "passed".
    """

    full_dir_path = os.path.abspath(dir_path)
    for sample in data:
        passed_string = "// " + ("PASSED" if sample["passed"] else "FAILED")
        prompt = sample["prompt"]
        file_path = os.path.join(
            full_dir_path,
            f"{sample['task_id'].replace('/', '_')}__{sample['completion_id']}.cu",
        )
        with open(file_path, "w+") as outfile:
            outfile.write(passed_string + "\n")
            outfile.write("/*\n" + prompt + "\n*/\n")
            outfile.write(sample["compilable_code"])


def write_jsonl(filename: str, data: Iterable[Dict], append: bool = False):
    """
    Writes an iterable of dictionaries to jsonl
    """
    if append:
        mode = "ab"
    else:
        mode = "wb"
    filename = os.path.expanduser(filename)
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode="wb") as gzfp:
                for x in data:
                    if x:
                        gzfp.write((json.dumps(x) + "\n").encode("utf-8"))
    else:
        with open(filename, mode) as fp:
            for x in data:
                if x:
                    fp.write((json.dumps(x) + "\n").encode("utf-8"))
