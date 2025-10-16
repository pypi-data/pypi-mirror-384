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
"""Logger."""
from __future__ import annotations

import gettext
import locale
from pathlib import Path

from .error_codes import CommonErrorCodes


def Localization(language: str = "", platform_type: str = ""):
    if not hasattr(Localization, "instance") or Localization.instance is None:
        Localization.instance = _Localization(language, platform_type)
    return Localization.instance


class _Localization:
    """Localization for CLIP"""

    def __init__(self, language: str, platform_type: str):
        """Initialize locale language. based on the language param"""
        self._get_text = lambda a: a  # palaceholder for get_text
        self._platform_type = platform_type

        locale_path = Path(__file__).parent / "locales"

        if not locale_path.exists():
            raise FileNotFoundError(f"Locale path not found: {locale_path}")

        language_path = locale_path
        if not language_path.exists():
            language_path = locale_path / language[0:2]  # Language path only, ex: en

        if not language_path.exists():
            raise FileNotFoundError(f"Locale file not found: {language_path}")

        locale.setlocale(locale.LC_ALL, f"{language}.UTF-8")
        language_package = gettext.translation(
            "base", localedir=str(language_path), languages=[language]
        )
        language_package.install()
        self._get_text = language_package.gettext

    def _(self, key: str):
        """
        Returns localization based on Plataform if this one
        exists in the base.po file
        """
        _key = f"{key}_{self._platform_type}"
        output = self._get_text(_key)
        if output == _key:
            return self._get_text(key)
        return output
