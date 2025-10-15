import queue
import spaces
import gradio as gr
import torch
from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
import threading
import time
import sys
import logging
import random
import numpy as np
from typing import Callable

from gradio_livelog import LiveLog
from gradio_livelog.utils import ProgressTracker, livelog

# --- 1. SETUP ---
MODEL_ID = "SG161222/RealVisXL_V5.0_Lightning"
MAX_SEED = np.iinfo(np.int32).max

def configure_logging():
    """
    Configure logging for the application with two separate loggers:
    - 'logging_app' for the LiveLog Feature Demo tab.
    - 'diffusion_app' for the Diffusion Pipeline Integration tab.
    Each logger outputs to the console with DEBUG level.
    """
      
    #logging.basicConfig(level=logging.DEBUG)

    # Logger for LiveLog Feature Demo
    app_logger = logging.getLogger("logging_app")
    app_logger.setLevel(logging.INFO)
    if not app_logger.handlers:
        console_handler = logging.StreamHandler()
        #console_handler.flush = sys.stderr.flush
        app_logger.addHandler(console_handler)

    # Logger for Diffusion Pipeline Integration
    diffusion_logger = logging.getLogger("diffusion_app")
    diffusion_logger.setLevel(logging.INFO)
    if not diffusion_logger.handlers:
        console_handler = logging.StreamHandler()
        #console_handler.flush = sys.stderr.flush
        diffusion_logger.addHandler(console_handler)

# --- 2. BUSINESS LOGIC FUNCTIONS ---
def _run_process_logic(run_error_case: bool, **kwargs):
    """
    Simulate a process with multiple steps, logging progress and status updates to the LiveLog component.
    Used in the LiveLog Feature Demo tab to demonstrate logging and progress tracking.

    Args:
        run_error_case (bool): If True, simulates an error at step 25 to test error handling.
        **kwargs: Additional arguments including:
            - tracker (ProgressTracker): Tracker for progress updates.
            - log_callback (Callable): Callback to send logs and progress to LiveLog.
            - total_steps (int): Total number of steps for the process.
            - log_name (str, optional): Logger name, defaults to 'logging_app'.

    Raises:
        RuntimeError: If run_error_case is True, raises an error at step 25.
    """
    tracker: ProgressTracker = kwargs['tracker']
    log_callback: Callable = kwargs['log_callback']
    total_steps = kwargs.get('total_steps', tracker.total)
    logger = logging.getLogger(kwargs.get('log_name', 'logging_app'))

    logger.info(f"Starting simulated process with {total_steps} steps...")
    log_callback(advance=0, log_content=f"Starting simulated process with {total_steps} steps...")
    time.sleep(0.01)
    
    logger.info("Initializing system parameters...")
    logger.info("Verifying asset integrity (check 1/3)...")
    logger.info("Verifying asset integrity (check 2/3)...")
    logger.info("Verifying asset integrity (check 3/3)...")
    logger.info("Checking for required dependencies...")
    logger.info("  - Dependency 'numpy' found.")
    logger.info("  - Dependency 'torch' found.")
    logger.info("Pre-allocating memory buffer (1024 MB)...")
    logger.info("Initialization complete. Starting main loop.")
    log_callback(log_content="Simulating a process...")
    time.sleep(0.01)

    sub_tasks = ["Reading data block...", "Applying filter algorithm...", "Normalizing values...", "Checking for anomalies..."]

    update_interval = 2  # Update every 2 steps to reduce overhead
    for i in range(total_steps):
        time.sleep(0.03)
        current_step = i + 1
        logger.info(f"--- Begin Step {current_step}/{total_steps} ---")
        for task in sub_tasks:
            logger.info(f"  - {task} (completed)")

        if current_step == 10:
            logger.warning(f"Low disk space warning at step {current_step}.")
        elif current_step == 30:
            logger.log(logging.INFO + 5, f"Asset pack loaded at step {current_step}.")
        elif current_step == 40:
            logger.critical(f"Checksum mismatch at step {current_step}.")

        logger.info(f"--- End Step {current_step}/{total_steps} ---")

        if run_error_case and current_step == 25:
            logger.error("A fatal simulation error occurred! Aborting.")
            log_callback(status="error", log_content="A fatal simulation error occurred! Aborting.")
            time.sleep(0.01)
            raise RuntimeError("A fatal simulation error occurred! Aborting.")

        if current_step % update_interval == 0 or current_step == total_steps:
            log_callback(advance=min(update_interval, total_steps - (current_step - update_interval)), log_content=f"Processing step {current_step}/{total_steps}")
            time.sleep(0.01)

    logger.log(logging.INFO + 5, "Process completed successfully!")
    log_callback(status="success", log_content="Process completed successfully!")
    time.sleep(0.01)
    logger.info("Performing final integrity check.")
    logger.info("Saving results to 'output.log'...")
    logger.info("Cleaning up temporary files...")
    logger.info("Releasing memory buffer.")
    logger.info("Disconnecting from all services.")
    logger.info("Process finished.")

def _run_diffusion_logic(prompt: str, **kwargs):
    """
    Run a Stable Diffusion pipeline to generate an image based on a prompt, logging progress and status
    to the LiveLog component. Used in the Diffusion Pipeline Integration tab.

    Args:
        prompt (str): The text prompt for image generation.
        **kwargs: Additional arguments including:
            - log_callback (Callable): Callback to send logs and progress to LiveLog.
            - progress_bar_handler: Handler for tqdm progress updates.
            - total_steps (int, optional): Number of diffusion steps, defaults to 10.
            - log_name (str, optional): Logger name, defaults to 'diffusion_app'.

    Returns:
        List: Generated images from the diffusion pipeline.

    Raises:
        Exception: If an error occurs during image generation, logged and re-raised.
    """
    log_callback = kwargs.get('log_callback')
    progress_bar_handler = kwargs.get('progress_bar_handler')
    total_steps = kwargs.get('total_steps', 10)
    logger = logging.getLogger(kwargs.get('log_name', 'diffusion_app'))

    try:
        pipe = load_pipeline()
        pipe.set_progress_bar_config(file=progress_bar_handler, disable=False, ncols=100, dynamic_ncols=True, ascii=" █")
        
        seed = random.randint(0, MAX_SEED)
        generator = torch.Generator(device="cuda").manual_seed(seed)
        prompt_style = f"hyper-realistic 8K image of {prompt}. ultra-detailed, lifelike, high-resolution, sharp, vibrant colors, photorealistic"
        negative_prompt_style = "cartoonish, low resolution, blurry, simplistic, abstract, deformed, ugly"
        
        logger.info(f"Using seed: {seed}")
        log_callback(log_content=f"Using seed: {seed}")
        time.sleep(0.03)
        logger.info("Starting diffusion process...")
        log_callback(log_content="Starting diffusion process...")
        time.sleep(0.03)
        
        def progress_callback(pipe_instance, step, timestep, callback_kwargs):
            """Callback for diffusion pipeline to log progress at each step."""
            if log_callback:
                log_callback(advance=1, log_content=f"Diffusion step {step + 1}/{total_steps}")
                time.sleep(0.03)
            return callback_kwargs
                    
        images = pipe(
            prompt=prompt_style,
            negative_prompt=negative_prompt_style,
            width=1024,
            height=1024,
            guidance_scale=3.0,
            num_inference_steps=total_steps,
            generator=generator,
            callback_on_step_end=progress_callback
        ).images
        
        logger.log(logging.INFO + 5, "Image generated successfully!")
        log_callback(status="success", final_payload=images, log_content="Image generated successfully!")
        time.sleep(0.03)
        return images
    except Exception as e:
        logger.error(f"Error in diffusion logic: {e}, process aborted!")
        log_callback(status="error", log_content=f"Error: {str(e)}")
        time.sleep(0.03)
        raise e

# --- 3. PIPELINE LOADING ---
diffusion_pipeline = None
pipeline_lock = threading.Lock()

def load_pipeline():
    """
    Load and cache the Stable Diffusion XL pipeline for image generation, ensuring thread-safe initialization.

    Returns:
        StableDiffusionXLPipeline: The loaded pipeline, ready for image generation.
    """
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

# --- 4. GRADIO UI ---
def create_gradio_interface():
    """
    Create a Gradio interface to showcase the LiveLog component with two tabs:
    - LiveLog Feature Demo: Interactive testing of LiveLog features.
    - Diffusion Pipeline Integration: Real-time monitoring of image generation with Stable Diffusion.
    """
    with gr.Blocks(theme=gr.themes.Ocean()) as demo:
        gr.HTML("<h1><center>LiveLog Component Showcase</center></h1>")

        with gr.Tabs():
            with gr.TabItem("LiveLog Feature Demo"):
                """Interactive tab to test LiveLog features with customizable properties and simulated processes."""
                gr.Markdown("### Test all features of the LiveLog component interactively.")
                with gr.Row():
                    with gr.Column(scale=3):
                        feature_logger = LiveLog(
                            label="Process Output",
                            line_numbers=True,
                            height=450,
                            background_color="#000000",
                            display_mode="full"                            
                        )
                    with gr.Column(scale=1):
                        with gr.Group():
                            gr.Markdown("### Component Properties")
                            display_mode_radio = gr.Radio(["full", "log", "progress"], label="Display Mode", value="full")
                            rate_unit = gr.Radio(["it/s", "s/it"], label="Progress rate unit", value="it/s")
                            bg_color_picker = gr.ColorPicker(label="Background Color", value="#000000")
                            line_numbers_checkbox = gr.Checkbox(label="Show Line Numbers", value=True)
                            autoscroll_checkbox = gr.Checkbox(label="Autoscroll", value=True)
                            disable_console_checkbox = gr.Checkbox(label="Disable Python Console Output", value=False)
                        with gr.Group():
                            gr.Markdown("### Simulation Controls")
                            start_btn = gr.Button("Run Success Case", variant="primary")
                            error_btn = gr.Button("Run Error Case")

                @livelog(
                    log_names=["logging_app"],
                    outputs_for_yield=[feature_logger, start_btn, error_btn],
                    log_output_index=0,
                    interactive_outputs_indices=[1, 2],
                    result_output_index=0,
                    use_tracker=True,
                    tracker_mode="manual",
                    tracker_total_arg_name="total_steps",
                    tracker_description="Simulating a process...",
                    tracker_rate_unit="it/s",
                    disable_console_logs="disable_console",
                    tracker_total_steps=100
                )
                def run_success_case(disable_console: bool, rate_unit: str, total_steps: int = 100, **kwargs):
                    """
                    Run a simulated process that completes successfully, logging progress and status to feature_logger.

                    Args:
                        disable_console (bool): If True, suppress console logs.
                        rate_unit (str): Unit for progress rate ('it/s' or 's/it').
                        total_steps (int, optional): Total steps for the process. Defaults to 100.
                        **kwargs: Additional arguments passed to _run_process_logic.
                    """
                    kwargs["total_steps"] = total_steps
                    kwargs["rate_unit"] = rate_unit
                    kwargs["disable_console"] = disable_console
                    kwargs["log_name"] = "logging_app"
                    _run_process_logic(run_error_case=False, **kwargs)

                @livelog(
                    log_names=["logging_app"],
                    outputs_for_yield=[feature_logger, start_btn, error_btn],
                    log_output_index=0,
                    interactive_outputs_indices=[1, 2],
                    result_output_index=0,
                    use_tracker=True,
                    tracker_mode="manual",
                    tracker_total_arg_name="total_steps",
                    tracker_description="Simulating an error...",
                    tracker_rate_unit="it/s",
                    disable_console_logs="disable_console",
                    tracker_total_steps=100
                )
                def run_error_case(disable_console: bool, rate_unit: str, total_steps: int = 100, **kwargs):
                    """
                    Run a simulated process that triggers an error, logging progress and error to feature_logger.

                    Args:
                        disable_console (bool): If True, suppress console logs.
                        rate_unit (str): Unit for progress rate ('it/s' or 's/it').
                        total_steps (int, optional): Total steps for the process. Defaults to 100.
                        **kwargs: Additional arguments passed to _run_process_logic.
                    """
                    kwargs["total_steps"] = total_steps
                    kwargs["rate_unit"] = rate_unit
                    kwargs["disable_console"] = disable_console
                    kwargs["log_name"] = "logging_app"
                    _run_process_logic(run_error_case=True, **kwargs)

                start_btn.click(
                    fn=run_success_case,
                    inputs=[disable_console_checkbox, rate_unit],
                    outputs=[feature_logger, start_btn, error_btn]
                )
                error_btn.click(
                    fn=run_error_case,
                    inputs=[disable_console_checkbox, rate_unit],
                    outputs=[feature_logger, start_btn, error_btn]
                )
                feature_logger.clear(fn=lambda: None, outputs=[feature_logger])
                
                controls = [display_mode_radio, bg_color_picker, line_numbers_checkbox, autoscroll_checkbox]
                def update_livelog_properties(mode, color, lines, scroll):
                    """Update LiveLog properties dynamically based on user input."""
                    return gr.update(display_mode=mode, background_color=color, line_numbers=lines, autoscroll=scroll)
                for control in controls:
                    control.change(fn=update_livelog_properties, inputs=controls, outputs=feature_logger)
        
            with gr.TabItem("Diffusion Pipeline Integration"):
                """Tab to monitor a real image generation process using Stable Diffusion with LiveLog."""
                gr.Markdown("### Use `LiveLog` to monitor a real image generation process.")
                with gr.Row():
                    with gr.Column(scale=3):
                        with gr.Group():
                            prompt = gr.Textbox(label="Enter your prompt", show_label=False, placeholder="A cinematic photo of a robot in a floral garden...", scale=8, container=False)
                            run_button = gr.Button("Generate", scale=1, variant="primary")
                        livelog_viewer = LiveLog(
                            label="Process Monitor",
                            height=350,
                            display_mode="full",
                            line_numbers=False                            
                        )
                    with gr.Column(scale=2):
                        result_gallery = gr.Gallery(label="Result", columns=1, show_label=False, height=500, min_width=768, preview=True)
                
                @spaces.GPU(duration=60)
                @livelog(
                    log_names=["diffusion_app"],
                    outputs_for_yield=[result_gallery, livelog_viewer, run_button],
                    log_output_index=1,
                    interactive_outputs_indices=[2],
                    result_output_index=0,
                    use_tracker=True,
                    tracker_mode="auto",
                    tracker_total_arg_name="total_steps",
                    tracker_description="Diffusion Steps",
                    tracker_rate_unit="it/s",
                    disable_console_logs="disable_console",
                    tracker_total_steps=10
                )
                def generate(prompt: str, total_steps: int = 10, disable_console: bool = False, rate_unit: str = 'it/s', **kwargs):
                    """
                    Generate an image using Stable Diffusion, logging progress and status to livelog_viewer.

                    Args:
                        prompt (str): Text prompt for image generation.
                        total_steps (int, optional): Number of diffusion steps. Defaults to 10.
                        disable_console (bool): If True, suppress console logs.
                        rate_unit (str): Unit for progress rate ('it/s' or 's/it').
                        **kwargs: Additional arguments passed to _run_diffusion_logic.

                    Returns:
                        List: Generated images.
                    """
                    kwargs["total_steps"] = total_steps
                    kwargs["rate_unit"] = rate_unit
                    kwargs["disable_console"] = disable_console
                    kwargs["log_name"] = "diffusion_app"
                    return _run_diffusion_logic(prompt, **kwargs)

                run_button.click(
                    fn=generate,
                    inputs=[prompt, gr.State(value=10), disable_console_checkbox, rate_unit],
                    outputs=[result_gallery, livelog_viewer, run_button]
                )
                prompt.submit(
                    fn=generate,
                    inputs=[prompt, gr.State(value=10), disable_console_checkbox, rate_unit],
                    outputs=[result_gallery, livelog_viewer, run_button]
                )
                livelog_viewer.clear(fn=lambda: None, outputs=[livelog_viewer])
                
    return demo

if __name__ == "__main__":
    """
    Launch the Gradio interface with logging configured and a queue size of 50.
    """
    configure_logging()
    demo = create_gradio_interface()
    demo.queue(max_size=50).launch(debug=True)