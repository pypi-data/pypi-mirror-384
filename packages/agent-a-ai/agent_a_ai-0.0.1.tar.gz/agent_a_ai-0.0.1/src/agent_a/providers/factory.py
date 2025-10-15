
# Copyright (C) 2025 The Agent A Open Source Project
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .gemini import GeminiProvider
from .claude import ClaudeProvider
from .base import BaseProvider

def get_router(router_name: str) -> BaseProvider:
    if router_name.lower() == 'gemini':
        return GeminiProvider()
    elif router_name.lower() == 'claude':
        return ClaudeProvider()
    else:
        raise ValueError(f"Unknown router: {router_name}")
