
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

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FileObject:
    name: str
    uri: str
    mime_type: str
    expiration_time: Optional[datetime]
    base64_content: Optional[str] = None  # For inline files (Claude) - can be base64 or plain text
    is_inline: bool = False  # Flag to indicate inline vs. API
    is_base64_encoded: bool = False  # True if base64_content is actually base64 encoded

class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the provider."""
        pass

    @abstractmethod
    def handle_file_upload(self, file_path: str, cache: dict) -> Optional[FileObject]:
        """
        Handles file uploading and caching for the provider.
        Returns a FileObject or None if the path is a directory or on error.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file(self, name: str) -> FileObject:
        """
        Retrieves a file by its provider-specific name.
        """
       
        pass
    

    @abstractmethod
    def upload_file(self, file_path: str, mime_type: Optional[str] = None) -> FileObject:
        """Uploads a file and returns a provider-agnostic file object."""
        pass

    @abstractmethod
    def generate_content_stream(self, model_name: str, conversation: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """Performs a streaming query with a conversation history and yields text chunks."""
        pass

    @abstractmethod
    def generate_content(self, model_name: str, contents: List[Any]) -> Any:
        """Performs a non-streaming query and returns a provider-specific response object."""
        pass

    @abstractmethod
    def get_response_text(self, response: Any) -> str:
        """Extracts text from a non-streaming response object."""
        pass

    def generate_content_stream_batched(self, model_name: str,
                                          contents: List[Any]) -> str:
        """
        Performs a streaming query, collects all chunks, and returns a single
        concatenated string. This provides a unified way to get a complete
        response via the streaming pathway.
        """
        # The 'contents' format is used for single-turn, non-chat interactions,
        # so we wrap it in a minimal conversation structure.
        conversation = [{'role': 'user', 'parts': contents}]
        
        try:
            stream = self.generate_content_stream(model_name, conversation)
            return "".join(chunk for chunk in stream)
        except Exception:
            # Re-raise to allow the calling context (e.g., agent.py) to
            # handle it.
            raise
