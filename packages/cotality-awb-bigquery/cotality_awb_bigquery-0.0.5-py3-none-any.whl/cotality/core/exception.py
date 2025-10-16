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
"""Standard Corelogic exception."""
from __future__ import annotations

import traceback
import uuid
from typing import Any

from .error_codes import CommonErrorCodes
from .locale import Localization


class ClgxException(Exception):
    """Standard Corelogic exception class."""

    def __init__(
        self,
        error: CommonErrorCodes,
        parameters: dict[Any, Any] | None = None,
        message: str | None = "",
        cause: Exception | None = None,
    ):
        """Corelogic standard Exception.

        Args:
            error (CommonErrorCodes): Error code
            parameters (Optional[dict], optional): Required parameters for this error code. Defaults to None.
            message (Optional[str], optional): Additional internal message. Defaults to "".
            cause (Optional[Exception], optional): aused exception. Defaults to None.
        """
        # Save the state for Serialization/Deserialization
        self.__error = error
        self.__parameters = parameters
        self.__message = message
        self.__cause = cause
        self.__localization = Localization()
        # Find the root cause (the very first exception in the chain)
        self.__root_cause = self._find_root_cause(cause)

        # Capture stack trace at exception creation time (fallback)
        self.__creation_stack_trace = traceback.format_stack()

        self.__case_number = uuid.uuid4().hex
        if not error:
            error = CommonErrorCodes.GEN_RUN_TIME

        (
            self.__error_type,
            self.__error_number,
            self.__error_msg_template,
            self.__system_type,
        ) = error.parse

        # Set error code from the exception Type and Number
        self.__error_code = f"{self.__error_type}-{self.__error_number}"

        # translate the key if it finds it
        template_msg = self.__error_msg_template
        if hasattr(Localization, "instance") or Localization.instance is not None:
            if self.__localization._(template_msg) != template_msg:
                template_msg = self.__localization._(template_msg)

        # Replace the Text template with the values from parameters
        if template_msg and parameters:
            template_msg = template_msg.format(**parameters)

        self.__external_message = f"{template_msg}.{message}"
        self.__msg = (
            f"Case:{self.__case_number}, Error:{self.__error_code}, "
            f"Message:{self.__external_message}, Cause:{cause}, SystemType:{self.__system_type}"
        )
        super().__init__(self.__msg)

    def _find_root_cause(self, cause: Exception | None) -> Any:
        """Find the root cause (the very first exception) in the exception chain.

        Args:
            cause: The immediate cause exception

        Returns:
            The root cause exception, or None if no cause
        """
        if cause is None:
            return None

        # Traverse the exception chain to find the root
        root = cause

        # Follow standard Python exception chaining (__cause__)
        while hasattr(root, "__cause__") and root.__cause__ is not None:
            root = root.__cause__

        # Also follow __context__ chain (implicit exception context)
        if hasattr(root, "__context__") and root.__context__ is not None:
            context_root = root.__context__
            while (
                hasattr(context_root, "__cause__")
                and context_root.__cause__ is not None
            ):
                context_root = context_root.__cause__
            root = context_root

        return root

    def __reduce__(self):
        return ClgxException, (
            self.__error,
            self.__parameters,
            self.__message,
            self.__cause,
        )

    @property
    def external_message(self) -> str:
        """Return external message.

        Returns:
            str: External message
        """
        return self.__external_message

    @property
    def error_type(self) -> str:
        """Return error type.

        Returns:
            str: Error type.
        """
        return self.__error_type

    @property
    def error_code(self) -> str:
        """Return error code.

        Returns:
            str: Error code.
        """
        return self.__error_code

    @property
    def stack_trace(self) -> str:
        """Return stack trace from the root cause (original exception).

        Returns:
            str: Stack trace showing the root cause location, or creation location if no cause
        """
        if self.__root_cause is not None:
            # Show the stack trace from the root cause
            if (
                hasattr(self.__root_cause, "__traceback__")
                and self.__root_cause.__traceback__ is not None
            ):
                return "".join(
                    traceback.format_exception(
                        type(self.__root_cause),
                        self.__root_cause,
                        self.__root_cause.__traceback__,
                    )
                )
            return f"Root cause: {type(self.__root_cause).__name__}: {str(self.__root_cause)}"

        # Fallback to creation stack trace if no root cause
        return "".join(self.__creation_stack_trace)

    @property
    def creation_location(self) -> str:
        """Return a concise description of where the root cause originated.

        Returns:
            str: File name, line number, and function where the root cause was created
        """
        if self.__root_cause is not None:
            if (
                hasattr(self.__root_cause, "__traceback__")
                and self.__root_cause.__traceback__ is not None
            ):
                tb = self.__root_cause.__traceback__
                # Get the deepest frame (where the original exception occurred)
                while tb.tb_next is not None:
                    tb = tb.tb_next
                return f'File "{tb.tb_frame.f_code.co_filename}", line {tb.tb_lineno}, in {tb.tb_frame.f_code.co_name}'
            return f"Root cause: {type(self.__root_cause).__name__}: {str(self.__root_cause)}"

        # Fallback to creation location if no root cause
        if len(self.__creation_stack_trace) >= 2:
            # Get the caller's frame (skip this __init__ method)
            caller_frame = self.__creation_stack_trace[-2]
            return caller_frame.strip()
        return "Unknown location"

    @property
    def root_cause(self) -> Any:
        """Return the root cause exception.

        Returns:
            The original exception that started the chain, or None if no cause
        """
        return self.__root_cause

    @property
    def system_type(self) -> str:
        """Return system type as string.

        Returns:
            str: System type (SYSTEM or CUSTOMER)
        """
        return self.__system_type

    def __str__(self) -> str:
        """Return string representation of this exception with stack trace.

        This is called when the exception is printed or converted to string.
        Always includes the stack trace regardless of whether there's a cause or not.

        Returns:
            str: Exception as string with full stack trace
        """
        # Always include the stack trace in the string representation
        return f"{self.__msg}\n\nStack Trace:\n{self.stack_trace}"

    def compact_string(self) -> str:
        """Return compact string representation without stack trace.

        Useful for logging or UI where you want just the basic error info.

        Returns:
            str: Exception message with root cause info but no stack trace
        """
        if self.__root_cause is not None:
            return f"{self.__msg} | Root Cause: {type(self.__root_cause).__name__}: {str(self.__root_cause)}"
        return self.__msg
