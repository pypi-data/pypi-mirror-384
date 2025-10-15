import datetime
import json
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, TypedDict

from fastapi import FastAPI


class FileResponse(TypedDict):
    file_id: str  # UUID
    file_path: str  # file:// path in most cases
    file_ref: str
    file_hash: str
    file_size_raw: int
    mime_type: str
    created_at: str  # ISO string
    embedded: bool  # Usually false for the agent server at the moment
    file_path_expiration: str | None  # ISO string or None
    agent_id: str  # UUID
    thread_id: str  # UUID
    user_id: str  # UUID
    file_url: str  # same as file_path in most cases
    work_item_id: str | None  # UUID or None


class FastAPIAgentDummyServer:
    """FastAPI-based dummy server for testing agent server clients using MemoryTransport.

    Similar to AgentDummyServer but uses FastAPI instead of HTTPHandler.
    Allows injection of responses for testing purposes.
    """

    def __init__(
        self,
        responses: list[str | dict] | None = None,
        file_responses: dict[str, FileResponse] | None = None,
    ):
        """
        Initialize the dummy server with a queue of responses.

        Args:
            responses: List of responses to return in order. Each request
                      will pop the next response from this list. Responses should be
                      either strings or can otherwise be serialized to JSON.
            file_responses: Dict mapping file names/refs to custom file response data.
                          Keys can be file names or file refs, values are dicts with
                          file response fields to override defaults. The fields should
                          match those used by the agent server:
                            - file_id: a UUID string
                            - file_path: a file:// URL
                            - file_ref: a string
                            - file_hash: a string
                            - file_size_raw: an integer
                            - mime_type: a string
                            - created_at: a datetime string
                            - embedded: a boolean
                            - file_path_expiration: a datetime string or None
                            - agent_id: a string or None
                            - thread_id: a string or None
                            - user_id: a string or None
                            - file_url: a file:// URL
                            - work_item_id: a string or None
        """
        self.app = FastAPI()
        self.responses = responses or []
        self.file_responses = file_responses or {}
        self.last_request = None
        self.server = None
        self.thread = None
        self.port = None
        self._setup_routes()

    def _setup_routes(self):
        """Set up the FastAPI routes."""
        from fastapi import Query
        from fastapi.responses import JSONResponse

        @self.app.get("/ok")
        async def health_check():
            """Health check endpoint for URL accessibility."""
            return JSONResponse({"ok": True})

        @self.app.post("/prompts/generate")
        async def prompts_generate(
            payload: dict[str, Any],
            thread_id: str | None = Query(None),
            agent_id: str | None = Query(None),
        ):
            """Generate a prompt response."""
            # Store the request for testing
            self.last_request = {
                "body": payload,
                "thread_id": thread_id,
                "agent_id": agent_id,
                "path": f"/api/v2/prompts/generate?thread_id={thread_id}&agent_id={agent_id}",
            }

            # Get response from queue
            if self.responses:
                user_response = self.responses.pop(0)
            else:
                user_response = "Request processed successfully."

            # Return the expected response format
            response = {
                "content": [
                    {
                        "kind": "text",
                        "text": user_response
                        if isinstance(user_response, str)
                        else json.dumps(user_response),
                    }
                ],
                "role": "agent",
                "raw_response": None,
                "stop_reason": None,
                "usage": {
                    "input_tokens": 115,
                    "output_tokens": len(str(user_response).split()),
                    "total_tokens": 115 + len(str(user_response).split()),
                },
                "metrics": {},
                "metadata": {},
                "additional_response_fields": {},
            }

            return JSONResponse(response)

        @self.app.get("/threads/{thread_id}/file-by-ref")
        async def get_file_by_ref(
            thread_id: str,
            file_ref: str = Query(...),
            agent_id: str | None = Query(None),
        ):
            """Get a file by reference (for testing purposes, returns a temporary file)."""
            # Check if custom file response is provided for this file_ref
            if file_ref in self.file_responses:
                custom_response = self.file_responses[file_ref]

                # Start with default response and override with custom values
                file_response = self._generate_default_file_response(file_ref, agent_id, thread_id)

                # Allow overriding any response fields
                file_response.update({k: v for k, v in custom_response.items()})

                return JSONResponse(file_response)

            # Default behavior
            file_response = self._generate_default_file_response(file_ref, agent_id, thread_id)
            return JSONResponse(file_response)

    def _generate_default_file_response(
        self, file_ref: str, agent_id: str, thread_id: str
    ) -> dict[str, Any]:
        """Generate a default file response for when a file parameter is not provided."""
        # Create a temporary file for testing
        temp_dir = tempfile.gettempdir()
        file_path = Path(temp_dir) / file_ref
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write some test content
        file_path.write_text(f"Test content for {file_ref}")

        return FileResponse(
            file_id=str(uuid.uuid4()),
            file_path=f"file://{file_path!s}",
            file_ref=file_ref,
            file_hash="test-hash",
            file_size_raw=file_path.stat().st_size,
            mime_type="application/pdf",
            created_at=datetime.datetime.now(datetime.UTC).isoformat(),
            embedded=False,
            file_path_expiration=None,
            agent_id=agent_id,
            thread_id=thread_id,
            user_id="test-user-id",
            file_url=f"file://{file_path!s}",
            work_item_id=None,
        )

    def _run_server(self):
        """Run the server in a thread."""
        try:
            import uvicorn
        except ImportError as e:
            raise ImportError(
                "uvicorn is required to run FastAPIAgentDummyServer. "
                "Install with: pip install uvicorn"
            ) from e

        # Use port 0 to let the OS assign a free port
        config = uvicorn.Config(
            self.app,
            host="localhost",
            port=0,
            log_level="error",  # Quiet the logs during tests
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def start(self):
        """Start the server in a background thread."""
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

        # Wait for the server to start and get the actual port
        time.sleep(0.5)
        if self.server and hasattr(self.server, "servers"):
            for server in self.server.servers:
                if hasattr(server, "sockets"):
                    for socket in server.sockets:
                        self.port = socket.getsockname()[1]
                        break
                    break

    def get_port(self):
        """Get the port the server is running on."""
        return self.port

    def get_app(self):
        """Get the FastAPI app instance for direct testing."""
        return self.app

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=1)
