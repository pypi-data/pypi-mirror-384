# backend/gradio_livelog/utils.py

from functools import wraps
import io
import threading
import logging
import queue
import re
import sys
import time
import inspect
import uuid
import gradio as gr
from contextlib import contextmanager
from typing import Callable, List, Iterator, Dict, Any, Literal, Optional, Union

# Place this code in a utility file, e.g., gradio_livelog/utils.py

class _QueueLogHandler(logging.Handler):
    """A private logging handler that directs log records into a queue."""
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        self.log_queue.put(record)

@contextmanager
def capture_logs(
    log_name: Union[str, List[str], None] = None, 
    log_level: int = logging.INFO,
    disable_console: bool = False
) -> Iterator[Callable[[], List[logging.LogRecord]]]:
    """
    A context manager to capture logs from one or more specified loggers.

    This function temporarily attaches a thread-safe, queue-based handler to the
    target logger(s) to intercept all log messages. If `disable_console` is True,
    it will also temporarily remove other console-based StreamHandlers from the
    target loggers to prevent duplicate output to the terminal.

    Args:
        log_name: The name of the logger(s) to capture.
                - `str`: Captures logs from a single named logger.
                - `List[str]`: Captures logs from multiple named loggers.
                - `None` or `""`: Captures logs from the root logger.
        log_level: The minimum level of logs to capture (e.g., `logging.INFO`).
        disable_console: If True, prevents the captured logs from also being
                        printed to the console by other handlers on the same logger.

    Yields:
        A callable function. When this function is called, it returns a list
        of all log records captured since the last time it was called, effectively
        acting as a "get new logs" utility.
        
    Example:
        >>> with capture_logs(log_name=["my_app", "my_library"]) as get_logs:
        ...     logging.getLogger("my_app").info("Starting process.")
        ...     new_logs = get_logs()  # Contains the first log record
        ...     logging.getLogger("my_library").warning("A potential issue.")
        ...     more_logs = get_logs() # Contains only the warning record
    """
    # Step 1: Determine the target loggers based on the `log_name` argument.
    target_loggers: List[logging.Logger] = []
    log_names_to_process = []
    if log_name is None or log_name == "":
        log_names_to_process.append(None) # `None` is the identifier for the root logger
    elif isinstance(log_name, list):
        log_names_to_process.extend(log_name)
    elif isinstance(log_name, str):
        log_names_to_process.append(log_name)
    
    # Get the actual logger objects from their names.
    for name in set(log_names_to_process): # Use set to avoid duplicates
        target_loggers.append(logging.getLogger(name))

    # Step 2: Set up the thread-safe queue and the custom handler.
    log_queue = queue.Queue()
    queue_handler = _QueueLogHandler(log_queue)

    # Step 3: Store the original state of each logger to restore it later.
    original_levels = {logger.name: logger.level for logger in target_loggers}
    original_handlers = {logger.name: logger.handlers[:] for logger in target_loggers}
    
    # Step 4: Modify the target loggers for the duration of the context.
    for logger in target_loggers:
        # Set the desired capture level.
        logger.setLevel(log_level)

        if disable_console:
            # If disabling console, remove all existing StreamHandlers.
            # We keep other handlers (e.g., FileHandler) intact.
            logger.handlers = [
                h for h in logger.handlers if not isinstance(h, logging.StreamHandler)
            ]
        
        # Add our custom queue handler to start capturing logs.
        logger.addHandler(queue_handler)

    # This holds all records captured during the context's lifetime.
    all_captured: List[logging.LogRecord] = [] 
    # This index tracks the last record that was returned to the caller.
    last_returned_index = 0 

    try:
        def get_captured_records() -> List[logging.LogRecord]:
            """
            Retrieves new log records from the queue and returns them.
            This function is what the context manager yields to the user.
            """
            nonlocal last_returned_index
            
            # Drain the queue into our master list of captured records.
            while not log_queue.empty():
                try:
                    record = log_queue.get_nowait()
                    all_captured.append(record)
                except queue.Empty:
                    # This handles a rare race condition where the queue becomes empty
                    # between the `empty()` check and `get_nowait()`.
                    break 
            
            # Slice the master list to get only the new records.
            new_records = all_captured[last_returned_index:]
            # Update the index to the end of the list for the next call.
            last_returned_index = len(all_captured)
            
            return new_records

        # Yield the function to the `with` block.
        yield get_captured_records

    finally:
        # Step 5: Restore the loggers to their original state, ensuring no side effects.
        for logger in target_loggers:
            # Remove our custom handler.
            logger.removeHandler(queue_handler)
            
            # Restore the original log level.
            if logger.name in original_levels:
                logger.setLevel(original_levels[logger.name])
            
            # If we disabled the console, restore the original handlers.
            if disable_console and logger.name in original_handlers:
                # It's safest to clear handlers and then re-add the originals.
                logger.handlers = []
                for handler in original_handlers[logger.name]:
                    logger.addHandler(handler)
                    
class Tee(io.StringIO):
    """
    A file-like object that acts like the Unix 'tee' command.
    It writes to multiple file-like objects simultaneously.
    """
    def __init__(self, *files):
        """
        Initializes the Tee object.
        Args:
            *files: A variable number of file-like objects (e.g., sys.stderr,
                    a TqdmToQueueWriter instance, etc.).
        """
        super().__init__()
        self.files = files

    def write(self, s: str) -> int:
        """
        Writes the string 's' to all managed files.
        """
        for f in self.files:
            f.write(s)
            # Some file-like objects, like the console, might need to be flushed.
            if hasattr(f, 'flush'):
                f.flush()
        return len(s)

    def flush(self):
        """Flushes all managed files."""
        for f in self.files:
            if hasattr(f, 'flush'):
                f.flush()
                
class TqdmToQueueWriter(io.StringIO):
    """
    A custom, thread-safe, file-like object that intercepts tqdm's output.

    This class is designed to be passed to a `tqdm` instance (or a library
    that uses `tqdm`, like `diffusers`) via its `file` argument. It uses a
    regular expression to parse the formatted progress string in real-time.

    It extracts key metrics:
    - The iteration rate value (e.g., 2.73).
    - The rate unit ("it/s" or "s/it").
    - Any additional status information that follows the rate.

    The extracted data is packaged into a dictionary and put onto a
    `queue.Queue`, allowing a consumer thread (like a Gradio UI thread)
    to receive real-time progress data from a worker thread.
    """
    def __init__(self, rate_queue: queue.Queue):
        """
        Initializes the writer with a queue for communication.

        Args:
            rate_queue (queue.Queue): The thread-safe queue to which the
                                      extracted rate data will be sent.
        """
        super().__init__()
        self.rate_queue = rate_queue
                
        # This regex is designed to be robust. It finds the core stats
        # and captures everything after as the "extra text".
        self.tqdm_regex = re.compile(
            # Optional time block like [00:55<00:03,
            r"(?:\[\s*(\d{2}:\d{2})<(\d{2}:\d{2})\s*,)?"
            # Rate and unit (e.g., 1.96s/it)
            r"\s*(\d+\.?\d*)\s*(it/s|s/it)"
            # Optional comma and the rest of the line (non-greedy)
            r"(?:,\s*(.*?))?\s*\]"
        )

    def write(self, s: str) -> int:
        """
        This method is called by `tqdm` whenever it updates the progress bar.
        It receives the full, formatted progress string.

        Args:
            s (str): The string output from `tqdm` (e.g., "75%|...| 2.73it/s, ...").

        Returns:
            int: The number of characters written, as required by the file-like
                 object interface.
        """
        try:
            match = self.tqdm_regex.search(s)
            if not match:
                return len(s)

            rate_info = {}
            # Groups are shifted because of the optional time block
            g = match.groups()
            
            # g[0] is elapsed, g[1] is ETA
            if g[1]:
                rate_info["eta"] = g[1]
            
            # g[2] is rate, g[3] is unit
            if g[2] and g[3]:
                rate_info["rate"] = float(g[2])
                rate_info["unit"] = g[3]
            
            # g[4] is the extra text
            if g[4]:
                rate_info["extra_text"] = g[4].strip()

            if rate_info:
                self.rate_queue.put(rate_info)

        except Exception as e:
            # This is a safety net. If anything goes wrong, we print the error
            # to the console for debugging but DO NOT crash the thread.
            print(f"Error in TqdmToQueueWriter: {e}", file=sys.stderr)
            print(f"Failed to parse string: {s}", file=sys.stderr)
        
        return len(s)
                    
class ProgressTracker:
    """
    A helper class to track and format progress updates for the LiveLog component.

    This versatile class operates in a hybrid mode for calculating iteration rates:
    1.  **Internal Calculation (Default):** It uses an Exponential Moving Average (EMA)
        to compute a smoothed, stable rate. The unit for this internal calculation
        (`it/s` or `s/it`) can be specified during initialization, making it flexible
        for different types of processes.
    2.  **External Override (Preferred):** It can accept a dictionary of externally
        captured rate data (e.g., from a `tqdm` instance). This provides the most
        accurate possible display by sourcing the rate and its unit directly from
        the process being monitored, overriding any internal calculations.

    The tracker also intelligently "freezes" the last known rate when the process
    status changes to 'success' or 'error', ensuring the final speed remains visible on the UI.
    """
    def __init__(self, total: int, description: str = "Processing...", 
                 smoothing_factor: float = 0.3, 
                 rate_unit: Literal["it/s", "s/it"] = "s/it"):
        """
        Initializes the progress tracker.

        Args:
            total (int): The total number of iterations for the process.
            description (str): A short, fixed description of the task being performed.
            smoothing_factor (float): The EMA smoothing factor used for the internal
                                      rate calculation. A smaller value (e.g., 0.1)
                                      results in smoother but less responsive updates.
            rate_unit (Literal["it/s", "s/it"]): The preferred unit for the
                                                 internal rate calculation when no
                                                 external data is provided. Defaults to "it/s".
        """
        self.total = total
        self.description = description
        self.smoothing_factor = smoothing_factor
        self.preferred_rate_unit = rate_unit  # Stores the user's preference for internal calculations.
        
        self.current = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_update_item = 0
        
        # State fields that will be updated and returned.
        self.rate = 0.0
        self.rate_unit = self.preferred_rate_unit  # Sets the initial unit.
        self.extra_info = {}
        self.has_started = False

    def update(self, advance: int = 1, status: str = "running", 
               logs: Optional[List[Dict]] = None, log_content: Optional[str] = None, 
               rate_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Updates the tracker's state and returns a dictionary formatted for the frontend.

        This is the core method of the tracker. It's designed to be called repeatedly
        during a long-running process. Its key feature is the ability to handle two
        distinct types of updates:

        1.  **Progress Updates (`advance > 0`):** When `advance` is a positive integer,
            the internal progress counter (`self.current`) is incremented. If no external
            `rate_data` is provided, the tracker will perform its internal rate
            calculation based on the time elapsed since the last advancing update.

        2.  **Text-Only Updates (`advance = 0`):** When `advance` is zero, the progress
            bar's position remains unchanged. This is useful for updating contextual
            information on the UI (e.g., "Processing tile 2/10...") without moving the
            main progress bar. In this mode, the method relies exclusively on the
            `rate_data` dictionary to update text fields like `extra_info`. The internal
            rate calculation is skipped, preserving the last known rate.

        Args:
            advance (int): The number of steps to advance the progress counter.
                           Defaults to 1. If 0, no progress is made, but other
                           information (like `extra_info` from `rate_data`) can still be updated.
            status (str): The current status of the process ("running", "success", "error").
            logs (Optional[List[Dict]]): An optional list of log dictionaries to pass to the frontend.
            log_content (Optional[str]): An optional string to override the fixed description for this update.
            rate_data (Optional[Dict]): A dictionary from an external source (like `tqdm`)
                                        containing keys like 'rate', 'unit', and 'extra'.
                                        If provided, this data will override all internal
                                        rate calculations and text fields.

        Returns:
            Dict[str, Any]: A state dictionary formatted for a frontend component,
                            containing all the necessary information to render the
                            progress bar and associated text.
        """
        # --- Progress Advancement ---
        if advance > 0 and not self.has_started:
            self.has_started = True
            # For better accuracy, reset the start time to when the first step is taken.
            self.start_time = time.time() 
        
        # Only increment the progress counter if explicitly told to.
        if advance > 0:
            self.current += advance
            self.current = min(self.current, self.total)

        now = time.time()
        self.extra_info = {}
        
        if self.has_started:
            # 1. Calculate and format elapsed time.
            elapsed_seconds = now - self.start_time
            minutes = int(elapsed_seconds // 60)
            seconds = int(elapsed_seconds % 60)
            self.extra_info['elapsed'] = f"{minutes:02d}:{seconds:02d}"
            
        # --- Rate and Information Update Logic ---
        
        
        rate_from_tqdm = None
        if rate_data:
            # Update values only if the corresponding key exists in the dictionary.
            # This prevents overwriting existing values with None if a key is missing.
            if "rate" in rate_data: 
                rate_from_tqdm = rate_data["rate"]
            if "unit" in rate_data: 
                self.rate_unit = rate_data["unit"]
            if "eta" in rate_data: 
                self.extra_info['eta'] = rate_data["eta"]
            if "extra_text" in rate_data: 
                self.extra_info['extra_text'] = rate_data["extra_text"]
        
        # Priority 1: Use external `rate_data` if available. This is the most accurate
        # source and is processed regardless of the `advance` value, allowing for
        # text-only updates.         
        if rate_from_tqdm is not None:
            self.rate = rate_from_tqdm
        # Priority 2: If no external data is provided, fall back to internal calculation.
        # This block is only executed when the process is running AND progress has actually
        # been made (`advance > 0`), as rate calculation is meaningless otherwise.
        elif status == "running" and advance > 0:
            delta_time = now - self.last_update_time
            delta_items = self.current - self.last_update_item

            # Prevent division by zero if updates are too fast or no items progressed.
            if delta_time > 0 and delta_items > 0:
                # Calculate rate based on the user's preferred unit ("it/s" or "s/it").
                if self.preferred_rate_unit == "it/s":
                    instant_rate = delta_items / delta_time
                    self.rate_unit = "it/s"
                else:  # "s/it"
                    instant_rate = delta_time / delta_items
                    self.rate_unit = "s/it"

                # Apply Exponential Moving Average (EMA) for a smoother, less jumpy rate.
                if self.rate == 0.0:  # Initialize with the first measurement.
                    self.rate = instant_rate
                else:
                    self.rate = (self.smoothing_factor * instant_rate) + \
                                ((1 - self.smoothing_factor) * self.rate)
             
            self.last_update_time = now
            self.last_update_item = self.current
        
        # Priority 3: If status is 'success' or 'error', or if `advance` is 0 without
        # `rate_data`, the logic above is skipped. This effectively "freezes" the
        # rate and extra_info fields at their last known values, which is the desired
        # behavior for terminal states or text-only updates.
        
        # Determine the description to display for this specific update.
        desc = log_content if log_content is not None else self.description
        
        # Assemble and return the final state dictionary for the frontend.
        return {
            "type": "progress",
            "current": self.current,
            "total": self.total,
            "desc": desc,
            "rate": self.rate,
            "rate_unit": self.rate_unit,
            "extra_info": self.extra_info,
            "status": status,
            "logs": logs or [],
        }
        

def livelog(
    log_names: List[str],
    outputs_for_yield: List[gr.components.Component],
    log_output_index: int,
    interactive_outputs_indices: List[int],
    result_output_index: int,
    use_tracker: bool = False,
    tracker_mode: str = "auto",
    tracker_total_arg_name: str | None = None,
    tracker_description: str = "Processing...",
    tracker_rate_unit: str = "it/s",
    tracker_total_steps: int = 100,
    disable_console_logs: bool | str = False
) -> Callable:
    """
    A decorator for Gradio applications that captures logs and progress updates from a function
    and streams them to a LiveLog component in real-time. It supports multi-logger capture,
    progress tracking, and UI updates for interactive components, enabling seamless monitoring
    of function execution in the Gradio UI.

    Args:
        log_names (List[str]): List of logger names to capture logs from. The first logger is used
            as the default if no 'log_name' is provided in the function's kwargs.
        outputs_for_yield (List[gr.components.Component]): List of Gradio components to yield updates to,
            including the LiveLog component and other output components (e.g., for results).
        log_output_index (int): Index of the LiveLog component in outputs_for_yield where log and
            progress updates are sent.
        interactive_outputs_indices (List[int]): Indices of components in outputs_for_yield to toggle
            as non-interactive during processing and re-enable afterward.
        result_output_index (int): Index of the component in outputs_for_yield to send the final result.
        use_tracker (bool, optional): If True, enables progress tracking with a ProgressTracker.
            Defaults to False.
        tracker_mode (str, optional): Progress tracking mode. Currently supports 'auto', which sends
            a final 'success' update when the function completes. Defaults to 'auto'.
        tracker_total_arg_name (str | None, optional): Name of the function's kwarg specifying the total
            number of steps for the progress tracker. If None, tracker_total_steps is used. Defaults to None.
        tracker_description (str, optional): Description for the LiveLog progress bar. Defaults to 'Processing...'.
        tracker_rate_unit (str, optional): Unit for the progress rate (e.g., 'it/s' or 's/it'). Defaults to 'it/s'.
        tracker_total_steps (int, optional): Default total steps for the progress tracker if tracker_total_arg_name
            is not provided. Defaults to 100.
        disable_console_logs (bool | str, optional): Controls console log suppression. If True, suppresses console logs.
            If a string, uses the value of the named kwarg in the function. Defaults to False.

    Returns:
        Callable: A decorator that wraps the input function to enable log and progress streaming.

    Example:
        @livelog(
            log_names=["my_app"],
            outputs_for_yield=[live_log_component, result_output],
            log_output_index=0,
            interactive_outputs_indices=[1],
            result_output_index=1,
            use_tracker=True,
            tracker_description="Training model...",
            tracker_total_steps=50
        )
        def my_function(total_steps: int, log_callback: Callable):
            for i in range(total_steps):
                log_callback(advance=1, log_content=f"Step {i+1}/{total_steps}")
                time.sleep(0.1)
            return "Completed"
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Bind function arguments to inspect defaults and kwargs
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            all_kwargs = bound_args.arguments
            error_occurred = False  # Track if an error occurs during execution
            all_logs: List[Dict[str, Any]] = []  # Store all captured log records
            update_queue = queue.Queue()  # Queue for streaming updates to the UI

            # Resolve console log suppression setting
            should_disable_console = all_kwargs.get(disable_console_logs, False) if isinstance(disable_console_logs, str) else disable_console_logs

            # Set up logger based on log_names or kwargs
            log_name = all_kwargs.get("log_name", log_names[0] if log_names else "logging_app")
            error_logger = logging.getLogger(log_name)
            error_logger.setLevel(logging.DEBUG)
            if not error_logger.handlers:
                console_handler = logging.StreamHandler()
                console_handler.flush = sys.stderr.flush
                error_logger.addHandler(console_handler)

            def worker():
                """
                Worker function that runs in a separate thread to execute the decorated function,
                capture logs, and stream progress updates to the UI.
                """
                nonlocal error_occurred, all_logs
                rate_queue = queue.Queue() if use_tracker else None
                tqdm_writer = TqdmToQueueWriter(rate_queue) if use_tracker else None
                progress_bar_handler = Tee(sys.stderr, tqdm_writer) if use_tracker else None
                last_known_rate_data: Dict[str, Any] | None = None
                tracker: ProgressTracker | None = None
                last_current: int = 0
                updates_sent = 0

                def ui_update_callback(advance: int = 0, status: str = "running", final_payload: Any = None, log_content: str = None):
                    """
                    Callback to update the UI with progress and log data.

                    Args:
                        advance (int, optional): Number of steps to advance the progress tracker. Defaults to 0.
                        status (str, optional): Progress status ('running', 'success', 'error'). Defaults to 'running'.
                        final_payload (Any, optional): Final result to send to the UI. Defaults to None.
                        log_content (str, optional): Additional log content to display. Defaults to None.
                    """
                    nonlocal all_logs, last_known_rate_data, tracker, last_current, updates_sent
                    if use_tracker and rate_queue:
                        while not rate_queue.empty():
                            try:
                                last_known_rate_data = rate_queue.get_nowait()
                            except queue.Empty:
                                break

                    # Capture new log records
                    new_records = get_logs()
                    if new_records:
                        new_logs = [{"type": "log", "level": "SUCCESS" if r.levelno == logging.INFO + 5 else r.levelname, "content": r.getMessage()} for r in new_records]
                        all_logs.extend(new_logs)

                    update_dict = {}
                    if tracker:
                        update_dict = tracker.update(advance=advance, status=status, logs=all_logs, log_content=log_content, rate_data=last_known_rate_data)
                        current = update_dict.get("current", 0)
                        update_queue.put({"type": "progress_update", "content": update_dict, "final_payload": final_payload})
                        last_current = max(current, last_current)
                        updates_sent += 1
                        time.sleep(0.01)
                    else:
                        update_dict = {"type": "progress", "logs": all_logs, "status": status, "current": 0, "total": 1, "desc": log_content or tracker_description}
                        update_queue.put({"type": "progress_update", "content": update_dict, "final_payload": final_payload})
                        updates_sent += 1
                        time.sleep(0.01)

                try:
                    with capture_logs(log_level=logging.INFO, log_name=[log_name], disable_console=should_disable_console) as get_logs:
                        # Initialize progress tracker
                        total_steps = all_kwargs.get(tracker_total_arg_name, tracker_total_steps) if tracker_total_arg_name else tracker_total_steps
                        rate_unit = all_kwargs.get("rate_unit", tracker_rate_unit)
                        if use_tracker:
                            tracker = ProgressTracker(total=total_steps, description=tracker_description, rate_unit=rate_unit)
                            kwargs['tracker'] = tracker
                            kwargs['progress_bar_handler'] = progress_bar_handler

                        kwargs['log_callback'] = ui_update_callback

                        # Send initial progress update
                        if use_tracker:
                            update_dict = tracker.update(advance=0, status="running", logs=all_logs, log_content=tracker_description)
                            update_queue.put({"type": "progress_update", "content": update_dict, "final_payload": None})
                            updates_sent += 1
                            time.sleep(0.01)

                        # Execute the decorated function
                        result = func(*args, **kwargs)

                        # Send final update for auto mode
                        if tracker_mode == "auto" and result is not None:
                            update_dict = tracker.update(advance=tracker.total - last_current, status="success", logs=all_logs, log_content="Process completed successfully!")
                            update_queue.put({"type": "progress_update", "content": update_dict, "final_payload": result})
                            updates_sent += 1
                            time.sleep(0.05)

                        return result

                except Exception as e:
                    error_occurred = True
                    update_dict = {
                        "type": "progress",
                        "current": last_current,
                        "total": total_steps,
                        "desc": f"Error: {str(e)}",
                        "status": "error",
                        "logs": all_logs + [{"type": "log", "level": "ERROR", "content": f"Error: {str(e)}"}],
                        "rate": 0.0,
                        "rate_unit": rate_unit
                    }
                    update_queue.put({"type": "progress_update", "content": update_dict, "final_payload": None})
                    updates_sent += 1
                    time.sleep(0.05)
                    return None
                finally:
                    if not error_occurred and tracker and last_current < tracker.total:
                        update_dict = tracker.update(advance=tracker.total - last_current, status="success", logs=all_logs, log_content="Process completed successfully!")
                        update_queue.put({"type": "progress_update", "content": update_dict, "final_payload": result if 'result' in locals() else None})
                        updates_sent += 1
                        time.sleep(0.05)
                    update_queue.put({"type": "done"})
                    time.sleep(0.05)

            # Yield minimal initial UI state
            initial_updates = [gr.skip()] * len(outputs_for_yield)
            for i in interactive_outputs_indices:
                initial_updates[i] = gr.update(interactive=False)
            if use_tracker:
                initial_updates[log_output_index] = {
                    "type": "progress",
                    "current": 0,
                    "total": 1,  # Temporary value
                    "desc": tracker_description,
                    "status": "running",
                    "logs": all_logs,
                    "rate": 0.0,
                    "rate_unit": all_kwargs.get("rate_unit", tracker_rate_unit)
                }
            yield tuple(initial_updates)

            # Start the worker thread
            process_thread = threading.Thread(target=worker)
            process_thread.start()

            # Process updates from the queue
            final_result = None
            last_yielded_current = 0
            max_wait_time = 60.0
            start_time = time.time()
            updates_yielded = 0
            while (process_thread.is_alive() or not update_queue.empty()) and (time.time() - start_time < max_wait_time):
                try:
                    update = update_queue.get(timeout=0.5)
                    yield_updates = [gr.skip()] * len(outputs_for_yield)

                    if update["type"] == "progress_update":
                        current = update["content"].get("current", 0)
                        total = update["content"].get("total", 1)
                        status = update["content"].get("status", "running")
                        yield_updates[log_output_index] = update["content"]
                        if status in ["success", "error"]:
                            final_result = update.get("final_payload")
                            if final_result is not None:
                                yield_updates[result_output_index] = gr.update(value=final_result)
                        last_yielded_current = max(current, last_yielded_current)
                        yield tuple(yield_updates)
                        updates_yielded += 1
                        time.sleep(0.01)

                    elif update["type"] == "done":
                        break

                except queue.Empty:
                    yield tuple([gr.skip()] * len(outputs_for_yield))
                    continue

            # Drain remaining updates
            while not update_queue.empty():
                try:
                    update = update_queue.get_nowait()
                    yield_updates = [gr.skip()] * len(outputs_for_yield)
                    if update["type"] == "progress_update":
                        current = update["content"].get("current", 0)
                        total = update["content"].get("total", 1)
                        status = update["content"].get("status", "running")
                        yield_updates[log_output_index] = update["content"]
                        if status in ["success", "error"]:
                            final_result = update.get("final_payload")
                            if final_result is not None:
                                yield_updates[result_output_index] = gr.update(value=final_result)
                        last_yielded_current = max(current, last_yielded_current)
                        yield tuple(yield_updates)
                        updates_yielded += 1
                        time.sleep(0.01)
                except queue.Empty:
                    break

            # Force final update if needed
            total_steps = all_kwargs.get(tracker_total_arg_name, tracker_total_steps) if tracker_total_arg_name else tracker_total_steps
            rate_unit = all_kwargs.get("rate_unit", tracker_rate_unit)
            if use_tracker and last_yielded_current < total_steps and not error_occurred:
                yield_updates = [gr.skip()] * len(outputs_for_yield)
                yield_updates[log_output_index] = {
                    "type": "progress",
                    "current": total_steps,
                    "total": total_steps,
                    "desc": "Process completed successfully!",
                    "status": "success",
                    "logs": all_logs + [{"type": "log", "level": "SUCCESS", "content": "Process completed successfully!"}],
                    "rate": 0.0,
                    "rate_unit": rate_unit
                }
                if final_result is not None:
                    yield_updates[result_output_index] = gr.update(value=final_result)
                yield tuple(yield_updates)
                updates_yielded += 1
                time.sleep(0.05)

            # Yield final UI state
            final_updates = [gr.skip()] * len(outputs_for_yield)
            for i in interactive_outputs_indices:
                final_updates[i] = gr.update(interactive=True)
            if final_result is not None:
                final_updates[result_output_index] = gr.update(value=final_result)
            yield tuple(final_updates)

            # Clean up logger handlers to prevent memory leaks
            for handler in error_logger.handlers[:]:
                error_logger.removeHandler(handler)
                handler.close()

        return wrapper
    return decorator