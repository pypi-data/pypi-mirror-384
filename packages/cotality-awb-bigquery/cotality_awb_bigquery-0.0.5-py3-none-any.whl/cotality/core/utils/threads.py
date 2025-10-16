# Copyright 2022 CORELOGIC
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

"""Thread utilities."""

import json
import logging
import multiprocessing
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CallbackException:
    """Callback function."""

    thread_id: int
    start_time: datetime
    input: object
    output: object
    end_time: datetime = datetime.now()
    exception: Optional[str] = ""


def to_message(exceptions: List[CallbackException]) -> str:
    """Consolidate all exceptions to a log format text message.

    Parameters:
        exceptions - call back exceptions
        only_error - Default is False. If set, only exception exceptions are included in the log message

    Returns: str - Log message
    """
    msg = ""
    if exceptions and len(exceptions) > 0:
        messages = []
        for exp in exceptions:
            messages.append(
                {
                    "thread_id": exp.thread_id,
                    "input": exp.input,
                    "output": exp.output,
                    "time": str({exp.end_time - exp.start_time}),
                    "exception": exp.exception,
                }
            )
        msg = json.dumps(messages, indent=2)
    return msg


def multi_thread_execute(
    callback, parameters: List, log_function=logger.info
) -> List[CallbackException]:
    """Execute the provided callback function with multithreads.

    Parameters:
        callback - Callback function
        parameters - List of payloads to be consumed by the callback

    Returns: List of callback CallbackResult
    """
    start_time = datetime.now()
    exceptions: List[CallbackException] = []
    len_params = len(parameters)
    que: queue.Queue = queue.Queue(maxsize=len_params)
    max_cores = multiprocessing.cpu_count()
    max_threads = max_cores if len_params >= max_cores else len_params
    max_threads = min(max_cores, len_params)

    log_function(
        "Thread execution - Queing. Method:%s, Len(Parameters):%d, Max Threads:%d",
        callback,
        len_params,
        max_threads,
    )
    for param in parameters:
        que.put(param)

    log_function(
        "Thread execution - Threading. Method:%s, Len(Parameters):%d, Max Threads:%d}",
        callback,
        len_params,
        max_threads,
    )
    for thread_id in range(max_threads):
        try:
            worker = threading.Thread(
                target=callback, args=(thread_id, que, exceptions, log_function)
            )
            worker.start()
        except Exception as ex:
            exceptions.append(
                CallbackException(
                    thread_id=thread_id,
                    start_time=start_time,
                    input="Thread",
                    output="Thread",
                    exception=str(ex),
                )
            )
    log_function(
        "Thread execution - Joining. Method:%s, Len(Parameters):%d, Max Threads:%d",
        callback,
        len_params,
        max_threads,
    )
    que.join()

    log_function(
        "Thread execution - Finished. Method:%s, Len(Parameters):%d, Max Threads:%d",
        callback,
        len_params,
        max_threads,
    )
    return exceptions
