# MB Utils

[![Python Version](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/bigmb/mb_utils/graphs/commit-activity)
[![Downloads](https://static.pepy.tech/badge/mb_utils)](https://pepy.tech/project/mb_utils)

A collection of utility functions and tools to simplify common Python development tasks. This package provides various helper functions for logging, file operations, S3 interactions, and more.

## Features

- **Logging**: Easy-to-use logging setup with file handlers
- **File Operations**: Path checking and validation
- **Decorators**: Useful decorators for deprecation warnings and retry logic
- **Image Verification**: Validate and verify image files
- **S3 Integration**: Simplified AWS S3 file and directory operations
- **Utilities**: Various helper functions including timing and batching

##  Installation

Install the package using pip:

```bash
pip install mb_utils
```

## Usage

### Logging
```python
from mb_utils.src.logging import logger

logger.info("This is an info message")
logger.error("This is an error message")
```

### Path Checking
```python
from mb_utils.src.path_checker import check_path

check_path(path_list,max_workers=16)
```

### Retry Decorator
```python
from mb_utils.src.retry_decorator import retry

@retry(max_retries=3, delay=1)
def might_fail():
    pass
```

### S3 Operations
```python
from mb_utils.src.s3 import upload_file, download_file, upload_dir, download_dir

# Upload a single file
upload_file('local_file.txt', 'bucket-name', 'remote_file.txt')

# Download a file
download_file('bucket-name', 'remote_file.txt', 'local_file.txt')
```

##  Available Modules

| Module | Description | Import Path |
|--------|-------------|-------------|
| logging | Logger setup with file handlers | `from mb_utils.src.logging import logger` |
| path_checker | Path validation utilities | `from mb_utils.src.path_checker import *` |
| deprecated | Function deprecation decorator | `from mb_utils.src.deprecated import deprecated_func` |
| verify_image | Image verification | `from mb_utils.src.verify_image import verify_image` |
| retry_decorator | Retry mechanism for functions | `from mb_utils.src.retry_decorator import retry` |
| s3 | AWS S3 operations | `from mb_utils.src.s3 import *` |
| extra | Additional utilities | `from mb_utils.src.extra import *` |
| profiler | Code profiling utilities | `from mb_utils.src.profiler import *` |


##  Profiling

The `profiler` module provides utilities for performance analysis of your Python code.

### Function Profiling with SnakeViz
```python
from mb_utils.src.profiler import run_with_snakeviz

@run_with_snakeviz(save_only=False)  # Opens SnakeViz automatically
def process_data(data):
    pass

# Or use as context manager
with run_with_snakeviz():
    pass
```

### Line-by-Line Profiling
```python
from mb_utils.src.profiler import line_profile

@line_profile
def process_item(item):
    result = item * 2
    return result
```

### Simple Timing
```python
from mb_utils.src.profiler import time_it

@time_it
def expensive_operation():
    pass
```

### Memory Profiling
```python
from mb_utils.src.profiler import MemoryProfiler

def process_large_data():
    with MemoryProfiler() as mem:
        data = [0] * 10**6
```

### Comprehensive Profiling
```python
from mb_utils.src.profiler import profile_function

@profile_function(
    enable_line_profiling=True,
    enable_memory_profiling=True
)
def analyze_data(data):
    # Will run with multiple profiling tools
    pass
```

## Included Scripts

- `verify_images_script`: Utility script for image verification

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

