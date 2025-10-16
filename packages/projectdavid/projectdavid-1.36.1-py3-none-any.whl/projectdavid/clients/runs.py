#!!Python
import json
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
import requests
from projectdavid_common import UtilsInterface, ValidationInterface
from projectdavid_common.validation import StatusEnum, TruncationStrategy
from pydantic import ValidationError
from sseclient import SSEClient

from projectdavid.clients.base_client import BaseAPIClient

ent_validator = ValidationInterface()
logging_utility = UtilsInterface.LoggingUtility()


class RunsClient(BaseAPIClient):
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        write_timeout: float = 30.0,
    ):
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
        )
        logging_utility.info("RunsClient ready at: %s", self.base_url)

    def create_run(
        self,
        assistant_id: str,
        thread_id: str,
        instructions: str = "",
        meta_data: Optional[Dict[str, Any]] = None,
        *,
        # new optional knobs; keep backwards compatible
        model: Optional[str] = None,
        response_format: str = "text",
        tool_choice: Optional[str] = None,  # allow None in signature, fix below
        temperature: float = 1.0,
        top_p: float = 1.0,
        # ↓ NEW: optional; only sent if provided
        truncation_strategy: Optional[ent_validator.TruncationStrategy] = None,
    ) -> ent_validator.Run:
        """
        Create a run. The server injects user_id from the API key.
        We normalize all timestamp fields to epoch ints (or None).
        """
        # ── Coerce client-friendly Nones into schema-acceptable values ─────────
        meta_data = meta_data or {}  # schema expects Dict
        tool_choice = tool_choice or "none"  # schema expects str
        model = model or "gpt-4"  # defer to schema default or override at callsite

        now = int(time.time())

        run_payload = ent_validator.RunCreate(
            id=UtilsInterface.IdentifierService.generate_run_id(),
            user_id=None,  # server fills this
            assistant_id=assistant_id,
            thread_id=thread_id,
            instructions=instructions,
            meta_data=meta_data,
            cancelled_at=None,
            completed_at=None,
            created_at=now,
            expires_at=now + 3600,
            failed_at=None,
            incomplete_details=None,
            last_error=None,
            max_completion_tokens=1000,
            max_prompt_tokens=500,
            model=model,
            object="run",
            parallel_tool_calls=False,
            required_action=None,
            response_format=response_format,
            started_at=None,
            status=ent_validator.RunStatus.pending,
            tool_choice=tool_choice,
            tools=[],
            usage=None,
            temperature=temperature,
            top_p=top_p,
            tool_resources={},
            # Directly pass the truncation_strategy. It will be None if not provided.
            truncation_strategy=truncation_strategy,
        )

        logging_utility.info(
            "Creating run for assistant_id=%s, thread_id=%s", assistant_id, thread_id
        )
        logging_utility.debug("Run payload: %s", run_payload.model_dump())

        try:
            # Build dict from the Pydantic model. `exclude_none=True` will
            # automatically omit `truncation_strategy` if it is None, allowing
            # the server-side database default to apply.
            payload_dict = run_payload.model_dump(exclude_none=True)

            resp = self.client.post("/v1/runs", json=payload_dict)
            resp.raise_for_status()
            run_out = ent_validator.Run(**resp.json())
            logging_utility.info("Run created successfully: %s", run_out.id)
            return run_out

        except ValidationError as e:
            logging_utility.error("Validation error: %s", e.json())
            raise ValueError(f"Validation error: {e}") from e
        except httpx.HTTPStatusError as e:
            logging_utility.error("HTTP error during run creation: %s", str(e))
            raise
        except Exception as e:
            logging_utility.error("Unexpected error during run creation: %s", str(e))
            raise

    def retrieve_run(self, run_id: str) -> ent_validator.RunReadDetailed:
        """
        Retrieve a run by its ID and return it as a RunReadDetailed Pydantic model.

        Args:
            run_id (str): The run ID.

        Returns:
            RunReadDetailed: The retrieved run details.
        """
        logging_utility.info("Retrieving run with id: %s", run_id)
        try:
            response = self.client.get(f"/v1/runs/{run_id}")
            response.raise_for_status()
            run_data = response.json()
            validated_run = ent_validator.RunReadDetailed(**run_data)
            logging_utility.info(
                "Run with id %s retrieved and validated successfully", run_id
            )
            return validated_run

        except ValidationError as e:
            logging_utility.error("Validation error: %s", e.json())
            raise ValueError(f"Data validation failed: {e}")
        except httpx.HTTPStatusError as e:
            logging_utility.error(
                "HTTP error occurred while retrieving run: %s", str(e)
            )
            raise
        except Exception as e:
            logging_utility.error(
                "An unexpected error occurred while retrieving run: %s", str(e)
            )
            raise

    def update_run_status(self, run_id: str, new_status: str) -> ent_validator.Run:
        """
        Update the status of a run.

        Args:
            run_id (str): The run ID.
            new_status (str): The new status to set.

        Returns:
            Run: The updated run.
        """
        logging_utility.info(
            "Updating run status for run_id: %s to %s", run_id, new_status
        )
        update_data = {"status": new_status}

        try:
            validated_data = ent_validator.RunStatusUpdate(**update_data)
            response = self.client.put(
                f"/v1/runs/{run_id}/status", json=validated_data.dict()
            )
            response.raise_for_status()

            updated_run = response.json()
            validated_run = ent_validator.Run(**updated_run)
            logging_utility.info("Run status updated successfully")
            return validated_run

        except ValidationError as e:
            logging_utility.error("Validation error: %s", e.json())
            raise ValueError(f"Validation error: {e}")
        except httpx.HTTPStatusError as e:
            logging_utility.error(
                "HTTP error occurred while updating run status: %s", str(e)
            )
            raise
        except Exception as e:
            logging_utility.error(
                "An error occurred while updating run status: %s", str(e)
            )
            raise

    def delete_run(self, run_id: str) -> Dict[str, Any]:
        """
        Delete a run by its ID.

        Args:
            run_id (str): The run ID.

        Returns:
            Dict[str, Any]: The deletion result.
        """
        logging_utility.info("Deleting run with id: %s", run_id)
        try:
            response = self.client.delete(f"/v1/runs/{run_id}")
            response.raise_for_status()
            result = response.json()
            logging_utility.info("Run deleted successfully")
            return result
        except httpx.HTTPStatusError as e:
            logging_utility.error("HTTP error occurred while deleting run: %s", str(e))
            raise
        except Exception as e:
            logging_utility.error("An error occurred while deleting run: %s", str(e))
            raise

    def generate(
        self, run_id: str, model: str, prompt: str, stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate content for a run based on the provided model and prompt.

        Args:
            run_id (str): The run ID.
            model (str): The model to use.
            prompt (str): The prompt text.
            stream (bool): Whether to stream the response.

        Returns:
            Dict[str, Any]: The generated content.
        """
        logging_utility.info(
            "Generating content for run_id: %s, model: %s", run_id, model
        )
        try:
            run = self.retrieve_run(run_id)
            response = self.client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "context": run.meta_data.get("context", []),
                    "temperature": run.temperature,
                    "top_p": run.top_p,
                },
            )
            response.raise_for_status()
            result = response.json()
            logging_utility.info("Content generated successfully")
            return result
        except httpx.HTTPStatusError as e:
            logging_utility.error(
                "HTTP error occurred while generating content: %s", str(e)
            )
            raise
        except Exception as e:
            logging_utility.error(
                "An error occurred while generating content: %s", str(e)
            )
            raise

    def chat(
        self,
        run_id: str,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Chat using a run, model, and provided messages.

        Args:
            run_id (str): The run ID.
            model (str): The model to use.
            messages (List[Dict[str, Any]]): The messages for context.
            stream (bool): Whether to stream the response.

        Returns:
            Dict[str, Any]: The chat response.
        """
        logging_utility.info("Chatting for run_id: %s, model: %s", run_id, model)
        try:
            run = self.retrieve_run(run_id)
            response = self.client.post(
                "/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "context": run.meta_data.get("context", []),
                    "temperature": run.temperature,
                    "top_p": run.top_p,
                },
            )
            response.raise_for_status()
            result = response.json()
            logging_utility.info("Chat completed successfully")
            return result
        except httpx.HTTPStatusError as e:
            logging_utility.error("HTTP error occurred during chat: %s", str(e))
            raise
        except Exception as e:
            logging_utility.error("An error occurred during chat: %s", str(e))
            raise

    def cancel_run(self, run_id: str) -> Dict[str, Any]:
        """
        Cancel a run by its ID.

        Args:
            run_id (str): The run ID.

        Returns:
            Dict[str, Any]: The cancellation result.
        """
        logging_utility.info("Cancelling run with id: %s", run_id)
        try:
            response = self.client.post(f"/v1/runs/{run_id}/cancel")
            response.raise_for_status()
            result = response.json()
            logging_utility.info("Run %s cancelled successfully", run_id)
            return result
        except httpx.HTTPStatusError as e:
            logging_utility.error(
                "HTTP error occurred while cancelling run %s: %s", run_id, str(e)
            )
            raise
        except Exception as e:
            logging_utility.error(
                "An error occurred while cancelling run %s: %s", run_id, str(e)
            )
            raise

    # --- NEW POLLING AND EXECUTION HELPER METHOD ---
    def poll_and_execute_action(
        self,
        run_id: str,
        thread_id: str,  # Needed for submit_tool_output
        assistant_id: str,  # Needed for submit_tool_output
        # *** Accept the consumer's handler function ***
        tool_executor: Callable[[str, Dict[str, Any]], str],
        # *** Accept SDK sub-clients or main client ***
        actions_client: Any,  # Instance of ActionsClient
        messages_client: Any,  # Instance of MessagesClient
        timeout: float = 60.0,
        interval: float = 1.0,
    ) -> bool:
        """
        Polls for a required action, executes it using the provided executor,
        submits the result, and updates run status. This is a BLOCKING call.

        Args:
            run_id (str): The ID of the run to monitor and handle.
            thread_id (str): The ID of the thread the run belongs to.
            assistant_id (str): The ID of the assistant for the run.
            tool_executor (Callable): A function provided by the consumer that takes
                                      (tool_name: str, arguments: dict) and returns
                                      a string result.
            actions_client (Any): An initialized instance of the ActionsClient.
            messages_client (Any): An initialized instance of the MessagesClient.
            timeout (float): Maximum time to wait for an action in seconds.
            interval (float): Time between polling attempts in seconds.

        Returns:
            bool: True if an action was successfully found, executed, and submitted.
                  False if timeout occurred, the run reached a terminal state first,
                  or an error prevented successful handling.
        """
        if timeout <= 0 or interval <= 0:
            raise ValueError("Timeout and interval must be positive numbers.")
        if not callable(tool_executor):
            raise TypeError("tool_executor must be a callable function.")

        start_time = time.time()
        action_handled_successfully = False
        logging_utility.info(
            f"[SDK Helper] Waiting for action on run {run_id} (timeout: {timeout}s)..."
        )

        # Define terminal states using the exact string values from your StatusEnum
        terminal_states = {
            StatusEnum.completed.value,
            StatusEnum.failed.value,
            StatusEnum.cancelled.value,
            StatusEnum.expired.value,
        }
        transient_states = {
            StatusEnum.queued.value,
            StatusEnum.in_progress.value,
            StatusEnum.processing.value,
            StatusEnum.cancelling.value,
            StatusEnum.pending.value,
            StatusEnum.retrying.value,
        }
        target_state = StatusEnum.pending_action.value

        while (time.time() - start_time) < timeout:
            action_to_handle = None
            current_status_str = None

            # --- Check Run Status First ---
            try:
                current_run = self.retrieve_run(run_id)  # Use self.retrieve_run
                if isinstance(current_run.status, Enum):
                    current_status_str = current_run.status.value
                else:
                    current_status_str = str(current_run.status)

                logging_utility.debug(
                    f"[SDK Helper] Polling run {run_id}: Status='{current_status_str}'"
                )

                if current_status_str == target_state:
                    # Action required, now get action details
                    logging_utility.info(
                        f"[SDK Helper] Run {run_id} requires action. Fetching details..."
                    )
                    try:
                        # Use the passed-in actions_client
                        pending_actions = actions_client.get_pending_actions(
                            run_id=run_id
                        )
                        if pending_actions:
                            action_to_handle = pending_actions[0]
                        else:
                            logging_utility.warning(
                                f"[SDK Helper] Run {run_id} is '{target_state}' but no pending actions found via API."
                            )
                            # Maybe the status changed again quickly? Loop will re-check status.
                    except Exception as e:
                        logging_utility.error(
                            f"[SDK Helper] Error fetching pending actions for run {run_id}: {e}",
                            exc_info=True,
                        )
                        # Consider stopping if we can't get action details
                        return False  # Stop if error getting action details
                elif current_status_str in terminal_states:
                    logging_utility.info(
                        f"[SDK Helper] Run {run_id} reached terminal state '{current_status_str}'. Stopping wait."
                    )
                    return False  # Stop if run finished/failed
                elif current_status_str not in transient_states:
                    logging_utility.warning(
                        f"[SDK Helper] Run {run_id} in unexpected state '{current_status_str}'. Stopping wait."
                    )
                    return False  # Stop on unexpected states

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise  # Re-raise 404 immediately
                logging_utility.error(
                    f"[SDK Helper] HTTP error {e.response.status_code} retrieving run {run_id} status: {e.response.text}. Stopping wait."
                )
                return False  # Stop on other HTTP errors
            except Exception as e:
                logging_utility.error(
                    f"[SDK Helper] Error retrieving run {run_id} status: {e}",
                    exc_info=True,
                )
                return False  # Stop on other errors retrieving status

            # --- Process Action if Found ---
            if action_to_handle:
                action_id = action_to_handle.get("action_id")
                tool_name = action_to_handle.get("tool_name")
                arguments = action_to_handle.get("function_arguments")

                if not action_id or not tool_name:
                    logging_utility.error(
                        f"[SDK Helper] Invalid action data found for run {run_id}: {action_to_handle}"
                    )
                    # Continue loop to re-fetch status/actions? Or fail? Let's fail for now.
                    return False

                logging_utility.info(
                    f"[SDK Helper] Processing action {action_id} (Tool: '{tool_name}') for run {run_id}..."
                )
                try:
                    # --- Call Consumer's Executor ---
                    logging_utility.debug(
                        f"[SDK Helper] Calling provided tool_executor for '{tool_name}'..."
                    )
                    tool_result_content = tool_executor(tool_name, arguments)
                    if not isinstance(tool_result_content, str):
                        logging_utility.warning(
                            f"[SDK Helper] tool_executor for '{tool_name}' did not return a string. Attempting json.dumps."
                        )
                        try:
                            tool_result_content = json.dumps(tool_result_content)
                        except Exception:
                            logging_utility.error(
                                f"[SDK Helper] Failed to convert tool_executor result to JSON string."
                            )
                            raise TypeError(
                                "Tool executor must return a string or JSON-serializable object."
                            )
                    logging_utility.info(
                        f"[SDK Helper] tool_executor for '{tool_name}' completed."
                    )
                    # --- End Consumer's Executor ---

                    # --- Submit Tool Output ---
                    logging_utility.debug(
                        f"[SDK Helper] Submitting output for action {action_id}..."
                    )
                    # Use the passed-in messages_client
                    messages_client.submit_tool_output(
                        thread_id=thread_id,
                        tool_id=action_id,
                        content=tool_result_content,
                        role="tool",
                        assistant_id=assistant_id,
                    )
                    logging_utility.info(
                        f"[SDK Helper] Output submitted successfully for action {action_id}."
                    )
                    # --- End Submit ---

                    # --- Optional: Update Run Status ---
                    # Backend might do this automatically, but updating here ensures client knows
                    # try:
                    #      self.update_run_status(run_id=run_id, new_status=StatusEnum.processing.value)
                    #      logging_utility.info(f"[SDK Helper] Run {run_id} status updated to '{StatusEnum.processing.value}'.")
                    # except Exception as e:
                    #      logging_utility.warning(f"[SDK Helper] Failed to update run status after submitting output for {action_id}: {e}")
                    # --- End Optional Status Update ---

                    action_handled_successfully = True
                    break  # Exit the while loop successfully

                except Exception as e:
                    logging_utility.error(
                        f"[SDK Helper] Error during execution or submission for action {action_id} (Run {run_id}): {e}",
                        exc_info=True,
                    )
                    # Should we update action/run to failed? Depends on API design.
                    # For now, just break the loop and return False.
                    action_handled_successfully = False
                    break

            # If no action to handle yet and not in terminal/error state, sleep.
            if not action_to_handle:
                time.sleep(interval)
        # --- End While Loop ---

        if not action_handled_successfully and (time.time() - start_time) >= timeout:
            logging_utility.warning(
                f"[SDK Helper] Timeout reached waiting for action on run {run_id}."
            )
        elif not action_handled_successfully:
            logging_utility.info(
                f"[SDK Helper] Exited wait loop for run {run_id} without handling action (likely due to error or terminal state reached)."
            )

        return action_handled_successfully

    def watch_run_events(
        self,
        run_id: str,
        tool_executor: Callable[[str, dict], str],
        actions_client: Any,
        messages_client: Any,
        assistant_id: str,
        thread_id: str,
    ) -> None:
        """
        Opens an SSE connection to /v1/runs/{run_id}/events, waits for
        'action_required', runs the executor, and submits the result.
        Blocks until the action is handled.

        Requires 'sseclient': pip install sseclient-py
        """

        url = f"{self.base_url}/v1/runs/{run_id}/events"
        headers = self.client.headers

        def _listen_and_handle():
            resp = requests.get(url, headers=headers, stream=True)
            resp.raise_for_status()

            # Wrap the line‑iterator in SSEClient
            client = SSEClient(resp.iter_lines())

            # Iterate over the parsed events
            for event in client.events():
                if event.event == "action_required":
                    action = json.loads(event.data)
                    tool_name = action.get("tool_name")
                    args = action.get("function_arguments", {})

                    # execute
                    result = tool_executor(tool_name, args)
                    if not isinstance(result, str):
                        result = json.dumps(result)

                    # submit
                    messages_client.submit_tool_output(
                        thread_id=thread_id,
                        tool_id=action.get("action_id"),
                        content=result,
                        role="tool",
                        assistant_id=assistant_id,
                    )
                    break

        t = threading.Thread(target=_listen_and_handle, daemon=True)
        t.start()
        t.join()

    # ------------------------------------------------------------
    # List all runs by thread_id
    # ------------------------------------------------------------
    def list_runs(
        self, thread_id: str, limit: int = 20, order: str = "asc"
    ) -> ent_validator.RunListResponse:
        params = {"limit": limit, "order": order if order in ("asc", "desc") else "asc"}
        resp = self.client.get(f"/v1/threads/{thread_id}/runs", params=params)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and "data" in payload:
            return ent_validator.RunListResponse(**payload)
        runs = [ent_validator.Run(**item) for item in payload]
        return ent_validator.RunListResponse(
            object="list",
            data=runs,
            first_id=runs[0].id if runs else None,
            last_id=runs[-1].id if runs else None,
            has_more=False,
        )

    # ------------------------------------------------------------
    # List all runs by user
    # ------------------------------------------------------------
    def list_all_runs(
        self, limit: int = 20, order: str = "asc"
    ) -> ent_validator.RunListResponse:
        params = {"limit": limit, "order": order if order in ("asc", "desc") else "asc"}
        resp = self.client.get("/v1/runs", params=params)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and "data" in payload:
            return ent_validator.RunListResponse(**payload)
        # legacy fallback: wrap raw list
        runs = [ent_validator.Run(**item) for item in payload]
        return ent_validator.RunListResponse(
            object="list",
            data=runs,
            first_id=runs[0].id if runs else None,
            last_id=runs[-1].id if runs else None,
            has_more=False,
        )
