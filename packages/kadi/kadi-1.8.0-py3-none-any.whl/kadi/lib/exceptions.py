# Copyright 2020 Karlsruhe Institute of Technology
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


class KadiException(Exception):
    """Base exception class."""


class KadiConfigurationError(KadiException):
    """For errors related to invalid configuration."""


class KadiStorageError(KadiException):
    """Base file storage error class."""


class KadiFilesizeExceededError(KadiStorageError):
    """For errors related to exceeded file size."""


class KadiFilesizeMismatchError(KadiStorageError):
    """For errors related to file size validation."""


class KadiChecksumMismatchError(KadiStorageError):
    """For errors related to file checksum validation."""


class KadiValidationError(KadiException):
    """For errors related to value format validation."""


class KadiPermissionError(KadiException):
    """For errors related to permissions."""


class KadiDatabaseError(KadiException):
    """Base database error class."""


class KadiDecryptionKeyError(KadiDatabaseError):
    """For errors related to an invalid database value decryption key."""
