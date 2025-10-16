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
Cotality SDK

The Cotality Software Development Kit (SDK) provides comprehensive tools and utilities
for data processing, analysis, and application development. It includes modules for
working with various data sources, processing pipelines, visualization components,
and enterprise-grade utilities.

This SDK is designed to support enterprise data workflows with robust error handling,
comprehensive documentation, and scalable architecture patterns.

Author: Cotality Data Engineering Team
Version: 1.0.0
Last Updated: August 2025
License: Apache License 2.0

Main Packages:
    core: Core utilities and interfaces for data processing
    app: Application frameworks and UI components
    xapi: External API integrations and connectors
    platform: Platform-specific implementations
    snowflake: Snowflake-specific utilities and connectors
    local: Local development and testing utilities

Examples:
    Basic DataFrame comparison:
        >>> from cotality.core.utils import compare_dataframes
        >>> import pandas as pd
        >>> df1 = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})
        >>> df2 = pd.DataFrame({'id': [1, 3], 'value': [10, 30]})
        >>> result = compare_dataframes(df1, df2, key_column='id')
        >>> print(result['counts']['total_differences'])

    Application development:
        >>> from cotality.app.panel import create_dashboard
        >>> dashboard = create_dashboard(data_source='example.csv')

For more information, visit: https://cotality.com/docs
"""

__version__ = "1.0.0"
__author__ = "Cotality Data Engineering Team"
__license__ = "Apache License 2.0"
__copyright__ = "Copyright 2025 Cotality"

# Core imports for easy access
try:
    from .core.utils import (
        compare_dataframes,
        compare_with_composite_key,
        hash_based_comparison,
        quick_comparison_summary,
    )

    __all__ = [
        "compare_dataframes",
        "hash_based_comparison",
        "compare_with_composite_key",
        "quick_comparison_summary",
    ]
except ImportError:
    # Handle cases where dependencies might not be available
    __all__ = []
