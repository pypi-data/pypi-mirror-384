import json
import numpy as np
import os
from PIL import Image
import time

from .paths import get_input_path, get_output_path
from .logger import LOGGER

# Cache for TIFF scale values
_tiff_scale_cache = {}

def get_tiff_scaler(tiff_path, is_image=False):
    """Get the min and max pixel values across all layers of a TIFF image.
    Results are cached based on the file path or image id.
    Returns a tuple (min_val, max_val) that can be used for scaling.
    """
    # Use the tiff_path as cache key for file inputs
    cache_key = id(tiff_path) if is_image else tiff_path
    
    if cache_key in _tiff_scale_cache:
        LOGGER.info('📎 Using cached scale values')
        return _tiff_scale_cache[cache_key]
    
    LOGGER.info('📂 Opening the TIFF image...')
    if is_image:
        im = tiff_path
    else:
        im = Image.open(tiff_path)
    
    LOGGER.info('🔢 Getting the number of layers...')
    n_layers = im.n_frames
    LOGGER.debug(f'🔢 Number of layers: {n_layers}')
    
    min_val = np.inf
    max_val = -np.inf

    LOGGER.info('🔄 Finding min and max pixel values...')
    for i in range(n_layers):
        if not i % 50: LOGGER.info(f'🔄 Processing layer {i+1}/{n_layers}...')
        im.seek(i)
        layer_array = np.array(im)
        # Convert to float64 before computing min/max to handle all numeric types
        layer_array = layer_array.astype(np.float64, copy=False)
        min_val = np.minimum(min_val, np.min(layer_array))
        max_val = np.maximum(max_val, np.max(layer_array))
    
    LOGGER.debug(f'📊 Min value: {min_val}, Max value: {max_val}')
    
    # Cache the results as Python floats for consistent serialization
    scaler = (float(min_val), float(max_val))
    _tiff_scale_cache[cache_key] = scaler
    LOGGER.info('💾 Cached scale values')
    
    return scaler

def clear_tiff_scale_cache():
    """Clear the TIFF scale cache."""
    _tiff_scale_cache.clear()

def get_slice_image(tiff_image, layer_index, scaler):
    """Get a slice from a TIFF image, properly scaled and flipped.
    
    Args:
        tiff_image: PIL Image object
        layer_index: Index of the layer to extract
        scaler: Tuple of (min_val, max_val) for scaling the pixel values
        
    Returns:
        PIL Image object of the processed slice
    """
    min_val, max_val = scaler
    LOGGER.info(f'🔄 Getting slice {layer_index} with scaler min={min_val}, max={max_val}...')
    tiff_image.seek(layer_index)

    LOGGER.debug('🔄 Converting current layer to a numpy array...')
    pixel_values = np.array(tiff_image)
    original_dtype = pixel_values.dtype
    LOGGER.info(f'📊 Original pixel values - shape: {pixel_values.shape}, dtype: {original_dtype}')
    LOGGER.info(f'📊 Original pixel values - range: [{np.min(pixel_values)}, {np.max(pixel_values)}]')
    LOGGER.info(f'📊 Original pixel values - mean: {np.mean(pixel_values):.2f}, std: {np.std(pixel_values):.2f}')

    LOGGER.debug('🔄 Scaling pixel values...')
    # Convert everything to float64 for precise scaling
    pixel_values = pixel_values.astype(np.float64, copy=False)
    min_val = np.float64(min_val)
    max_val = np.float64(max_val)
    
    # Scale to 0-1 range based on global min/max
    scaled_values = (pixel_values - min_val) / (max_val - min_val)
    LOGGER.info(f'📊 After min-max scaling - range: [{np.min(scaled_values)}, {np.max(scaled_values)}]')
    LOGGER.info(f'📊 After min-max scaling - mean: {np.mean(scaled_values):.2f}, std: {np.std(scaled_values):.2f}')
    
    # Ensure values are clamped to 0-1 range
    scaled_values = np.clip(scaled_values, 0, 1)
    LOGGER.info(f'📊 After clipping - range: [{np.min(scaled_values)}, {np.max(scaled_values)}]')
    
    # Scale to 0-255 range and convert to uint8
    scaled_values = np.round(scaled_values * 255).astype(np.uint8)
    LOGGER.info(f'📊 Final uint8 values - range: [{np.min(scaled_values)}, {np.max(scaled_values)}]')
    LOGGER.info(f'📊 Final uint8 values - mean: {np.mean(scaled_values):.2f}, std: {np.std(scaled_values):.2f}')

    # Flip the array horizontally before converting to image
    scaled_values = np.fliplr(scaled_values)

    LOGGER.debug('🔄 Converting scaled values to image...')
    slice_image = Image.fromarray(scaled_values)
    
    return slice_image

def prepare_slice_for_tiling(pil_image, slice_index, scaler, task=None, viewer_id=None, progress_start=0, progress_end=100, total_slices=None):
    """Prepare a slice from a multi-slice image for tiling.
    
    Args:
        pil_image: PIL Image object of the multi-slice image
        slice_index: Index of the slice to process
        scaler: Tuple of (min_val, max_val) for scaling
        task: Optional Celery task for progress updates
        viewer_id: Optional viewer ID for progress updates
        progress_start: Start of progress range (0-100)
        progress_end: End of progress range (0-100)
        total_slices: Optional total number of slices for progress calculation
        
    Returns:
        PIL Image object ready for tiling
    """
    LOGGER.info(f'🔄 Preparing slice {slice_index} for tiling...')
    
    # Update progress if task is provided
    if task:
        update_slice_progress(
            task, 
            progress_start, 
            'Processing slice...', 
            viewer_id, 
            slice_index, 
            total_slices
        )
    
    # Get and process the slice
    slice_image = get_slice_image(pil_image, slice_index, scaler)
    
    # Update progress
    if task:
        update_slice_progress(
            task, 
            (progress_start + progress_end) / 2, 
            'Converting to RGB...', 
            viewer_id, 
            slice_index, 
            total_slices
        )
    
    # Convert to RGB mode
    if slice_image.mode != 'RGB':
        slice_image = slice_image.convert('RGB')
    
    # Final progress update
    if task:
        update_slice_progress(
            task, 
            progress_end, 
            'Slice preparation complete', 
            viewer_id, 
            slice_index, 
            total_slices
        )
    
    return slice_image

def update_slice_progress(task, current_progress, status_message, viewer_id=None, slice_index=None, total_slices=None):
    """Update the progress of a slice processing task.
    
    Args:
        task: Celery task instance
        current_progress: Current progress value (0-100)
        status_message: Status message to display
        viewer_id: Optional viewer ID
        slice_index: Optional slice index
        total_slices: Optional total number of slices
    """
    if not task:
        return
        
    # Get slice_index and total_slices from task state if not provided
    if slice_index is None or total_slices is None:
        try:
            task_state = task.AsyncResult(task.request.id).state
            task_info = task.AsyncResult(task.request.id).info
            if isinstance(task_info, dict):
                slice_index = task_info.get('slice_index', slice_index)
                total_slices = task_info.get('total_slices', total_slices)
        except Exception as e:
            LOGGER.debug(f"Error getting task info: {e}")
    
    # Create progress update with slice information if available
    progress_meta = {
        'current': current_progress,
        'total': 100,
        'status': status_message,
        'stage': 'processing',
        'fraction_complete': current_progress / 100,
        'viewer_id': viewer_id,
        'session_timestamp': int(time.time())  # Add timestamp for tracking session
    }
    
    # Add slice information if available
    if slice_index is not None:
        progress_meta['slice_index'] = slice_index
    if total_slices is not None:
        progress_meta['total_slices'] = total_slices
        
    # If we have both slice index and total slices, calculate overall progress
    if slice_index is not None and total_slices is not None and total_slices > 0:
        # Overall progress combines slice index and progress within the slice
        slice_progress = current_progress / 100
        overall_progress = ((slice_index + slice_progress) / total_slices) * 100
        progress_meta['overall_progress'] = overall_progress
        
        # Update status message with slice information
        if 'slices' not in status_message.lower():
            progress_meta['status'] = f"Processing slice {slice_index+1} of {total_slices}: {status_message}"
    
    # Add missing slices information if available from task state
    try:
        task_info = task.AsyncResult(task.request.id).info
        if isinstance(task_info, dict) and 'missing_slices' in task_info:
            progress_meta['missing_slices'] = task_info['missing_slices']
    except Exception as e:
        LOGGER.debug(f"Error getting missing slices info: {e}")
    
    task.update_state(
        state='PROGRESS',
        meta=progress_meta
    )

num_slices_cache = {}
def get_tiff_layers(slices_key):
    """Get the number of layers (frames) in a TIFF file.
    
    Args:
        slices_key (str): The hash identifier for the TIFF file
        
    Returns:
        int: Number of frames in the TIFF file
    """
    LOGGER.debug(f'🔍 Checking cache for {slices_key = }...')
    if slices_key in num_slices_cache:
        LOGGER.info('✅ Found in cache.')
        return num_slices_cache[slices_key]
    
    # Extract base hash (remove slice index if present)
    base_hash = slices_key.rsplit('_', 1)[0] if '_' in slices_key else slices_key
    
    # Get metadata file path
    metadata_path = os.path.join(get_output_path(), f"{base_hash}_slices", "metadata.json")
    
    try:
        # Try to get number of frames from metadata file
        with open(metadata_path) as f:
            metadata = json.load(f)
            num_frames = metadata['num_frames']
            num_slices_cache[slices_key] = num_frames
            return num_frames
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        LOGGER.debug(f"Could not load metadata file: {e}")
        
        # If metadata not available, try to find the original file
        input_dir = get_input_path()
        for ext in ['.tif', '.tiff']:
            input_path = os.path.join(input_dir, f"{base_hash}{ext}")
            if os.path.exists(input_path):
                with Image.open(input_path) as img:
                    num_frames = img.n_frames
                    num_slices_cache[slices_key] = num_frames
                    return num_frames
        
        # If we get here, we couldn't find the file
        raise FileNotFoundError(f"Could not find TIFF file for hash {base_hash}")
