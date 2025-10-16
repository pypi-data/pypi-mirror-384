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
"""System utility functions."""
from __future__ import annotations

import os
from logging import getLogger

logger = getLogger(__name__)
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def available_memory_and_cpu() -> tuple[int, int, int, int]:
    """Calculate optimal memory and CPU based on available system resources.

    Returns:
        available_memory_mb: Available memory in MB
        total_memory_gb: Total memory in GB
        cpu_count: Number of CPU cores
        max_workers_by_cpu: Suggested max workers based on CPU count
    """

    if PSUTIL_AVAILABLE:
        # Get system memory information using psutil
        memory_info = psutil.virtual_memory()
        available_memory_mb = memory_info.available / 1024 / 1024
        total_memory_gb = memory_info.total / 1024 / 1024 / 1024

        logger.info(
            "Dynamic Resource Calculation (psutil):\n  - Total Memory: %.1f GB\n  - Available Memory: %.1f GB",
            total_memory_gb,
            available_memory_mb / 1024,
        )
    else:
        # Fallback: estimate based on heuristics without psutil
        logger.warning("psutil not available, using heuristic memory estimation")

        # Try to get a rough estimate using /proc/meminfo on Linux or default values
        try:
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", encoding="utf-8") as f:
                    meminfo = f.read()
                    total_kb = int(
                        [line for line in meminfo.split("\n") if "MemTotal:" in line][
                            0
                        ].split()[1]
                    )
                    available_kb = int(
                        [
                            line
                            for line in meminfo.split("\n")
                            if "MemAvailable:" in line
                        ][0].split()[1]
                    )
                    available_memory_mb = available_kb / 1024
                    total_memory_gb = total_kb / 1024 / 1024
            else:
                # Default conservative estimates
                available_memory_mb = 2048  # 2GB default
                total_memory_gb = 4.0  # 4GB default

            logger.info(
                "Dynamic Resource Calculation (fallback):\n"
                "  - Estimated Total Memory: %.1f GB\n"
                "  - Estimated Available Memory: %.1f GB",
                total_memory_gb,
                available_memory_mb / 1024,
            )
        except Exception:
            # Ultra-conservative fallback
            available_memory_mb = 1024  # 1GB default
            total_memory_gb = 2.0  # 2GB default
            logger.warning(
                "Could not determine memory, using conservative estimates: 2GB total, 1GB available"
            )

    cpu_count = os.cpu_count() or 4
    max_workers_by_cpu = min(cpu_count * 2, 8)

    logger.info(
        "CPU Count: (%d,%d), Suggested Max Workers by CPU: %d",
        os.cpu_count(),
        cpu_count,
        max_workers_by_cpu,
    )

    return (
        int(available_memory_mb),
        int(total_memory_gb),
        int(cpu_count),
        int(max_workers_by_cpu),
    )
