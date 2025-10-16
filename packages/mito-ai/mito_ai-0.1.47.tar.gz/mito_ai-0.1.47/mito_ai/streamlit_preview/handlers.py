# Copyright (c) Saga Inc.
# Distributed under the terms of the GNU Affero General Public License v3.0 License.

import os
from typing import Literal, TypedDict
import uuid
from mito_ai.streamlit_preview.utils import ensure_app_exists, validate_request_body
import tornado
from jupyter_server.base.handlers import APIHandler
from mito_ai.streamlit_preview.manager import get_preview_manager
from mito_ai.path_utils import  AbsoluteNotebookPath, get_absolute_notebook_dir_path, get_absolute_notebook_path
from mito_ai.utils.telemetry_utils import log_streamlit_app_conversion_error, log_streamlit_app_preview_failure, log_streamlit_app_preview_success
from mito_ai.completions.models import MessageType
from mito_ai.utils.error_classes import StreamlitConversionError, StreamlitPreviewError
import traceback


class StreamlitPreviewHandler(APIHandler):
    """REST handler for streamlit preview operations."""

    def initialize(self) -> None:
        """Initialize the handler."""
        self.preview_manager = get_preview_manager()

    @tornado.web.authenticated
    async def post(self) -> None:
        """Start a new streamlit preview."""
        try:
            # Parse and validate request
            body = self.get_json_body()
            notebook_path, force_recreate, edit_prompt = validate_request_body(body)

            # Ensure app exists
            absolute_notebook_path = get_absolute_notebook_path(notebook_path)
            await ensure_app_exists(absolute_notebook_path, force_recreate, edit_prompt)

            # Start preview
            # TODO: There's a bug here where when the user rebuilds and already running app. Instead of 
            # creating a new process, we should update the existing process. The app displayed to the user 
            # does update, but that's just because of hot reloading when we overwrite the app.py file. 
            preview_id = str(uuid.uuid4())
            absolute_app_directory = get_absolute_notebook_dir_path(absolute_notebook_path)
            port = self.preview_manager.start_streamlit_preview(absolute_app_directory, preview_id)

            # Return success response
            self.finish({
                "type": 'success',
                "id": preview_id, 
                "port": port, 
                "url": f"http://localhost:{port}"
            })
            log_streamlit_app_preview_success('mito_server_key', MessageType.STREAMLIT_CONVERSION, edit_prompt)

        except StreamlitConversionError as e:
            print(e)
            self.set_status(e.error_code)
            error_message = str(e)
            formatted_traceback = traceback.format_exc()
            self.finish({"error": error_message})
            log_streamlit_app_conversion_error(
                'mito_server_key', 
                MessageType.STREAMLIT_CONVERSION, 
                error_message, 
                formatted_traceback,
                edit_prompt,
            )
        except StreamlitPreviewError as e:
            print(e)
            error_message = str(e)
            formatted_traceback = traceback.format_exc()
            self.set_status(e.error_code)
            self.finish({"error": error_message})
            log_streamlit_app_preview_failure('mito_server_key', MessageType.STREAMLIT_CONVERSION, error_message, formatted_traceback, edit_prompt)
        except Exception as e:
            print(f"Exception in streamlit preview handler: {e}")
            self.set_status(500)
            error_message = str(e)
            formatted_traceback = traceback.format_exc()
            self.finish({"error": error_message})
            log_streamlit_app_preview_failure('mito_server_key', MessageType.STREAMLIT_CONVERSION, error_message, formatted_traceback, "")

    @tornado.web.authenticated
    def delete(self, preview_id: str) -> None:
        """Stop a streamlit preview."""
        try:
            if not preview_id:
                self.set_status(400)
                self.finish({"error": "Missing preview_id parameter"})
                return

            # Stop the preview
            stopped = self.preview_manager.stop_preview(preview_id)

            if stopped:
                self.set_status(204)  # No content
            else:
                self.set_status(404)
                self.finish({"error": f"Preview {preview_id} not found"})

        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"Internal server error: {str(e)}"})
