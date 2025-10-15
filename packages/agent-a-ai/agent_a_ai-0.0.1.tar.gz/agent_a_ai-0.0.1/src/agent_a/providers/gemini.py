
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
from typing import List, Dict, Any, Generator, Optional
from datetime import datetime, timezone

from google import genai
from google.genai import types

import logging

from .base import BaseProvider, FileObject
from  agent_a.utils import get_file_hash, discover_mimetype, update_status

class GeminiProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "gemini"

    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set.", file=sys.stderr)
            print("Please set the environment variable with your API key.", file=sys.stderr)
            sys.exit(1)
            
        try:
            #logging.getLogger("google.genai").setLevel(logging.ERROR)
            logging.basicConfig(level=logging.ERROR)
            self.client = genai.Client(api_key=api_key)
            
        except Exception as e:
            print(f"Failed to create Gemini client: {e}", file=sys.stderr)
            sys.exit(1)

    def handle_file_upload(self, file_path: str, cache: dict) -> Optional[FileObject]:
        """
        Uploads a file if it's new, has changed, or has expired from cache.
        Uses provider's get_file to retrieve existing files if they are still valid.
        Returns the file object and updates the cache.
        """
        if os.path.isdir(file_path):
            print(f" - Skipping directory: '{file_path}'")
            return None

        try:
            update_status(file_path, "checking cache")
            current_hash = get_file_hash(file_path)
            cached_entry = cache.get(file_path)

            if cached_entry:
                cached_hash = cached_entry.get('hash')
                cached_file_name = cached_entry.get('name')
                cached_expiration_str = cached_entry.get('expiration_time')

                is_expired = False
                if cached_expiration_str:
                    try:
                        expiration_time = datetime.fromisoformat(cached_expiration_str)
                        if datetime.now(timezone.utc) >= expiration_time:
                            is_expired = True
                    except (ValueError, TypeError):
                        print(f"\nWarning: Could not parse expiration time for cached file '{file_path}'. Assuming expired.", file=sys.stderr)
                        is_expired = True

                if cached_hash == current_hash and not is_expired:
                    update_status(file_path, "verifying with server")
                    try:
                        file_obj = self.get_file(name=cached_file_name)
                        update_status(file_path, "Done (using cache)", is_final=True)
                        return file_obj
                    except Exception as e:
                        print(f"\nWarning: Could not retrieve cached file '{cached_file_name}' from server. Re-uploading. Error: {e}", file=sys.stderr)
                
                if is_expired:
                    update_status(file_path, "expired, re-uploading")
                elif cached_hash != current_hash:
                    update_status(file_path, "changed, re-uploading")
            else:
                update_status(file_path, "uploading")
            
            mime_type = discover_mimetype(file_path)
            uploaded_file = self.upload_file(file_path=file_path, mime_type=mime_type)
            
            final_status = "Done (reuploaded)" if cached_entry else "Done (uploaded)"
            update_status(file_path, final_status, is_final=True)

            cache[file_path] = {
                'hash': current_hash,
                'name': uploaded_file.name,
                'expiration_time': uploaded_file.expiration_time.isoformat() if uploaded_file.expiration_time else None,
            }
            return uploaded_file
        except Exception as e:
            print(f"\nError handling file upload for '{file_path}': {e}", file=sys.stderr)
            return None

    def _prepare_model_name(self, model_name: str) -> str:
        if not model_name.startswith("models/"):
            return f"models/{model_name}"
        return model_name

    def _convert_conversation_to_gemini_format(self, conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert FileObjects in conversation to Gemini's URI-based format.
        
        Args:
            conversation: List of message dicts with 'role' and 'parts'
        
        Returns:
            Conversation with FileObjects converted to Gemini Parts
        """
        gemini_conversation = []
        
        for msg in conversation:
            role = msg.get('role', 'user')
            parts = msg.get('parts', [])
            gemini_parts = []
            
            for part in parts:
                if isinstance(part, dict):
                    # Already in correct format (text dict or Gemini Part)
                    gemini_parts.append(part)
                elif isinstance(part, FileObject):
                    # Convert FileObject to Gemini Part
                    # Gemini only uses URI-based file references (no inline support)
                    gemini_parts.append(types.Part.from_uri(
                        file_uri=part.uri,
                        mime_type=part.mime_type
                    ))
            
            gemini_conversation.append({
                'role': role,
                'parts': gemini_parts
            })
        
        return gemini_conversation

    def _convert_contents_to_gemini_format(self, contents: List[Any]) -> List[Any]:
        """
        Convert FileObjects in contents list to Gemini Parts.
        
        Args:
            contents: List of content items (dicts or FileObjects)
        
        Returns:
            Contents with FileObjects converted to Gemini Parts
        """
        gemini_contents = []
        
        for item in contents:
            if isinstance(item, dict):
                # Already in correct format
                gemini_contents.append(item)
            elif isinstance(item, FileObject):
                # Convert FileObject to Gemini Part
                gemini_contents.append(types.Part.from_uri(
                    file_uri=item.uri,
                    mime_type=item.mime_type
                ))
        
        return gemini_contents

           
    def get_file(self, name: str) -> FileObject:
        file_obj = self.client.files.get(name=name)
        return FileObject(
            name=file_obj.name,
            uri=file_obj.uri,
            mime_type=file_obj.mime_type,
            expiration_time=file_obj.expiration_time,
            base64_content=None,
            is_inline=False,
            is_base64_encoded=False
        ) 

    def upload_file(self, file_path: str, mime_type: Optional[str] = None) -> FileObject:
        upload_config = None
        if mime_type:
            upload_config = types.UploadFileConfig(mime_type=mime_type)

        uploaded_file = self.client.files.upload(file=file_path, config=upload_config)
        return FileObject(
            name=uploaded_file.name,
            uri=uploaded_file.uri,
            mime_type=uploaded_file.mime_type,
            expiration_time=uploaded_file.expiration_time,
            base64_content=None,
            is_inline=False,
            is_base64_encoded=False
        )

    def generate_content_stream(self, model_name: str, conversation: List[Dict[str, Any]]) -> Generator[str, None, None]:
        try:
            model_to_use = self._prepare_model_name(model_name)
            
            # Convert FileObjects to Gemini format
            gemini_conversation = self._convert_conversation_to_gemini_format(conversation)
        
            response = self.client.models.generate_content_stream(
                model=model_to_use,
                contents=gemini_conversation
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"An error occurred during response generation: {e}", file=sys.stderr)
            yield "An error occurred during the response generation."

    def generate_content(self, model_name: str, contents: List[Any]) -> Any:
        model_to_use = self._prepare_model_name(model_name)
        
        # Convert FileObjects to Gemini format
        gemini_contents = self._convert_contents_to_gemini_format(contents)
        
        return self.client.models.generate_content(
            model=model_to_use,
            contents=gemini_contents,
        )

    def get_response_text(self, response: Any) -> str:
        return response.text
