from celery import shared_task
from PIL import Image
import pyvips
import os
import numpy as np
import time
import threading
from celery.result import AsyncResult
import os
import json

from .image_utils import get_image_hash
from .paths import get_output_path, get_input_path
from .slices import get_tiff_scaler, prepare_slice_for_tiling
from .logger import LOGGER

# Thread-local storage for progress handlers
_progress_handlers = threading.local()

# Cache for TIFF metadata
_tiff_metadata_cache = {}

# Cache for slice information
_slice_cache = {}

# Configuration from environment variables
JPEG_QUALITY = os.getenv('JPEG_QUALITY', 80)
DZI_MIN_PIXELS = os.getenv('DZI_MIN_PIXELS', 10 ** float(os.getenv('DZI_MIN_PIXELS_EXP', 8.5)))
SLICE_MIN_PIXELS = os.getenv('SLICE_MIN_PIXELS', 10 ** float(os.getenv('SLICE_MIN_PIXELS_EXP', 7)))
DZI_TILE_SIZE = os.getenv('DZI_TILE_SIZE', 256)
DZI_OVERLAP = os.getenv('DZI_OVERLAP', 1)

# Progress thresholds from environment variables
PROGRESS_START = int(os.getenv('PROGRESS_START', 0))
PROGRESS_LOAD_IMAGE = int(os.getenv('PROGRESS_LOAD_IMAGE', 10))
PROGRESS_PROCESS_SLICE = int(os.getenv('PROGRESS_PROCESS_SLICE', 20))
PROGRESS_CONVERT_FORMAT = int(os.getenv('PROGRESS_CONVERT_FORMAT', 30))
PROGRESS_TILE_START = int(os.getenv('PROGRESS_TILE_START', 40))
PROGRESS_TILE_END = int(os.getenv('PROGRESS_TILE_END', 90))
PROGRESS_COMPLETE = int(os.getenv('PROGRESS_COMPLETE', 100))

class ProgressHandler:
    """Handler for pyvips progress updates that updates Celery task state."""
    def __init__(self, task, viewer_id):
        self.task = task
        self.viewer_id = viewer_id
        self.last_percent = PROGRESS_START
        self.session_timestamp = int(time.time())
        
    def __call__(self, percent):
        # pyvips progress goes from 0 to 100
        # Map it to our PROGRESS_TILE_START-PROGRESS_TILE_END range
        mapped_percent = PROGRESS_TILE_START + (percent * (PROGRESS_TILE_END - PROGRESS_TILE_START) / 100)
        if mapped_percent > self.last_percent:  # Only update if progress increased
            self.last_percent = mapped_percent
            self.task.update_state(
                state='PROGRESS',
                meta={
                    'current': mapped_percent,
                    'total': PROGRESS_COMPLETE,
                    'status': 'Generating and saving tiles...',
                    'stage': 'saving',
                    'fraction_complete': mapped_percent / PROGRESS_COMPLETE,
                    'viewer_id': self.viewer_id,
                    'session_timestamp': self.session_timestamp
                }
            )
        # Check for task cancellation
        check_task_cancelled(self.task)
        return True

def set_thread_progress_handler(handler):
    """Set the progress handler for the current thread."""
    _progress_handlers.handler = handler

def clear_thread_progress_handler():
    """Clear the progress handler for the current thread."""
    if hasattr(_progress_handlers, 'handler'):
        delattr(_progress_handlers, 'handler')

# Task state management helpers
def update_task_state(task, state, current, total, status, stage, viewer_id=None, **extra_meta):
    """Helper function to update task state with consistent format."""
    fraction = current / total if total > 0 else 0
    meta = {
        'current': current,
        'total': total,
        'status': status,
        'stage': stage,
        'fraction_complete': fraction,
        'viewer_id': viewer_id,
        'session_timestamp': extra_meta.get('session_timestamp', int(time.time()))
    }
    meta.update(extra_meta)
    task.update_state(state=state, meta=meta)

def check_task_cancelled(task):
    """Helper function to check if a task has been cancelled."""
    if task and hasattr(task, 'request') and not task.request.called_directly:
        task_result = AsyncResult(task.request.id)
        if task_result.state == 'REVOKED':
            LOGGER.info("Task was cancelled")
            raise Exception("Task cancelled by user")

def handle_task_error(task, error, viewer_id=None, is_cancellation=False):
    """Helper function to handle task errors with consistent format."""
    LOGGER.error(f"Error in task: {str(error)}")
    LOGGER.error("Stack trace:", exc_info=True)
    
    session_timestamp = int(time.time())
    try:
        # Try to get existing session timestamp from task
        task_meta = task.AsyncResult(task.request.id).info
        if isinstance(task_meta, dict) and 'session_timestamp' in task_meta:
            session_timestamp = task_meta['session_timestamp']
    except Exception:
        pass
    
    if is_cancellation or isinstance(error, Exception) and 'Task cancelled by user' in str(error):
        task.update_state(
            state='REVOKED',
            meta={
                'current': 0,
                'total': 100,
                'status': 'Task cancelled by user',
                'stage': 'cancelled',
                'fraction_complete': 0.0,
                'viewer_id': viewer_id,
                'session_timestamp': session_timestamp,
                'exc_type': 'TaskRevokedError',
                'exc_message': 'Task cancelled by user',
                'exc_module': 'celery.exceptions'
            }
        )
    else:
        task.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': str(error),
                'stage': 'error',
                'fraction_complete': 0.0,
                'viewer_id': viewer_id,
                'session_timestamp': session_timestamp,
                'exc_type': type(error).__name__,
                'exc_message': str(error),
                'exc_module': error.__class__.__module__
            }
        )

def generate_tiles(image_filename, hash, task=None, viewer_id=None, slice_index=None, scaler=None, tile_size=256):
    """
    Generate tiles from an input image using pyvips.
    
    Args:
        image_filename (str): Path to the input image file
        hash (str): Hash identifier for the output files
        task: Celery task instance for progress updates
        viewer_id: ID of the viewer this task belongs to
        slice_index (int, optional): Index for slice in multi-slice images
        scaler (float, optional): Scaling factor for slice images
        tile_size (int): Size of each tile in pixels (default: 256)
    
    Returns:
        str: Output filename if successful, None if failed
    """
    LOGGER.info(f"Starting tile generation for image: {image_filename} with hash: {hash}")
    LOGGER.info(f"Using tile size: {tile_size}")

    output_filename = f"{hash}"
    if slice_index is not None:
        output_filename += f"_{slice_index}"

    ready, _, _ = get_tiles_ready(output_filename)
    if ready:
        LOGGER.info(f"Tiles already exist for hash: {output_filename}")
        if task:
            update_task_state(
                task,
                state='SUCCESS',
                current=PROGRESS_COMPLETE,
                total=PROGRESS_COMPLETE,
                status='Tiles already exist',
                stage='finished',
                viewer_id=viewer_id,
                fraction_complete=1.0
            )
        return output_filename

    try:
        start_time = time.perf_counter()
        
        # Check if task is already cancelled
        check_task_cancelled(task)
        
        # Update progress: Starting
        if task:
            update_task_state(
                task,
                state='STARTED',
                current=PROGRESS_START,
                total=PROGRESS_COMPLETE,
                status='Loading image...',
                stage='loading',
                viewer_id=viewer_id,
                fraction_complete=PROGRESS_START / PROGRESS_COMPLETE
            )

        # Load the image
        LOGGER.info(f"Loading image: {image_filename}")
        pil_image = Image.open(os.path.join(get_input_path(), image_filename))
        
        check_task_cancelled(task)
        
        # Update progress: Image loaded
        if task:
            update_task_state(
                task,
                state='PROGRESS',
                current=PROGRESS_LOAD_IMAGE,
                total=PROGRESS_COMPLETE,
                status='Processing image...',
                stage='processing',
                viewer_id=viewer_id,
                fraction_complete=PROGRESS_LOAD_IMAGE / PROGRESS_COMPLETE
            )

        # Process the image - either prepare slice or use as is
        if slice_index is not None:
            assert scaler is not None, "Scaler must be provided for slice generation"
            pil_image = prepare_slice_for_tiling(
                pil_image, 
                slice_index, 
                scaler,
                task,
                viewer_id,
                PROGRESS_LOAD_IMAGE,
                PROGRESS_PROCESS_SLICE,
                # Get total slices from task info if available
                getattr(task, 'info', {}).get('total_slices') if task else None
            )
        else:
            # For non-slice images, just ensure RGB mode
            pil_image = force_image_mode(pil_image, 'RGB')

        check_task_cancelled(task)

        # Handle minimum size requirement - use different thresholds for slices vs regular images
        min_pixels = SLICE_MIN_PIXELS if slice_index is not None else DZI_MIN_PIXELS
        if pil_image.width * pil_image.height < min_pixels:
            LOGGER.info(f"Resizing image {'slice' if slice_index is not None else ''}...")
            aspect_ratio = pil_image.width / pil_image.height
            target_height = int(np.ceil(np.sqrt(min_pixels / aspect_ratio)))
            target_width = int(np.ceil(target_height * aspect_ratio))
            pil_image = pil_image.resize((target_width, target_height), Image.LANCZOS)
            LOGGER.info(f"Resized {'slice' if slice_index is not None else 'image'} to {target_width}x{target_height} (min_pixels={min_pixels}).")
        LOGGER.info(f"Image size: {pil_image.size}")

        check_task_cancelled(task)

        # Update progress: Starting conversion to pyvips
        if task:
            update_task_state(
                task,
                state='PROGRESS',
                current=PROGRESS_CONVERT_FORMAT,
                total=PROGRESS_COMPLETE,
                status='Converting image format...',
                stage='converting',
                viewer_id=viewer_id,
                fraction_complete=PROGRESS_CONVERT_FORMAT / PROGRESS_COMPLETE
            )

        # Convert to pyvips format
        LOGGER.info("Converting PIL image to numpy array")
        np_array = np.array(pil_image)
        LOGGER.info("Creating pyvips image from numpy array")
        image = pyvips.Image.new_from_array(np_array)
        LOGGER.info(f"Pyvips image size: {image.width}x{image.height}")

        check_task_cancelled(task)

        # Create output directory if it doesn't exist
        output_dir = get_output_path()
        os.makedirs(output_dir, mode=0o775, exist_ok=True)
        
        try:
            # For slice images, create a slices subfolder
            if slice_index is not None:
                # Use the base hash (without slice index) for the subfolder
                base_hash = hash
                slices_dir = os.path.join(output_dir, f"{base_hash}_slices")
                os.makedirs(slices_dir, mode=0o775, exist_ok=True)
                output_path = os.path.join(slices_dir, output_filename)
            else:
                output_path = os.path.join(output_dir, output_filename)
                
            LOGGER.info(f"Saving tiles to: {output_path}")

            # Update progress: Starting tile save
            if task:
                update_task_state(
                    task,
                    state='PROGRESS',
                    current=PROGRESS_TILE_START,
                    total=PROGRESS_COMPLETE,
                    status='Generating and saving tiles...',
                    stage='saving',
                    viewer_id=viewer_id,
                    fraction_complete=PROGRESS_TILE_START / PROGRESS_COMPLETE
                )

            # Enable progress monitoring
            image.set_progress(True)

            # Set up progress handler
            def eval_handler(image, progress=None):
                if progress is not None and task:
                    try:
                        progress_val = 0
                        if hasattr(progress, 'percent'):
                            progress_val = float(progress.percent)
                        elif hasattr(progress, 'run'):
                            progress_val = (float(progress.run) / float(progress.eta)) * 100 if progress.eta > 0 else 0
                        
                        mapped_progress = PROGRESS_TILE_START + (progress_val * (PROGRESS_TILE_END - PROGRESS_TILE_START) / 100)
                        fraction_complete = mapped_progress / PROGRESS_COMPLETE
                        
                        update_task_state(
                            task,
                            state='PROGRESS',
                            current=mapped_progress,
                            total=PROGRESS_COMPLETE,
                            status='Generating and saving tiles...',
                            stage='saving',
                            viewer_id=viewer_id,
                            fraction_complete=fraction_complete
                        )
                    except Exception as e:
                        LOGGER.error(f"Error in progress handler: {str(e)}")
                return 0

            # Connect progress handler
            image.signal_connect('eval', eval_handler)

            # Generate tiles
            image.dzsave(output_path, 
                        suffix=f'.jpg[Q={JPEG_QUALITY}]',
                        tile_size=DZI_TILE_SIZE,
                        overlap=DZI_OVERLAP)

            # Verify files were created
            dzi_file = f"{output_path}.dzi"
            tiles_dir = f"{output_path}_files"
            LOGGER.info(f"Verifying output files:")
            LOGGER.info(f"  - DZI file exists: {os.path.exists(dzi_file)}")
            LOGGER.info(f"  - Tiles dir exists: {os.path.exists(tiles_dir)}")

            check_task_cancelled(task)

            end_time = time.perf_counter()
            execution_time = end_time - start_time
            LOGGER.info(f"✅ Tile generation completed successfully in {execution_time:.2f} seconds")

            # Update progress: Complete
            if task:
                update_task_state(
                    task,
                    state='SUCCESS',
                    current=PROGRESS_COMPLETE,
                    total=PROGRESS_COMPLETE,
                    status='Complete!',
                    stage='finished',
                    viewer_id=viewer_id,
                    fraction_complete=1.0,
                    execution_time=execution_time
                )

            return output_filename
            
        except Exception as e:
            LOGGER.error(f"Error in dzsave operation: {str(e)}")
            LOGGER.error("Stack trace:", exc_info=True)
            if task:
                handle_task_error(task, e, viewer_id)
            raise

    except Exception as e:
        LOGGER.error(f"Error generating tiles: {str(e)}")
        LOGGER.error(f"Stack trace:", exc_info=True)
        if task:
            # Check if this was a cancellation
            task_result = AsyncResult(task.request.id)
            is_cancellation = task_result.state == 'REVOKED'
            handle_task_error(task, e, viewer_id, is_cancellation)
        return None


def force_image_mode(image, mode='RGB'):
    LOGGER.debug('🔍 Checking image channels...')
    if not image.mode == mode:
        LOGGER.debug(f'🛠️ Converting image to {mode}...')
        image = image.convert(mode)
        LOGGER.debug(f'✅ Image converted to {mode}.')
    return image

@shared_task(bind=True, name='backend.utilities.tiles.generate_tiles_task', queue='heavy')
def generate_tiles_task(self, image_filename, hash, viewer_id=None, slice_index=None, scaler=None):
    """Celery task wrapper for generate_tiles function."""
    LOGGER.debug(f"Starting generate_tiles_task for {image_filename} with hash {hash}")
    try:
        # Generate session timestamp for task tracking
        session_timestamp = int(time.time())
        
        # Determine total slices if this is a slice task
        total_slices = 1
        if slice_index is not None:
            # Try to get the total number of slices from metadata
            try:
                metadata = get_tiff_metadata(hash)
                if metadata:
                    total_slices = metadata.get('num_frames', 1)
                    
                    # Also get missing_slices if available
                    _, _, missing_slices = get_tiles_ready(hash)
            except Exception as e:
                LOGGER.warning(f"Could not get total slices from metadata: {e}")
                missing_slices = None
        
        # Initialize task state
        self.update_state(
            state='STARTED',
            meta={
                'current': 0,
                'total': 100,
                'status': 'Task starting...',
                'stage': 'initializing',
                'fraction_complete': 0.0,
                'viewer_id': viewer_id,
                'slice_index': slice_index,
                'total_slices': total_slices,
                'session_timestamp': session_timestamp,
                'missing_slices': missing_slices if 'missing_slices' in locals() else None
            }
        )

        # Call generate_tiles with task instance
        LOGGER.debug("Calling generate_tiles function")
        result = generate_tiles(
            image_filename=image_filename,
            hash=hash,
            task=self,
            viewer_id=viewer_id,
            slice_index=slice_index,
            scaler=scaler
        )
        log_result = result[:200] if len(result) > 200 else result
        LOGGER.debug(f"generate_tiles returned: {log_result}")

        # Return final success state
        return {
            'current': 100,
            'total': 100,
            'status': 'Task completed successfully',
            'stage': 'finished',
            'fraction_complete': 1.0,
            'viewer_id': viewer_id,
            'slice_index': slice_index,
            'total_slices': total_slices,
            'session_timestamp': session_timestamp,
            'missing_slices': missing_slices if 'missing_slices' in locals() else None,
            'result': result
        }
    except Exception as e:
        LOGGER.error(f"Error in generate_tiles_task: {str(e)}")
        LOGGER.error("Stack trace:", exc_info=True)
        handle_task_error(self, e, viewer_id)
        raise


def create_tiff_metadata(input_path, hash):
    """Create metadata file for a TIFF image containing frame count and scaler values.
    
    Args:
        input_path (str): Path to the input TIFF file
        hash (str): Hash identifier for the output files
        
    Returns:
        dict: Metadata containing num_frames and scaler values
    """
    LOGGER.info(f"Creating metadata for TIFF: {input_path}")
    
    with Image.open(input_path) as img:
        num_frames = img.n_frames
        scaler = get_tiff_scaler(img, is_image=True)
    
    metadata = {
        'num_frames': num_frames,
        'scaler': scaler,
        'created_at': time.time(),
        'task_ids': [],  # Track task IDs for resumption
        'processing_started': None,  # Will be set when processing starts
        'filename': os.path.basename(input_path)  # Store original filename
    }
    
    # Create output directory if it doesn't exist
    output_dir = get_output_path()
    os.makedirs(output_dir, mode=0o775, exist_ok=True)
    
    # Create hash_slices directory if it doesn't exist
    hash_dir = os.path.join(output_dir, f"{hash}_slices")
    os.makedirs(hash_dir, mode=0o775, exist_ok=True)
    
    # Save metadata file
    metadata_path = os.path.join(hash_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    
    # Cache the metadata
    _tiff_metadata_cache[hash] = metadata
    
    LOGGER.info(f"Created metadata file at {metadata_path}")
    return metadata

def get_tiff_metadata(hash):
    """Get metadata for a TIFF image from cache or file.
    
    Args:
        hash (str): Hash identifier for the files
        
    Returns:
        dict: Metadata containing num_frames and scaler values, or None if not found
    """
    # Check cache first
    if hash in _tiff_metadata_cache:
        # Verify metadata file still exists
        metadata_path = os.path.join(get_output_path(), f"{hash}_slices", "metadata.json")
        if not os.path.exists(metadata_path):
            # Clear from cache if file is missing
            LOGGER.debug(f"Metadata file missing, clearing from cache: {metadata_path}")
            _tiff_metadata_cache.pop(hash, None)
            return None
        return _tiff_metadata_cache[hash]
    
    # Try to load from file
    metadata_path = os.path.join(get_output_path(), f"{hash}_slices", "metadata.json")
    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
            _tiff_metadata_cache[hash] = metadata
            return metadata
    except (FileNotFoundError, json.JSONDecodeError) as e:
        LOGGER.debug(f"Could not load metadata file: {e}")
        return None

def start_tile_generation(filename, viewer_id, is_slice=False):
    try:
        input_path = get_image_path(filename)
        LOGGER.info(f"Full input path: {input_path}")
        
        # Check if file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        hash = get_image_hash(input_path)
        LOGGER.info(f"Generated hash: {hash} for file: {filename}")
        
        # Initialize task_ids list
        task_ids = []
        
        # Create metadata file if this is a multi-frame TIFF
        if is_slice:
            try:
                metadata = get_tiff_metadata(hash)
                if not metadata:
                    metadata = create_tiff_metadata(input_path, hash)
                num_slices = metadata['num_frames']
                scaler = tuple(metadata['scaler'])  # Convert from list to tuple
                LOGGER.info(f"Using metadata - num_slices: {num_slices}, scaler: {scaler}")
                
                # Check which slices need to be generated
                ready, slice_files, missing_slices = get_tiles_ready(hash)
                if ready:
                    LOGGER.info("All slices already exist")
                    return hash, slice_files
                
                # Only create tasks for missing slices
                if missing_slices:
                    LOGGER.info(f"Creating tasks for {len(missing_slices)} missing slices")
                    
                    # Update metadata with processing start time if not already set
                    if not metadata.get('processing_started'):
                        metadata['processing_started'] = time.time()
                        metadata['task_ids'] = []  # Reset task IDs if starting fresh
                    
                    for slice_index in missing_slices:
                        LOGGER.info(f"Creating task for slice {slice_index}")
                        task = generate_tiles_task.delay(filename, hash, viewer_id, slice_index, scaler)
                        task_ids.append(task.id)
                        if task.id not in metadata['task_ids']:
                            metadata['task_ids'].append(task.id)
                    
                    # Save updated metadata
                    metadata_path = os.path.join(get_output_path(), f"{hash}_slices", "metadata.json")
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f)
                    
                    # Update cache
                    _tiff_metadata_cache[hash] = metadata
                    
                    # Return existing slice files along with task IDs
                    return hash, task_ids
                else:
                    # This shouldn't happen since ready would be True if no missing slices
                    LOGGER.warning("No missing slices but tiles not ready - possible race condition")
                    return hash, []
            except Exception as e:
                LOGGER.error(f"Error processing multi-frame TIFF: {e}")
                LOGGER.error("Stack trace:", exc_info=True)
                raise
        else:
            # Check if single image tiles exist
            ready, slice_files, _ = get_tiles_ready(hash)
            if ready:
                LOGGER.info("Tiles already exist")
                return hash, []
                
            LOGGER.info("Creating task for single image")
            LOGGER.debug(f"Calling generate_tiles_task.delay with args: filename={filename}, hash={hash}, viewer_id={viewer_id}")
            task = generate_tiles_task.delay(filename, hash, viewer_id)
            LOGGER.debug(f"Task created with ID: {task.id}")
            task_ids.append(task.id)
        
        LOGGER.info(f"Tile generation task(s) submitted successfully. Created {len(task_ids)} tasks.")
        return hash, task_ids
    except Exception as e:
        LOGGER.error(f"Error in start_tile_generation: {e}")
        LOGGER.error("Stack trace:", exc_info=True)
        raise


def get_image_path(filename):
    LOGGER.debug(f"Getting full path for file: {filename}")
    full_path = os.path.join(get_input_path(), filename)
    LOGGER.debug(f"Full path resolved to: {full_path}")
    return full_path


def get_tiles_path(hash):
    LOGGER.debug(f"Getting tiles path for hash: {hash}")
    tiles_path = os.path.join(get_output_path(), hash)
    LOGGER.debug(f"Tiles path resolved to: {tiles_path}")
    return tiles_path


def get_file_ready(filename):
    """Check if a file exists in the output directory.
    
    Args:
        filename (str): Name of the file to check
        
    Returns:
        bool: True if the file exists, False otherwise
    """
    LOGGER.debug(f"Checking if file exists: {filename}")
    
    # Handle both absolute and relative paths
    if os.path.isabs(filename):
        file_path = filename
    else:
        file_path = os.path.join(get_output_path(), filename)
    
    # Normalize path to handle ./ and ../
    file_path = os.path.normpath(file_path)
    LOGGER.debug(f"Normalized file path: {file_path}")
    
    exists = os.path.exists(file_path)
    LOGGER.debug(f"File exists: {exists}")
    
    return exists


def mark_slice_as_ready(tiff_hash, slice_number):
    tiff_data = _tiff_metadata_cache.get(tiff_hash, {})
    tiff_data['slice_numbers'].add(slice_number)
    _tiff_metadata_cache[tiff_hash] = tiff_data


def get_slice_in_cache(tiff_hash, slice_number):
    tiff_data = _tiff_metadata_cache.get(tiff_hash, {})
    return slice_number in tiff_data.get('slice_numbers', [])


def _is_tiles_directory_populated(tiles_dir_path):
    """Check if a _files directory contains actual tile zoom level directories.
    
    Args:
        tiles_dir_path: Path to the _files directory
        
    Returns:
        bool: True if directory contains at least one zoom level directory
    """
    try:
        tile_contents = os.listdir(tiles_dir_path)
        # Check if there's at least one zoom level directory (e.g., "0", "1", etc.)
        return any(item.isdigit() and os.path.isdir(os.path.join(tiles_dir_path, item)) 
                  for item in tile_contents)
    except (OSError, PermissionError) as e:
        LOGGER.warning(f"Error checking tiles directory contents at {tiles_dir_path}: {e}")
        return False


def get_slices_ready(hash):
    LOGGER.debug(f"Checking if tiles are ready for hash: {hash}")
    output_path = get_output_path()
    LOGGER.info(f"Output path: {output_path}")
    
    # Check metadata file for slice information
    metadata = get_tiff_metadata(hash)
    is_slice = metadata['num_frames'] > 1
    assert is_slice, "Expected a slice set"
    expected_slices = metadata['num_frames']
    LOGGER.info(f"Using metadata - is_slice: {is_slice}, expected_slices: {expected_slices}.")
    
    if is_slice:
        # For slice sets, look in the slices subfolder
        slices_dir = os.path.join(output_path, f"{hash}_slices")
        if not os.path.exists(slices_dir):
            LOGGER.debug(f"Slices directory does not exist: {slices_dir}")
            return False, [], list(range(expected_slices))
            
        all_files = os.listdir(slices_dir)
        
        # Quick check: if directory is empty or has only metadata, no slices are ready
        if len(all_files) <= 1:  # Only metadata.json or empty
            LOGGER.debug("Slices directory is empty or has no slice files")
            return False, [], list(range(expected_slices))
        
        all_files_set = set(all_files)  # Convert to set for O(1) lookups
        
        # Find slice files - look for both .dzi files and their corresponding _files directories
        slice_files = []
        slice_numbers = set()
        
        # First pass: just count potential .dzi files
        potential_dzi_files = [f for f in all_files if f.startswith(hash) and f.endswith('.dzi')]
        
        # If we have few potential files or expected slices is large, skip expensive population checks
        # This prevents timeout on initial upload of large TIFF files
        skip_population_check = len(potential_dzi_files) < 10 or expected_slices > 500
        
        for f in potential_dzi_files:
            # Check if corresponding _files directory exists in the set
            files_dir_name = f[:-4] + '_files'  # Replace .dzi with _files
            if files_dir_name in all_files_set:
                # Only do expensive population check for smaller slice sets or when we have many complete slices
                if not skip_population_check:
                    files_dir_path = os.path.join(slices_dir, files_dir_name)
                    if not _is_tiles_directory_populated(files_dir_path):
                        LOGGER.debug(f"Slice {f} _files directory exists but not yet populated")
                        continue
                
                slice_files.append(f)
                try:
                    # Extract number from filename (e.g. hash_5.dzi -> 5)
                    slice_num = int(f[len(hash)+1:-4])
                    slice_numbers.add(slice_num)
                except (ValueError, IndexError):
                    LOGGER.warning(f"Invalid slice filename format: {f}")
                    continue
        
        if not slice_numbers:
            LOGGER.debug("No valid slice numbers found")
            return False, [], list(range(expected_slices))
        
        # For slices, we expect numbers to start at 0
        min_slice = min(slice_numbers)
        if min_slice != 0:
            LOGGER.debug(f"Slice numbers don't start at 0, got min_slice={min_slice}")
            return False, [], list(range(expected_slices))
        
        # Find missing slices
        expected_slices_set = set(range(expected_slices))
        missing_slices = sorted(list(expected_slices_set - slice_numbers))
        
        # If we have missing slices, return them
        if missing_slices:
            LOGGER.debug(f"Missing slices: {len(missing_slices) if len(missing_slices) > 10 else missing_slices}")
            return False, [], missing_slices
            
        # Sort files by their numeric index
        def get_slice_index(filename):
            try:
                # Extract number between underscore and .dzi
                return int(filename[len(hash)+1:-4])
            except (ValueError, IndexError):
                return -1  # Invalid files will be sorted to the start
        
        slice_files.sort(key=get_slice_index)
        
        # Return full paths relative to output directory
        slice_paths = [os.path.join(f"{hash}_slices", f) for f in slice_files]
        return True, slice_paths, []


def get_tiles_ready(hash, slice_number=None):
    """Check if DZI tiles are ready for a given hash.
    
    Args:
        hash (str): Hash identifier for the tiles (may include slice number like hash_123)
        slice_number (int, optional): Specific slice number to check
        
    Returns:
        tuple: (bool, list, list) - (True if tiles are ready, list of slice files if applicable, list of missing slice indices)
    """
    LOGGER.debug(f"Checking if tiles are ready for hash: {hash}")
    output_path = get_output_path()
    LOGGER.info(f"Output path: {output_path}")
    
    # Check if hash includes a slice number (format: basehash_slicenum)
    if '_' in hash and slice_number is None:
        try:
            base_hash, slice_str = hash.rsplit('_', 1)
            slice_number = int(slice_str)
            LOGGER.debug(f"Detected slice-specific hash: base={base_hash}, slice={slice_number}")
            # Check just this specific slice
            slices_dir = os.path.join(output_path, f"{base_hash}_slices")
            dzi_file = os.path.join(slices_dir, f"{hash}.dzi")
            tiles_dir = os.path.join(slices_dir, f"{hash}_files")
            
            dzi_exists = os.path.exists(dzi_file)
            tiles_exist = os.path.exists(tiles_dir)
            tiles_populated = tiles_exist and _is_tiles_directory_populated(tiles_dir)
            
            ready = dzi_exists and tiles_exist and tiles_populated
            LOGGER.debug(f"Single slice {slice_number} ready: {ready}")
            return ready, [f"{base_hash}_slices/{hash}.dzi"] if ready else [], []
        except (ValueError, IndexError):
            LOGGER.debug(f"Hash contains underscore but not a valid slice format: {hash}")
            # Fall through to normal checking
    
    # Check if this is a slice set by looking for metadata (base hash only)
    base_hash = hash.rsplit('_', 1)[0] if '_' in hash else hash
    metadata = get_tiff_metadata(base_hash)
    if metadata and metadata.get('num_frames', 1) > 1:
        # This is a slice set, delegate to get_slices_ready
        LOGGER.debug(f"Hash {hash} is a slice set, delegating to get_slices_ready")
        return get_slices_ready(base_hash)
    
    # For single files, check for .dzi and _files
    dzi_file = os.path.join(output_path, f"{hash}.dzi")
    tiles_dir = os.path.join(output_path, f"{hash}_files")
    
    dzi_exists = os.path.exists(dzi_file)
    tiles_exist = os.path.exists(tiles_dir)
    
    LOGGER.debug(f"DZI file exists: {dzi_exists}")
    LOGGER.debug(f"Tiles directory exists: {tiles_exist}")
    
    tiles_populated = tiles_exist and _is_tiles_directory_populated(tiles_dir)
    
    ready = dzi_exists and tiles_exist and tiles_populated
    LOGGER.debug(f"Tiles ready: {ready}")
    return ready, [f"{hash}.dzi"] if ready else [], []
