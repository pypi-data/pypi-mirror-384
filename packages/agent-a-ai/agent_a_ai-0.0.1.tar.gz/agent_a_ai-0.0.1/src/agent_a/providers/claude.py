
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

import os
import sys
import base64
from typing import List, Dict, Any, Generator, Optional

from anthropic import Anthropic

from .base import BaseProvider, FileObject
from  agent_a.utils import get_file_hash, discover_mimetype, update_status


class ClaudeProvider(BaseProvider):
    """
    Provider implementation for Anthropic's Claude API.
    Handles files by inlining them into the prompt:
    - Text-based files are wrapped in <document> tags.
    - Binary files (e.g., PDFs) are base64-encoded.
    This approach aligns with Anthropic's best practices for optimal model performance.
    """

    @property
    def name(self) -> str:
        return "claude"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Claude provider.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
            print("Please set the environment variable with your API key.", file=sys.stderr)
            sys.exit(1)
            
        try:
            self.client = Anthropic(api_key=api_key)
        except Exception as e:
            print(f"Failed to create Claude client: {e}", file=sys.stderr)
            sys.exit(1)

    def handle_file_upload(self, file_path: str, cache: dict) -> Optional[FileObject]:
        """
        Handles a file by reading its content if new or changed.
        Text files are read as-is for <document> tags, binary files are base64-encoded.
        Returns a FileObject and updates the cache.
        """
        if os.path.isdir(file_path):
            print(f" - Skipping directory: '{file_path}'")
            return None

        try:
            update_status(file_path, "checking cache")
            current_hash = get_file_hash(file_path)
            cached_entry = cache.get(file_path)

            if cached_entry and cached_entry.get('hash') == current_hash:
                # File hasn't changed, reconstruct FileObject from cache
                update_status(file_path, "Done (using cache)", is_final=True)
                return FileObject(
                    name=cached_entry.get('name'),
                    uri="",
                    mime_type=cached_entry.get('mime_type'),
                    expiration_time=None,
                    base64_content=cached_entry.get('base64_content'),
                    is_inline=True,
                    is_base64_encoded=cached_entry.get('is_base64_encoded')
                )

            if cached_entry:
                update_status(file_path, "changed, re-reading")
            else:
                update_status(file_path, "reading")
            
            mime_type = discover_mimetype(file_path)
            file_obj = self.upload_file(file_path=file_path, mime_type=mime_type)
            
            final_status = "Done (re-read)" if cached_entry else "Done (read)"
            update_status(file_path, final_status, is_final=True)

            # Update cache with new file info
            cache[file_path] = {
                'hash': current_hash,
                'name': file_obj.name,
                'mime_type': file_obj.mime_type,
                'is_base64_encoded': file_obj.is_base64_encoded,
                'base64_content': file_obj.base64_content
            }
            
            return file_obj
        except Exception as e:
            print(f"\nError handling file for '{file_path}': {e}", file=sys.stderr)
            return None

    def _is_binary_file(self, file_path: str, mime_type: Optional[str]) -> bool:
        """
        Determines if a file should be treated as binary (needs base64 encoding).

        Args:
            file_path: Path to the file
            mime_type: MIME type of the file

        Returns:
            True if file is binary (e.g., PDF), False if text
        """
        # PDF files must always be base64 encoded
        if mime_type and mime_type == 'application/pdf':
            return True

        # Check by extension as fallback
        _, ext = os.path.splitext(file_path)
        if ext.lower() == '.pdf':
            return True

        # All text-based mime types should not be base64 encoded
        if mime_type and (mime_type.startswith('text/') or
                         mime_type in ['application/json', 'application/xml', 'application/javascript']):
            return False

        return False

    def _encode_file_base64(self, file_path: str) -> str:
        """
        Encodes a binary file to base64 string.

        Args:
            file_path: Path to the file

        Returns:
            Base64 encoded string
        """
        try:
            with open(file_path, 'rb') as f:
                return base64.standard_b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding file '{file_path}' to base64: {e}", file=sys.stderr)
            raise

    def _read_text_file(self, file_path: str) -> str:
        """
        Reads a text file and returns its contents as a string.

        Args:
            file_path: Path to the file

        Returns:
            Text content of the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file '{file_path}': {e}", file=sys.stderr)
            raise

    def _format_files_as_documents(self, text_files: List[FileObject]) -> str:
        """
        Formats a list of text-based FileObjects into a single string with <document> tags.
        """
        if not text_files:
            return ""

        doc_strings = []
        for file_obj in text_files:
            # The file path is stored in 'name', and text content in 'base64_content'
            doc_strings.append(
                f"<document>\n"
                f"<source>{file_obj.name}</source>\n"
                f"<content>\n"
                f"{file_obj.base64_content}\n"
                f"</content>\n"
                f"</document>"
            )
        
        return "\n\n".join(doc_strings)


    def get_file(self, name: str) -> FileObject:
        file_obj = self.client.files.get(name=name)
        return FileObject(
            name=file_obj.name,
            uri=file_obj.uri,
            mime_type=file_obj.mime_type,
            expiration_time=file_obj.expiration_time,
            base64_content=None,
            is_inline=True,
            is_base64_encoded=False
        ) 


    def upload_file(self, file_path: str, mime_type: Optional[str] = None) -> FileObject:
        """
        Prepares a file for use with Claude.
        Text-based files are read as plain text for inline inclusion with <document> tags.
        Binary files (e.g., PDFs) are base64 encoded for inclusion as 'document' source objects.

        Args:
            file_path: Path to the file to upload
            mime_type: MIME type of the file

        Returns:
            FileObject with file metadata and content
        """
        is_binary = self._is_binary_file(file_path, mime_type)
        
        if is_binary:
            # Handle binary files: base64 encode them.
            try:
                content = self._encode_file_base64(file_path)
                return FileObject(
                    name=os.path.basename(file_path),
                    uri="",
                    mime_type=mime_type or "application/octet-stream",
                    expiration_time=None, # Inlined content doesn't expire
                    base64_content=content,
                    is_inline=True,
                    is_base64_encoded=True
                )
            except Exception as e:
                print(f"Error preparing binary file '{file_path}': {e}", file=sys.stderr)
                raise
        else:
            # Handle text files: read content as string.
            try:
                content = self._read_text_file(file_path)
                return FileObject(
                    name=file_path,  # Use full path for <source> tag
                    uri="",
                    mime_type=mime_type or "text/plain",
                    expiration_time=None,
                    base64_content=content, # Repurposed for plain text
                    is_inline=True,
                    is_base64_encoded=False
                )
            except Exception as e:
                print(f"Error preparing text file '{file_path}': {e}", file=sys.stderr)
                raise

    def _convert_conversation_to_claude_format(self, conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converts generic conversation format to Claude's message format.
        - Text files are formatted into <document> tags and prepended to the prompt.
        - Binary files are included as base64 'document' source objects.
        
        Args:
            conversation: List of message dicts with 'role' and 'parts'
        
        Returns:
            List of Claude-formatted messages
        """
        claude_messages = []
        
        for msg in conversation:
            role = msg.get('role', 'user')
            if role == 'model':
                role = 'assistant'
            
            parts = msg.get('parts', [])
            
            # Separate parts into text, text files, and binary files
            text_prompts = []
            text_files = []
            binary_files = []
            
            for part in parts:
                if isinstance(part, dict) and 'text' in part:
                    text_prompts.append(part['text'])
                elif isinstance(part, FileObject):
                    if part.is_base64_encoded:
                        binary_files.append(part)
                    else:
                        text_files.append(part)
            
            content_array = []

            # 1. Add binary files as 'document' source objects
            for file_obj in binary_files:
                content_array.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": file_obj.mime_type,
                        "data": file_obj.base64_content
                    }
                })

            # 2. Format text files into a single string
            documents_str = self._format_files_as_documents(text_files)
            
            # 3. Combine document string with user prompt text
            full_prompt_text = "\n".join(text_prompts)
            if documents_str:
                full_prompt_text = f"{documents_str}\n\n{full_prompt_text}".strip()

            if full_prompt_text:
                content_array.append({
                    "type": "text",
                    "text": full_prompt_text
                })
            
            if content_array:
                claude_messages.append({
                    "role": role,
                    "content": content_array
                })
        
        return claude_messages

    def generate_content_stream(self, model_name: str, conversation: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """
        Performs a streaming query with conversation history.
        Converts conversation to Claude's format and streams the response.
        
        Args:
            model_name: Claude model identifier
            conversation: List of message dicts
        
        Yields:
            Text chunks from the streaming response
        """
        try:
            # Convert conversation to Claude format
            claude_messages = self._convert_conversation_to_claude_format(conversation)
            
            if not claude_messages:
                yield "Error: No valid messages to send to Claude."
                return
            
            # Stream response from Claude
            with self.client.messages.stream(
                model=model_name,
                max_tokens=64000,
                messages=claude_messages
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            print(f"An error occurred during Claude streaming: {e}", file=sys.stderr)
            yield f"An error occurred during response generation: {e}"

    def generate_content(self, model_name: str, contents: List[Any]) -> Any:
        """
        Performs a non-streaming query. Used for coding mode.
        - Text files are formatted into <document> tags and prepended to the prompt.
        - Binary files are included as base64 'document' source objects.
        
        Args:
            model_name: Claude model identifier
            contents: List of content items (dicts with 'text' or FileObjects)
        
        Returns:
            Claude response object
        """
        try:
            # Separate parts into text, text files, and binary files
            text_prompts = []
            text_files = []
            binary_files = []

            for item in contents:
                if isinstance(item, dict) and 'text' in item:
                    text_prompts.append(item['text'])
                elif isinstance(item, FileObject):
                    if item.is_base64_encoded:
                        binary_files.append(item)
                    else:
                        text_files.append(item)

            content_array = []
            
            # 1. Add binary files
            for file_obj in binary_files:
                content_array.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": file_obj.mime_type,
                        "data": file_obj.base64_content
                    },
                    "cache_control": {"type": "ephemeral"}
                })

            # 2. Format text files
            documents_str = self._format_files_as_documents(text_files)

            # 3. Combine with prompt text
            full_prompt_text = "\n".join(text_prompts)
            if documents_str:
                full_prompt_text = f"{documents_str}\n\n{full_prompt_text}".strip()
            
            if full_prompt_text:
                content_array.append({
                    "type": "text",
                    "text": full_prompt_text
                })
            
            # Create message for Claude
            response = self.client.messages.create(
                model=model_name,
                max_tokens=64000,
                messages=[{
                    "role": "user",
                    "content": content_array
                }]
            )
            
            return response
            
        except Exception as e:
            print(f"An error occurred during Claude content generation: {e}", file=sys.stderr)
            raise

    def get_response_text(self, response: Any) -> str:
        """
        Extracts text from a Claude response object.
        
        Args:
            response: Claude response object
        
        Returns:
            Extracted text content
        """
        try:
            if hasattr(response, 'content') and response.content:
                # Claude's response.content is a list of content blocks
                text_parts = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        text_parts.append(block.text)
                return "\n".join(text_parts)
            return ""
        except Exception as e:
            print(f"Error extracting text from Claude response: {e}", file=sys.stderr)
            return ""
