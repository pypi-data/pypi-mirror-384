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
"""Common Decorator."""
import threading
import time
from functools import wraps
from logging import getLogger

logger = getLogger(__name__)


class SingletonMeta(type):
    """
    A thread-safe metaclass for creating singleton classes.

    This metaclass ensures that only one instance of any class that uses it
    is ever created. It is robust enough to handle:
    1.  Inheritance: Each subclass will be its own singleton.
    2.  Multiple Decorators: Works seamlessly when stacked with other decorators.

    Usages:
    1. Basic Singleton:
       class MyClass(metaclass=SingletonMeta):
           def __init__(self, *args, **kwargs):
               # Initialization code here
    2. More complicated usage with decorators:
       @decorator1
       @decorator2
       class MyClass(metaclass=SingletonMeta, ExtendsAnotherClass):
           def __init__(self, *args, **kwargs):
               # Initialization code here

    """

    # _instances = {}
    # _lock = threading.Lock()

    # def __call__(cls, *args, **kwargs):
    #    """
    #    This method is called when an instance of the class is created (e.g., MyClass()).
    #    It overrides the default class instantiation process.
    #    """
    #    # Use a lock to ensure thread-safety during the first instantiation.
    #    with cls._lock:
    #        # Check if an instance of this specific class already exists in our cache.
    #        # Using the class itself (cls) as the key handles inheritance correctly.
    #        if cls.__name__ not in cls._instances:
    #            # If not, create a new instance by calling the parent's __call__
    #            # (which in turn calls __new__ and __init__) and store it.
    #            print(f"**************> Creating a new instance of {cls.__name__}")
    #            instance = super().__call__(*args, **kwargs)
    #            cls._instances[cls.__name__] = instance

    #    for key, value in cls._instances.items():
    #        print(f"**************> {key} instance: {value}")

    # Return the single instance from the cache.
    #    return cls._instances[cls.__name__]


def singleton(cls):
    """
    DO NOT use this decorator. Will be removed!
    This decorator will not work if your class extends another class!.
    Use the avove SingletonMeta metaclass instead.

    Ensures only one instance of the decorated class is created,
    even in a multi-threaded environment.
    """
    # Store instances in a class-level dictionary
    instances = {}
    # Lock for thread safety
    lock = threading.Lock()

    @wraps(cls)
    def wrapper(*args, **kwargs):
        # Use double-checked locking for efficiency
        if cls.__name__ not in instances:
            with lock:
                # Check again inside the lock to avoid race condition
                if cls.__name__ not in instances:
                    logger.info(
                        "***** Creating new instance of class %s.", cls.__name__
                    )
                    instances[cls.__name__] = cls(*args, **kwargs)
        return instances[cls.__name__]

    return wrapper


def api_retry(api, success_codes: list, max_retries=3, delay=60):
    """
    A decorator to retry a function call if it raises an exception.

    Args:
        api (str): The name of the API being called, used for logging.
        success_codes (list): List of HTTP status codes that indicate success.
        max_retries (int): Maximum number of retries before giving up.
        delay (int): Delay in seconds between retries.

    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    api_response = func(*args, **kwargs)
                    if api_response.status_code in success_codes:
                        return api_response
                    logger.error(
                        "Failed to call API: %s. Attempts:%s, Status code: %s, Response: %s",
                        api,
                        attempt,
                        api_response.status_code,
                        api_response.text,
                    )
                    time.sleep(delay)
                except Exception as e:
                    logger.error(
                        "Failed to call API: %s. Attempts:%s, Error: %s",
                        api,
                        attempt,
                        str(e),
                    )
                    time.sleep(delay)

        return wrapper

    return decorator
