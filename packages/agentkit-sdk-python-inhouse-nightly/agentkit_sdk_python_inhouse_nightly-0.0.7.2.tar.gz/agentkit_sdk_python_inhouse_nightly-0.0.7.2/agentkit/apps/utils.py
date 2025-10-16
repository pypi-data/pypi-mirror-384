# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
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

import json
import logging

logger = logging.getLogger("agentkit." + __name__)


def safe_serialize_to_json_string(obj):
    """Safely serialize object directly to JSON string with progressive fallback handling.

    This method eliminates double JSON encoding by returning the JSON string directly,
    avoiding the test-then-encode pattern that leads to redundant json.dumps() calls.
    Used by both streaming and non-streaming responses for consistent behavior.

    Returns:
        str: JSON string representation of the object
    """
    try:
        # First attempt: direct JSON serialization with Unicode support
        return json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError, UnicodeEncodeError):
        try:
            # Second attempt: convert to string, then JSON encode the string
            return json.dumps(str(obj), ensure_ascii=False)
        except Exception as e:
            # Final fallback: JSON encode error object with ASCII fallback for problematic Unicode
            logger.warning("Failed to serialize object: %s: %s", type(e).__name__, e)
            error_obj = {
                "error": "Serialization failed",
                "original_type": type(obj).__name__,
            }
            return json.dumps(error_obj, ensure_ascii=False)
