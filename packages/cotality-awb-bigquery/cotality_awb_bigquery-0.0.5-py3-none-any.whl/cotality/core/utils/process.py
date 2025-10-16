# Copyright 2025 Cotality
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Parallel task execution utilities.

This module provides utilities for executing tasks in parallel using concurrent futures.
It offers flexible options for both thread-based (I/O-bound) and process-based (CPU-bound)
parallel execution with comprehensive error handling and memory management.

Author: Cotality Data Engineering Team
Version: 1.0.0
Last Updated: October 2025

CHOOSING BETWEEN THREADS AND PROCESSES
=======================================

Use THREADS (use_processes=False, default):
-------------------------------------------
✓ I/O-bound tasks (network requests, file I/O, database queries)
✓ Tasks that share large data structures (memory efficient)
✓ Lower overhead and faster startup
✓ Objects can be any type (no pickling required)
✓ Easier debugging

Limitations:
- Python's GIL limits true CPU parallelism
- Not suitable for CPU-intensive computations

Use PROCESSES (use_processes=True):
------------------------------------
✓ CPU-bound tasks (data processing, computations, encoding)
✓ True parallelism across multiple CPU cores (bypasses GIL)
✓ Tasks are independent with minimal data sharing
✓ Arguments and results are small or simple types

Important Considerations:
- NO MEMORY SHARING: Each process has isolated memory
- Arguments/results are PICKLED (serialized) - higher overhead
- Objects must be picklable (no locks, file handles, etc.)
- Higher memory usage (each process copies data)
- Slower startup time

MEMORY IMPLICATIONS
===================

With Threads:
    large_data = [1, 2, 3] * 1_000_000
    tasks = [Task(func, {'data': large_data}) for _ in range(10)]
    # Memory: 1 copy shared across all threads ✓

With Processes:
    large_data = [1, 2, 3] * 1_000_000
    tasks = [Task(func, {'data': large_data}) for _ in range(10)]
    # Memory: 10 copies (one per process) - expensive! ⚠️

PICKLING CONSTRAINTS (Processes Only)
======================================

Works (picklable):
    - Basic types: int, str, list, dict, tuple
    - NumPy arrays, Pandas DataFrames
    - Most user-defined classes and functions

Does NOT work (not picklable):
    - threading.Lock, multiprocessing.Lock
    - Open file handles
    - Database connections
    - Lambda functions (use def instead)
    - Nested/local functions

Example:
    import threading
    lock = threading.Lock()
    tasks = [Task(func, {'lock': lock})]
    execute_tasks_in_parallel(tasks, use_processes=True)  # ❌ FAILS!
    execute_tasks_in_parallel(tasks, use_processes=False) # ✓ WORKS

QUICK DECISION GUIDE
====================

Choose based on your bottleneck:
    - Network/Database calls → THREADS
    - File I/O operations → THREADS
    - API requests → THREADS
    - Heavy computations → PROCESSES
    - Image/video processing → PROCESSES
    - Data transformation → PROCESSES
    - Cryptography → PROCESSES

When in doubt: Start with THREADS (default), switch to PROCESSES if CPU is bottleneck.
"""

import logging
import pickle
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# Private module-level constants for task type detection
_CPU_TASK_INDICATORS = frozenset(
    {"cpu", "cpubound", "compute", "computational", "calculation"}
)
_IO_TASK_INDICATORS = frozenset({"io", "iobound", "i/o", "network", "database", "file"})


@dataclass
class Task:
    """
    Represents a task to be executed in parallel.

    Attributes:
        callback_function: The function to execute
        arguments: Dictionary of keyword arguments to pass to the function
    """

    callback_function: Callable
    arguments: Dict[str, Any]


def execute_tasks_in_parallel(
    tasks: List[Task],
    max_workers: Optional[int] = None,
    use_processes: bool = False,
    return_exceptions: bool = False,
) -> List[Union[Any, Exception]]:
    """
    Execute a list of tasks in parallel using thread or process pools.

    Args:
        tasks: List of Task objects to execute
        max_workers: Maximum number of worker threads/processes.
                    If None, defaults to min(32, (os.cpu_count() or 1) + 4)
        use_processes: If True, use ProcessPoolExecutor for CPU-bound tasks (true parallelism).
                      If False (default), use ThreadPoolExecutor for I/O-bound tasks.

                      WARNING: With processes, arguments are PICKLED and memory is NOT shared.
                      Each process gets a COPY of the data. Use threads if sharing large objects.

                      See module docstring for detailed guidance on choosing threads vs processes.
        return_exceptions: If True, exceptions are returned as results instead of being raised.

    Returns:
        List of results from each task execution, in the same order as the input tasks.

    Raises:
        Exception: If any task raises an exception and return_exceptions is False.

    Example:
        >>> def add(a, b):
        ...     return a + b
        >>>
        >>> def multiply(x, y):
        ...     return x * y
        >>>
        >>> tasks = [
        ...     Task(callback_function=add, arguments={'a': 1, 'b': 2}),
        ...     Task(callback_function=multiply, arguments={'x': 3, 'y': 4}),
        ... ]
        >>>
        >>> results = execute_tasks_in_parallel(tasks)
        >>> print(results)  # [3, 12]
    """
    if not tasks:
        logger.warning("No tasks provided to execute_tasks_in_parallel")
        return []

    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    results: List[Union[Any, Exception]] = [None] * len(tasks)

    with executor_class(max_workers=max_workers) as executor:
        # Submit all tasks and keep track of their original index
        future_to_index = {}
        for index, task in enumerate(tasks):
            try:
                future = executor.submit(task.callback_function, **task.arguments)
                future_to_index[future] = index
            except Exception as e:
                logger.error("Failed to submit task %d: %s", index, e)
                if return_exceptions:
                    results[index] = e
                else:
                    raise

        # Collect results as they complete
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
                logger.debug("Task %d completed successfully", index)
            except Exception as e:
                logger.error("Task %d raised an exception: %s", index, e)
                if return_exceptions:
                    results[index] = e
                else:
                    raise

    return results


def execute_tasks_in_parallel_unordered(
    tasks: List[Task],
    max_workers: Optional[int] = None,
    use_processes: bool = False,
    return_exceptions: bool = False,
) -> List[Union[Any, Exception]]:
    """
    Execute a list of tasks in parallel and return results as they complete (unordered).

    This function is similar to execute_tasks_in_parallel but yields results as soon as
    they are available, without preserving the original order.

    Args:
        tasks: List of Task objects to execute
        max_workers: Maximum number of worker threads/processes
        use_processes: If True, use ProcessPoolExecutor for CPU-bound tasks (true parallelism).
                      If False (default), use ThreadPoolExecutor for I/O-bound tasks.

                      WARNING: With processes, arguments are PICKLED and memory is NOT shared.
                      See module docstring for detailed guidance.
        return_exceptions: If True, exceptions are returned as results instead of being raised

    Returns:
        List of results from each task execution, in completion order (not input order).

    Example:
        >>> import time
        >>>
        >>> def slow_task(duration, value):
        ...     time.sleep(duration)
        ...     return value
        >>>
        >>> tasks = [
        ...     Task(callback_function=slow_task, arguments={'duration': 2, 'value': 'first'}),
        ...     Task(callback_function=slow_task, arguments={'duration': 1, 'value': 'second'}),
        ... ]
        >>>
        >>> results = execute_tasks_in_parallel_unordered(tasks)
        >>> print(results)  # ['second', 'first'] - second completes first
    """
    if not tasks:
        logger.warning("No tasks provided to execute_tasks_in_parallel_unordered")
        return []

    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    results: List[Union[Any, Exception]] = []

    with executor_class(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = []
        for index, task in enumerate(tasks):
            try:
                future = executor.submit(task.callback_function, **task.arguments)
                futures.append(future)
            except Exception as e:
                logger.error("Failed to submit task %d: %s", index, e)
                if return_exceptions:
                    results.append(e)
                else:
                    raise

        # Collect results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                logger.debug("Task completed successfully")
            except Exception as e:
                logger.error("Task raised an exception: %s", e)
                if return_exceptions:
                    results.append(e)
                else:
                    raise

    return results


def execute_tasks_in_parallel_streaming(
    tasks: List[Task],
    max_workers: Optional[int] = None,
    use_processes: bool = False,
    return_exceptions: bool = False,
    ordered: bool = True,
) -> Generator[Union[Tuple[int, Any], Tuple[int, Exception]], None, None]:
    """
    Generator that yields task results as they complete (memory-efficient streaming).

    This function is ideal for processing large numbers of tasks where you want to:
    - Process results as soon as they're available
    - Avoid holding all results in memory at once
    - Monitor progress in real-time
    - Handle results with minimal latency

    Args:
        tasks: List of Task objects to execute
        max_workers: Maximum number of worker threads/processes
        use_processes: If True, use ProcessPoolExecutor for CPU-bound tasks (true parallelism).
                      If False (default), use ThreadPoolExecutor for I/O-bound tasks.

                      WARNING: With processes, arguments are PICKLED and memory is NOT shared.
                      See module docstring for detailed guidance.
        return_exceptions: If True, exceptions are yielded as results instead of being raised
        ordered: If True, yield results in original task order. If False, yield as completed.

    Yields:
        Tuples of (index, result) where index is the position in the original tasks list
        and result is the return value from the task (or Exception if return_exceptions=True).

    Raises:
        Exception: If any task raises an exception and return_exceptions is False.

    Example:
        >>> def process_item(item_id):
        ...     # Some processing
        ...     return f"Processed {item_id}"
        >>>
        >>> tasks = [
        ...     Task(callback_function=process_item, arguments={'item_id': i})
        ...     for i in range(1000)  # Large number of tasks
        ... ]
        >>>
        >>> # Process results as they complete without holding all in memory
        >>> for index, result in execute_tasks_in_parallel_streaming(tasks):
        ...     print(f"Task {index}: {result}")
        ...     # Save to database, write to file, etc.

    Example with ordered=False for fastest processing:
        >>> for index, result in execute_tasks_in_parallel_streaming(tasks, ordered=False):
        ...     print(f"Completed task {index}: {result}")
    """
    if not tasks:
        logger.warning("No tasks provided to execute_tasks_in_parallel_streaming")
        return

    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor

    with executor_class(max_workers=max_workers) as executor:
        # Submit all tasks and keep track of their original index
        future_to_index: Dict[Any, int] = {}
        for index, task in enumerate(tasks):
            try:
                future = executor.submit(task.callback_function, **task.arguments)
                future_to_index[future] = index
            except Exception as e:
                logger.error("Failed to submit task %d: %s", index, e)
                if return_exceptions:
                    yield (index, e)
                else:
                    raise

        if ordered:
            # Collect all results first, then yield in order
            results: Dict[int, Union[Any, Exception]] = {}
            next_index_to_yield = 0

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                    logger.debug("Task %d completed successfully", index)
                except Exception as e:
                    logger.error("Task %d raised an exception: %s", index, e)
                    if return_exceptions:
                        results[index] = e
                    else:
                        # Clean up futures before raising
                        future_to_index.clear()
                        raise

                # Yield any results that are now in sequence
                while next_index_to_yield in results:
                    yield (next_index_to_yield, results[next_index_to_yield])
                    # Clear the result from memory immediately after yielding
                    del results[next_index_to_yield]
                    next_index_to_yield += 1
        else:
            # Yield results as they complete (unordered, fastest)
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    logger.debug("Task %d completed successfully", index)
                    yield (index, result)
                except Exception as e:
                    logger.error("Task %d raised an exception: %s", index, e)
                    if return_exceptions:
                        yield (index, e)
                    else:
                        # Clean up futures before raising
                        future_to_index.clear()
                        raise

        # Clear the future mapping to help garbage collection
        future_to_index.clear()


def should_use_processes(task_type: str = "io") -> bool:
    """
    Helper function to determine whether to use processes or threads.

    This is a convenience function to help users choose the right executor type
    based on their workload characteristics.

    Args:
        task_type: Type of task being performed. Options:
                  - "io" or "i/o" or "io-bound": Network, file I/O, database (default)
                  - "cpu" or "cpu-bound" or "compute": Heavy computation
                  - "mixed": Both I/O and CPU work

    Returns:
        True if processes are recommended, False if threads are recommended.

    Example:
        >>> task_type = "cpu"  # or detect automatically based on profiling
        >>> use_procs = should_use_processes(task_type)
        >>> results = execute_tasks_in_parallel(tasks, use_processes=use_procs)

    Notes:
        - For "mixed" workloads, threads are recommended by default (lower overhead)
        - Consider your data size: large shared data → threads, small data → processes OK
        - This is a guideline; profile your specific workload for best results
    """
    task_type_lower = task_type.lower().replace("-", "").replace("/", "")

    if any(indicator in task_type_lower for indicator in _CPU_TASK_INDICATORS):
        logger.info("Recommending processes for CPU-bound tasks")
        return True
    if any(indicator in task_type_lower for indicator in _IO_TASK_INDICATORS):
        logger.info("Recommending threads for I/O-bound tasks")
        return False
    # Default to threads for unknown/mixed workloads (safer, lower overhead)
    logger.info(
        "Unknown task type '%s', defaulting to threads (lower overhead)", task_type
    )
    return False


def is_picklable(obj: Any) -> bool:
    """
    Check if an object can be pickled (required for ProcessPoolExecutor).

    Use this function to validate that your task arguments can be used with
    processes before executing tasks.

    Args:
        obj: Any Python object to test

    Returns:
        True if the object can be pickled, False otherwise.

    Example:
        >>> import threading
        >>> lock = threading.Lock()
        >>> is_picklable(lock)
        False
        >>> is_picklable({'key': 'value'})
        True
        >>> is_picklable([1, 2, 3])
        True

    Notes:
        - Common non-picklable objects: locks, file handles, database connections
        - Lambda functions and nested functions are often not picklable
        - Use regular 'def' functions instead of lambdas for process pools
    """
    try:
        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, TypeError, AttributeError) as e:
        logger.debug("Object is not picklable: %s", e)
        return False
