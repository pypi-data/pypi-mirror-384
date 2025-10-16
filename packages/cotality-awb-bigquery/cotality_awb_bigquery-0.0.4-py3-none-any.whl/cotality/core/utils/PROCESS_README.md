# Parallel Task Execution Utilities

## Overview

The `cotality.core.utils.process` module provides a clean, type-safe way to execute tasks in parallel using Python's `concurrent.futures`. It supports both thread-based and process-based parallelism with comprehensive features for different use cases.

## Quick Start

```python
from cotality.core.utils.process import Task, execute_tasks_in_parallel

def add(a, b):
    return a + b

tasks = [
    Task(callback_function=add, arguments={'a': 1, 'b': 2}),
    Task(callback_function=add, arguments={'a': 3, 'b': 4}),
]

results = execute_tasks_in_parallel(tasks)
print(results)  # [3, 7]
```

## Key Features

### 1. **Three Execution Modes**

- **`execute_tasks_in_parallel()`** - Returns results in original order
- **`execute_tasks_in_parallel_unordered()`** - Returns results as they complete
- **`execute_tasks_in_parallel_streaming()`** - Yields results incrementally (memory efficient)

### 2. **Thread vs Process Selection**

The most important decision: **threads or processes?**

#### Use **Threads** (default) for:
- ✅ Network requests / API calls
- ✅ Database queries
- ✅ File I/O operations
- ✅ Sharing large data structures
- ✅ Lower overhead

#### Use **Processes** for:
- ✅ Heavy computation
- ✅ Image/video processing
- ✅ Data transformation
- ✅ True CPU parallelism
- ✅ Bypassing Python's GIL

### 3. **Memory Considerations**

**CRITICAL DIFFERENCE:**

```python
large_data = [1, 2, 3] * 1_000_000

# With THREADS: 1 copy in memory (shared)
tasks = [Task(func, {'data': large_data}) for _ in range(10)]
execute_tasks_in_parallel(tasks, use_processes=False)

# With PROCESSES: 10 copies in memory (isolated)
execute_tasks_in_parallel(tasks, use_processes=True)
```

## API Reference

### Task Dataclass

```python
@dataclass
class Task:
    callback_function: Callable  # Function to execute
    arguments: Dict[str, Any]    # Keyword arguments
```

### Main Functions

#### execute_tasks_in_parallel()

Execute tasks and return results in the same order as input.

```python
results = execute_tasks_in_parallel(
    tasks=tasks,
    max_workers=None,        # Auto-detect
    use_processes=False,     # Use threads by default
    return_exceptions=False  # Raise on error
)
```

#### execute_tasks_in_parallel_streaming()

Generator that yields results as they complete (memory efficient).

```python
for index, result in execute_tasks_in_parallel_streaming(
    tasks=tasks,
    max_workers=10,
    use_processes=False,
    return_exceptions=True,
    ordered=True  # or False for fastest completion
):
    print(f"Task {index}: {result}")
```

### Helper Functions

#### should_use_processes()

Recommends whether to use processes based on task type.

```python
use_procs = should_use_processes("cpu")  # True
use_procs = should_use_processes("io")   # False
```

#### is_picklable()

Check if an object can be used with processes.

```python
import threading
lock = threading.Lock()
is_picklable(lock)  # False - won't work with processes!
is_picklable([1, 2, 3])  # True - safe to use
```

## Common Patterns

### Pattern 1: API Requests (I/O-bound)

```python
def fetch_api(endpoint):
    response = requests.get(f"https://api.example.com/{endpoint}")
    return response.json()

tasks = [Task(fetch_api, {'endpoint': e}) for e in endpoints]
results = execute_tasks_in_parallel(tasks, max_workers=20)
```

### Pattern 2: Data Processing (CPU-bound)

```python
def process_image(image_path):
    img = load_image(image_path)
    return apply_heavy_transformation(img)

tasks = [Task(process_image, {'image_path': p}) for p in image_paths]
results = execute_tasks_in_parallel(tasks, use_processes=True, max_workers=4)
```

### Pattern 3: Large Dataset (Streaming)

```python
def process_record(record_id):
    # Process and save to database
    result = heavy_processing(record_id)
    save_to_db(result)
    return record_id

tasks = [Task(process_record, {'record_id': i}) for i in range(1_000_000)]

# Process without loading all results in memory
for index, record_id in execute_tasks_in_parallel_streaming(tasks, max_workers=50):
    if index % 1000 == 0:
        print(f"Processed {index} records")
```

### Pattern 4: Exception Handling

```python
tasks = [Task(risky_function, {'data': d}) for d in data_items]
results = execute_tasks_in_parallel(tasks, return_exceptions=True)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        logger.error(f"Task {i} failed: {result}")
    else:
        process_success(result)
```

## Pickling Constraints (Processes Only)

### ✅ Works (Picklable)
- Basic types: `int`, `str`, `list`, `dict`, `tuple`
- NumPy arrays, Pandas DataFrames
- Regular functions defined at module level
- Most user-defined classes

### ❌ Doesn't Work (Not Picklable)
- `threading.Lock`, `multiprocessing.Lock`
- Open file handles
- Database connections
- Lambda functions (use `def` instead)
- Nested/local functions
- Generators

## Performance Tips

1. **Start with threads** - Lower overhead, easier debugging
2. **Profile before switching to processes** - Only use if CPU is bottleneck
3. **Adjust max_workers** - More isn't always better (overhead increases)
4. **Use streaming for large workloads** - Avoid memory issues
5. **Batch small tasks** - Reduce overhead by grouping tiny operations

## Troubleshooting

### "Can't pickle X"
- **Solution**: Use threads instead, or refactor to use picklable objects
- Check with `is_picklable(obj)` first

### Slower with processes than threads
- **Cause**: Pickling overhead exceeds parallelism benefit
- **Solution**: Use threads or batch larger chunks of work

### Out of memory
- **Cause**: Processes copying large data, or accumulating too many results
- **Solution**: Use threads for shared data, or use streaming mode

## Examples

See `process_examples.py` for comprehensive examples covering all use cases.

Run examples:
```bash
python -m cotality.core.utils.process_examples
```

## When in Doubt

**Default to threads** - they work for 90% of use cases. Only switch to processes if:
1. You have CPU-bound work (verified by profiling)
2. Your data is small or simple types
3. You need true multi-core parallelism
