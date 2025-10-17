#
# The internetarchive module is a Python/CLI interface to Archive.org.
#
# Copyright (C) 2012-2024 Internet Archive
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
internetarchive.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (C) 2012-2024 by Internet Archive.
:license: AGPL 3, see LICENSE for more details.
"""

from typing import Dict, Optional


class AuthenticationError(Exception):
    """Authentication Failed"""


class ItemLocateError(Exception):
    def __init__(self, *args, **kwargs):
        default_message = "Item cannot be located because it is dark or does not exist."
        if args or kwargs:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(default_message)


class InvalidChecksumError(Exception):
    def __init__(self, *args, **kwargs):
        default_message = "File corrupt, checksums do not match."
        if args or kwargs:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(default_message)


class AccountAPIError(Exception):
    """Base exception for Account API-related errors."""
    def __init__(self, message: str, error_data: Optional[Dict] = None):
        super().__init__(message)
        self.error_data = error_data


class DirectoryTraversalError(Exception):
    """Raised when a computed local file path escapes the intended destination directory."""
