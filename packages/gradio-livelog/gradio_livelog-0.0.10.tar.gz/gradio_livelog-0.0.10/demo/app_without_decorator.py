# demo/app.py

import spaces
import gradio as gr
import torch
from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
import queue
import threading
import asyncio
import sys
import logging
import random
import numpy as np

# Import the component and ALL its utilities
from gradio_livelog import LiveLog
from gradio_livelog.utils import ProgressTracker, Tee, TqdmToQueueWriter, capture_logs

# --- 1. SETUP ---
MODEL_ID = "SG161222/RealVisXL_V5.0_Lightning"
MAX_SEED = np.iinfo(np.int32).max

# --- 2. LOGIC FOR THE "LIVELOG FEATURE DEMO" TAB ---
# Set up a dedicated logger for the simulation part of the demo.
app_logger = logging.getLogger("logging_app")
app_logger.setLevel(logging.INFO)
# Avoid adding duplicate handlers if the script is reloaded in some environments.
if not app_logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    app_logger.addHandler(console_handler)

async def run_process(disable_console: bool, rate_unit: str, run_error_case: bool):
    """
    An async generator that simulates a long-running process, yielding updates
    for the LiveLog component. It demonstrates manual progress tracking.
    """
    # Use the capture_logs context manager to intercept logs from `app_logger`.
    with capture_logs(log_level=logging.INFO, log_name=["logging_app"], disable_console=disable_console) as get_logs:
        total_steps = 100
        tracker = ProgressTracker(total=total_steps, description="Simulating a process...", rate_unit=rate_unit)
        all_logs = []
        last_log_content = None
        
        initial_log = f"Starting simulated process with {total_steps} steps..."
        app_logger.info(initial_log)
        # --- Start of heavily increased initial logs ---
        app_logger.info("Initializing system parameters...")
        app_logger.debug("Debug: Configuration file loaded.") # This will be ignored unless log level is changed to DEBUG
        app_logger.info("Verifying asset integrity (check 1/3)...")
        app_logger.info("Verifying asset integrity (check 2/3)...")
        app_logger.info("Verifying asset integrity (check 3/3)...")
        app_logger.info("Checking for required dependencies...")
        app_logger.info("  - Dependency 'numpy' found.")
        app_logger.info("  - Dependency 'torch' found.")
        app_logger.info("Pre-allocating memory buffer (1024 MB)...")
        app_logger.info("Initialization complete. Starting main loop.")
        # --- End of added logs ---
        logs = [
            {
                "type": "log",
                "level": "SUCCESS" if record.levelno == logging.INFO + 5 else record.levelname,
                "content": record.getMessage()
            }
            for record in get_logs()
        ]
        all_logs.extend(logs)
        last_log_content = logs[-1]["content"] if logs else None        
        yield tracker.update(advance=0, status="running", logs=all_logs, log_content=None)

        # A list of sub-tasks to log for every single step
        sub_tasks = [
            "Reading data block...",
            "Applying filter algorithm...",
            "Normalizing values...",
            "Checking for anomalies..."
        ]

        for i in range(total_steps):
            await asyncio.sleep(0.03)
            current_step = i + 1
            
            # --- NEW: Massively increased logging inside the loop ---
            # Log multiple sub-tasks for EACH step to generate high volume.
            app_logger.info(f"--- Begin Step {current_step}/{total_steps} ---")
            for task in sub_tasks:
                app_logger.info(f"  - {task} (completed)")
            
            # Keep the specific event logs for variety
            if current_step == 10:
                app_logger.warning(f"Low disk space warning at step {current_step}.")
            elif current_step == 30:
                app_logger.log(logging.INFO + 5, f"Asset pack loaded successfully at step {current_step}.")
            elif current_step == 75:
                app_logger.critical(f"Checksum mismatch! Data may be corrupt at step {current_step}.")
            
            app_logger.info(f"--- End Step {current_step}/{total_steps} ---")

            if run_error_case and current_step == 50:
                app_logger.error("A fatal simulation error occurred! Aborting.")
                logs = [
                    {
                        "type": "log",
                        "level": "SUCCESS" if record.levelno == logging.INFO + 5 else record.levelname,
                        "content": record.getMessage()
                    }
                    for record in get_logs()
                ]
                all_logs.extend(logs)
                last_log_content = logs[-1]["content"] if logs else last_log_content
                yield tracker.update(advance=0, status="error", logs=all_logs, log_content=last_log_content)
                return
            
            logs = [
                {
                    "type": "log",
                    "level": "SUCCESS" if record.levelno == logging.INFO + 5 else record.levelname,
                    "content": record.getMessage()
                }
                for record in get_logs()
            ]
            all_logs.extend(logs)
            if logs:
                last_log_content = logs[-1]["content"]
            yield tracker.update(advance=1, status="running", logs=all_logs, log_content=last_log_content)
        
        final_log = "Process completed successfully!"
        app_logger.log(logging.INFO + 5, final_log)
        # --- Start of heavily increased final logs ---
        app_logger.info("Performing final integrity check.")
        app_logger.info("Saving results to 'output.log'...")
        app_logger.info("Cleaning up temporary files...")
        app_logger.info("Releasing memory buffer.")
        app_logger.info("Disconnecting from all services.")
        app_logger.info("Process finished.")
        # --- End of added logs ---
        logs = [
            {
                "type": "log",
                "level": "SUCCESS" if record.levelno == logging.INFO + 5 else record.levelname,
                "content": record.getMessage()
            }
            for record in get_logs()
        ]
        all_logs.extend(logs)
        last_log_content = logs[-1]["content"] if logs else last_log_content
        yield tracker.update(advance=0, status="success", logs=all_logs, log_content=last_log_content)     
        
def update_livelog_properties(mode, color, lines, scroll):
    """Callback to update LiveLog's visual properties dynamically."""
    return gr.update(display_mode=mode, background_color=color, line_numbers=lines, autoscroll=scroll)

def clear_output():
    """Callback to clear the LiveLog component."""
    return None

# --- Wrapper functions for the simulation tab events ---
async def run_success_case(disable_console: bool, rate_unit: str):
    """Wrapper to run the simulation process in a success scenario."""
    yield None # Initial empty yield for Gradio
    async for update in run_process(disable_console=disable_console, rate_unit=rate_unit, run_error_case=False):
        yield update

async def run_error_case(disable_console: bool, rate_unit: str):
    """Wrapper to run the simulation process in an error scenario."""
    yield None
    async for update in run_process(disable_console=disable_console, rate_unit=rate_unit, run_error_case=True):
        yield update

# --- 3. LOGIC FOR THE "DIFFUSION PIPELINE INTEGRATION" TAB ---
diffusion_pipeline = None
pipeline_lock = threading.Lock()
def load_pipeline():
    """A thread-safe function to load the model, ensuring it's only done once."""
    global diffusion_pipeline
    with pipeline_lock:
        if diffusion_pipeline is None:
            print("Loading Stable Diffusion model for the first time...")
            pipe = StableDiffusionXLPipeline.from_pretrained(
                MODEL_ID, torch_dtype=torch.float16, use_safetensors=True, add_watermarker=False, device_map="cuda"
            )
            pipe.enable_vae_tiling()
            pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)        
            diffusion_pipeline = pipe
            print("Model loaded successfully!")
    return diffusion_pipeline

@spaces.GPU(duration=60, enable_queue=True)
def run_diffusion_in_thread(prompt: str, disable_console: bool, update_queue: queue.Queue):
    """
    The main worker function for the diffusion process. It runs in a separate thread.
    It captures logs and TQDM progress, sending formatted updates back to the main
    thread via a queue.
    """
    tracker = None    
    with capture_logs(log_level=logging.INFO, log_name=["logging_app"], disable_console=disable_console) as get_logs:
        try:            
            pipe = load_pipeline()
            
            # Set up TQDM progress capture
            rate_queue = queue.Queue()
            tqdm_writer = TqdmToQueueWriter(rate_queue)
            progress_bar_handler = Tee(sys.stderr, tqdm_writer)
            pipe.set_progress_bar_config(file=progress_bar_handler, disable=False, ncols=100, dynamic_ncols=True, ascii=" █")
            
            seed = random.randint(0, MAX_SEED)
            generator = torch.Generator(device="cuda").manual_seed(seed)
            prompt_style = f"hyper-realistic 8K image of {prompt}..."
            negative_prompt_style = "cartoonish, low resolution..."
            num_inference_steps = 10
            
            all_logs = []
            last_known_rate_data = None

            def process_and_send_updates(status="running", advance=0, final_image_payload=None):
                """
                Core callback to capture logs/progress and send a complete update
                object to the UI queue.
                """
                nonlocal all_logs, last_known_rate_data
                
                # Get TQDM rate data if available
                new_rate_data = None
                while not rate_queue.empty():
                    try: new_rate_data = rate_queue.get_nowait()
                    except queue.Empty: break
                if new_rate_data is not None: last_known_rate_data = new_rate_data
                
                # Get new log records
                new_records = get_logs()
                if new_records:
                    new_logs = [{"type": "log", "level": "SUCCESS" if r.levelno == logging.INFO + 5 else r.levelname, "content": r.getMessage()} for r in new_records]
                    all_logs.extend(new_logs)
                
                # Build the update dictionary
                update_dict = {}
                if tracker:
                    update_dict = tracker.update(advance=advance, status=status, logs=all_logs, rate_data=last_known_rate_data)
                else:
                    update_dict = {"type": "progress", "logs": all_logs, "current": 0, "total": num_inference_steps, "desc": "Diffusion Steps"}

                update_queue.put((final_image_payload, update_dict))
                
            app_logger.info(f"Using seed: {seed}")
            process_and_send_updates()
                        
            app_logger.info("Starting diffusion process...")
            process_and_send_updates()
                        
            tracker = ProgressTracker(total=num_inference_steps, description="Diffusion Steps", rate_unit='it/s')
            
            def progress_callback(pipe_instance, step, timestep, callback_kwargs):
                """Callback passed to the diffusers pipeline, called at each step."""
                process_and_send_updates(advance=1) 
                return callback_kwargs
                        
            # Run the main diffusion pipeline
            images = pipe(
                prompt=prompt_style, negative_prompt=negative_prompt_style, width=1024, height=1024,
                guidance_scale=3.0, num_inference_steps=num_inference_steps,
                generator=generator, callback_on_step_end=progress_callback
            ).images
            
            app_logger.log(logging.INFO + 5, "Image generated successfully!")
            process_and_send_updates(status="success", final_image_payload=images)

        except Exception as e:
            app_logger.error(f"Error in diffusion thread: {e}", exc_info=True)                    
            process_and_send_updates(status="error")                                                        
        finally:
            # Signal that the thread has finished
            update_queue.put(None)
            
@spaces.GPU(duration=60, enable_queue=True)
def generate(prompt: str):
    """
    The main Gradio event function. It starts the worker thread and yields
    updates from the queue back to the UI components.
    """   
    # Yield initial state: no images, no logs, and disable the button.
    yield None, None, gr.update(interactive=False)    
    
    update_queue = queue.Queue()
    diffusion_thread = threading.Thread(target=run_diffusion_in_thread,  args=(prompt, True, update_queue))
    diffusion_thread.start()
    
    final_images = None
    log_update = None
    
    # Loop to get updates from the worker thread's queue.
    while True:
        update = update_queue.get()
        if update is None: # The 'None' signal means the thread is done.
            break
        
        images, log_update = update
        if images:
            final_images = images
      
        # Yield the new data to the UI outputs.
        yield final_images, log_update, gr.skip()
    
    # Yield the final state: final images, last log update, and re-enable the button.
    yield final_images, log_update, gr.update(interactive=True)

# --- 4. THE COMBINED GRADIO UI with TABS ---
with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    gr.HTML("<h1><center>LiveLog Component Showcase</center></h1>")

    with gr.Tabs():
        with gr.TabItem("LiveLog Feature Demo"):            
            gr.Markdown("### Test all features of the LiveLog component interactively.")
            with gr.Row():
                with gr.Column(scale=3):
                    feature_logger = LiveLog(label="Process Output", line_numbers=True, height=450, background_color="#000000", display_mode="full")
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.Markdown("### Component Properties")
                        display_mode_radio = gr.Radio(["full", "log", "progress"], label="Display Mode", value="full")
                        rate_unit = gr.Radio(["it/s","s/it"], label="Progress rate unit", value="it/s")
                        bg_color_picker = gr.ColorPicker(label="Background Color", value="#000000")
                        line_numbers_checkbox = gr.Checkbox(label="Show Line Numbers", value=True)
                        autoscroll_checkbox = gr.Checkbox(label="Autoscroll", value=True)
                        disable_console_checkbox = gr.Checkbox(label="Disable Python Console Output", value=True)
                    with gr.Group():
                        gr.Markdown("### Simulation Controls")
                        start_btn = gr.Button("Run Success Case", variant="primary")
                        error_btn = gr.Button("Run Error Case")
            
            start_btn.click(fn=run_success_case, inputs=[disable_console_checkbox, rate_unit], outputs=feature_logger)
            error_btn.click(fn=run_error_case, inputs=[disable_console_checkbox, rate_unit], outputs=feature_logger)
            feature_logger.clear(fn=clear_output, inputs=None, outputs=feature_logger)
            controls = [display_mode_radio, bg_color_picker, line_numbers_checkbox, autoscroll_checkbox]
            for control in controls:
                control.change(fn=update_livelog_properties, inputs=controls, outputs=feature_logger)
        
        with gr.TabItem("Diffusion Pipeline Integration"):               
            gr.Markdown("### Use `LiveLog` to monitor a real image generation process.")
            with gr.Row():
                with gr.Column(scale=3):
                    with gr.Group():
                        prompt = gr.Textbox(label="Enter your prompt", show_label=False, placeholder="A cinematic photo...", scale=8, container=False)
                        run_button = gr.Button("Generate", scale=1, variant="primary")
                    livelog_viewer = LiveLog(label="Process Monitor", height=350, display_mode="full", line_numbers=False)
                with gr.Column(scale=2):
                    result_gallery = gr.Gallery(label="Result", columns=1, show_label=False, height=500, min_width=768, preview=True)
            
            run_button.click(fn=generate, inputs=[prompt], outputs=[result_gallery, livelog_viewer, run_button])
            prompt.submit(fn=generate, inputs=[prompt], outputs=[result_gallery, livelog_viewer, run_button])
            livelog_viewer.clear(fn=clear_output, inputs=None, outputs=[livelog_viewer])
                
if __name__ == "__main__":
    demo.queue(max_size=50).launch(debug=True)