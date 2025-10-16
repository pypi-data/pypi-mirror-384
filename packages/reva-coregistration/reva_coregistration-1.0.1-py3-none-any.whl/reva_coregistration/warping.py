from .coregistration  import calculate_coregistration
from .image_utils     import get_upscaled_image_size, get_image_hash
from .paths           import get_input_path, get_output_path
from .globals         import *
from .transformations import *
from .landmarks       import *
from celery import shared_task
from scipy.ndimage import map_coordinates
from PIL import Image
import dask.array as da
import json
import numpy as np
import os
import time


WARP_PHOTO_TIMEOUT = int(os.getenv('WARP_PHOTO_TIMEOUT', 1440))  # 24 hours in minutes
IMAGE_ENDPOINT = os.getenv('IMAGE_ENDPOINT')
TILES_ENDPOINT  = os.getenv('TILES_ENDPOINT' )
LOGGER.debug(f'{IMAGE_ENDPOINT = }, {TILES_ENDPOINT = }')

# Load progress thresholds from environment
PROGRESS_START = int(os.getenv('PROGRESS_START', 0))
PROGRESS_LOAD_IMAGE = int(os.getenv('PROGRESS_LOAD_IMAGE', 10))
PROGRESS_PREPROCESSING = int(os.getenv('PROGRESS_PREPROCESSING', 20))
PROGRESS_RESIZING = int(os.getenv('PROGRESS_RESIZING', 30))
PROGRESS_LANDMARKS = int(os.getenv('PROGRESS_LANDMARKS', 40))
PROGRESS_TRANSFORM = int(os.getenv('PROGRESS_TRANSFORM', 50))
PROGRESS_WARPING = int(os.getenv('PROGRESS_WARPING', 60))
PROGRESS_SAVING = int(os.getenv('PROGRESS_SAVING', 90))
PROGRESS_COMPLETE = int(os.getenv('PROGRESS_COMPLETE', 100))


def do_warp_image(source_image, target_image_h: int, target_image_w: int, transformation, apply_nonlinear_warping: bool = True):
    '''
    This will output an image that is the same shape as (target_image_h, target_image_w),
    containing the transformed source image in the target image's frame of reference.
    
    Parameters:
    source_image (np.array): The source image to be transformed
    target_image_h (int): The height of the target image to be used as reference
    target_image_w (int): The width of the target image to be used as reference
    transformation (dict): The transformation to be applied

    Returns:
    np.array: The transformed source image, of the same shape as (target_image_h, target_image_w)
    '''
    LOGGER.debug(f'🔄 Warping image. {apply_nonlinear_warping = }')
    target_image = np.zeros((target_image_h, target_image_w, source_image.shape[2]), dtype=source_image.dtype)
    affine_matrix = transformation['affine_matrix_from_target_to_src']
    rbf_x = transformation['rbf_x_target_to_affine']
    rbf_y = transformation['rbf_y_target_to_affine']
    
    def _transform_block(block, block_info=None):
        block_offset = (block_info[0]['array-location'][0][0], block_info[0]['array-location'][1][0])  # (y, x) offset for this block
        block_shape = block.shape

        target_block_coords = np.indices(block_shape[:2])
        target_block_coords = target_block_coords.reshape((2, -1))  
        target_block_coords[0, :] += block_offset[0] # y
        target_block_coords[1, :] += block_offset[1] # x
        
        inverse_tps_x = target_block_coords[1, :]
        inverse_tps_y = target_block_coords[0, :]
        LOGGER.debug(f'🔄 Applying nonlinear warping: {apply_nonlinear_warping = }')
        if apply_nonlinear_warping:
            inverse_tps_x = rbf_x(target_block_coords[1, :], target_block_coords[0, :])
            inverse_tps_y = rbf_y(target_block_coords[1, :], target_block_coords[0, :])

        coords_for_dot_product = np.vstack((inverse_tps_x, inverse_tps_y, np.ones(target_block_coords.shape[1])))
        source_coords = np.dot(affine_matrix, coords_for_dot_product)
        source_coords = np.array([source_coords[1], source_coords[0]]) # Swap the rows back to (y, x) form
        source_coords = source_coords.reshape((2,) + block_shape[:2])

        if len(block_shape) == 3:  # multi-channel image
            registered_block = np.dstack([map_coordinates(source_image[:, :, i], source_coords, order=1) for i in range(block_shape[2])])
        else:  # grayscale image
            registered_block = map_coordinates(source_image, source_coords, order=1)
        
        assert registered_block.shape == block.shape, f'🚨 Shapes do not match: ({registered_block.shape = }) != ({block.shape = }). ({source_coords.shape = }, {block_shape = })'
        return registered_block

    LOGGER.info(f'🔄 Converting image to Dask array...')
    LOGGER.debug(f'📝 {target_image.shape = }')
    dask_source = da.from_array(
        target_image,
        chunks=(
            DASK_BLOCK_SIZE[0] + DASK_OVERLAP_PIXELS,
            DASK_BLOCK_SIZE[1] + DASK_OVERLAP_PIXELS,
            -1
        )
    )
    LOGGER.info(f'✅ Source image converted to Dask array.')

    LOGGER.info(f'🔄 Preparing chunks of target image...')
    dask_registered_image = dask_source.map_blocks(_transform_block, dtype=np.float32)
    LOGGER.info(f'✅ Chunks of target image prepared.')
    
    LOGGER.info(f'🔄 Applying transformation and warping image...')
    dask_registered_image = dask_registered_image.compute()
    LOGGER.info(f'✅ Transformation applied and image warped.')
    
    return np.array(dask_registered_image, dtype=source_image.dtype)


def get_upscale_factor(image_name: str):
    hash = get_image_hash(os.path.join(get_input_path(), f'{image_name}'))
    LOGGER.debug(f'📏 {hash = }')

    LOGGER.info(f'🔍 Retrieving upscaled image size for {image_name}...')
    upscaled_image_size = get_upscaled_image_size(hash)
    LOGGER.debug(f'📏 Upscaled image size: {upscaled_image_size = }.')

    LOGGER.info('🔍 Loading local image...')
    image_path = os.path.join(get_input_path(), f'{image_name}')
    image = Image.open(image_path)

    LOGGER.debug(f'📏 Original image size: {image.size}.')
    upscale_factor = upscaled_image_size[0] / image.size[0]
    LOGGER.debug(f'📈 Upscale factor: {upscale_factor = }')
    return upscale_factor, image.size, image


def cleanup_old_warped_images(current_image_path=None):
    """Clean up warped images older than 1 hour, except for the currently viewed image"""
    current_time = time.time()
    # Use os.path.join and normpath to ensure consistent path handling
    # warped_pattern = os.path.normpath(os.path.join(get_output_path(), '.w', '*.jpg'))
    # for file_path in glob.glob(warped_pattern):
    for file_name in os.listdir(os.path.join(get_output_path(), '.w')):
        file_path = os.path.join(get_output_path(), '.w', file_name)
        if not file_path.endswith('.jpg'):
            continue

        LOGGER.debug(f'📝 {file_path = }, {current_image_path = }')
        # Skip the current image if specified
        if current_image_path and file_path == current_image_path:
            continue
            
        file_age = current_time - os.path.getmtime(file_path)
        LOGGER.debug(f'📝 {file_path = }, {file_age = }, {WARP_PHOTO_TIMEOUT * 60 = }')
        if file_age > WARP_PHOTO_TIMEOUT * 60:  # Convert minutes to seconds
            os.remove(file_path)
            LOGGER.info(f'🗑️ Removed old warped image: {file_path}')

def get_downscale_factors(photo_image: Image.Image, microct_image: Image.Image):
    # Calculate initial dimensions
    photo_pixels = photo_image.size[0] * photo_image.size[1]
    microct_pixels = microct_image.size[0] * microct_image.size[1]
    # Determine if we need to downscale either image to MAX_WARPED_PIXELS
    photo_downscale = np.sqrt(max(1, photo_pixels / MAX_WARPED_PIXELS))
    microct_downscale = np.sqrt(max(1, microct_pixels / MAX_WARPED_PIXELS))
    LOGGER.debug(f'📏 {photo_downscale = }, {microct_downscale = }')

    return photo_downscale, microct_downscale

def get_original_dimensions(photo_image: Image.Image, microct_image: Image.Image):
    original_photo_w = photo_image.size[0]
    original_photo_h = photo_image.size[1]
    original_microct_w = microct_image.size[0]
    original_microct_h = microct_image.size[1]
    return original_photo_w, original_photo_h, original_microct_w, original_microct_h

def get_downscale_dimensions(original_photo_w: int, original_photo_h: int, original_microct_w: int, original_microct_h: int, photo_downscale: float, microct_downscale: float):    
    # Calculate new dimensions
    new_photo_w = int(original_photo_w / photo_downscale)
    new_photo_h = int(original_photo_h / photo_downscale)
    new_microct_w = int(original_microct_w / microct_downscale)
    new_microct_h = int(original_microct_h / microct_downscale)    
    LOGGER.debug(f'📏 {new_photo_w = }, {new_photo_h = }, {new_microct_w = }, {new_microct_h = }')
    LOGGER.info(f'Source photo dimensions: {(original_photo_w, original_photo_h)} -> {(new_photo_w, new_photo_h)}')
    LOGGER.info(f'Target microCT dimensions: {(original_microct_w, original_microct_h)} -> {(new_microct_w, new_microct_h)}')

    return new_photo_w, new_photo_h, new_microct_w, new_microct_h


def downscale_images(photo_image: Image.Image, microct_image: Image.Image, photo_downscale: float, microct_downscale: float, new_photo_w: int, new_photo_h: int, new_microct_w: int, new_microct_h: int):
    if photo_downscale > 1:
        photo_image = photo_image.resize((new_photo_w, new_photo_h), Image.Resampling.LANCZOS)
        LOGGER.info(f'Downscaled photo by factor of {photo_downscale:.2f}')
        
    if microct_downscale > 1:
        microct_image = microct_image.resize((new_microct_w, new_microct_h), Image.Resampling.LANCZOS)
        LOGGER.info(f'Downscaled microCT by factor of {microct_downscale:.2f}')

    return photo_image, microct_image

def load_and_scale_landmarks(landmarks: str, original_photo_w: int, original_photo_h: int, original_microct_w: int, original_microct_h: int, photo_downscale: float, microct_downscale: float):
    # Load and scale landmarks
    LOGGER.debug(f'📏 {original_photo_w = }, {original_photo_h = }, {original_microct_w = }, {original_microct_h = }')
    target_landmarks, source_landmarks = load_landmarks(landmarks, original_microct_w, original_microct_h, original_photo_w, original_photo_h)
    LOGGER.debug(f'📏 {landmarks = }, {target_landmarks = }, {source_landmarks = }')
    
    # Scale landmarks to match the downscaled images
    source_landmarks /= photo_downscale
    target_landmarks /= microct_downscale

    return source_landmarks, target_landmarks

def scale_transformation(transformation, target_w, target_h):
    # Calculate scaling factors
    scale_x = target_w / transformation['target_image_width']
    scale_y = target_h / transformation['target_image_height']

    # Scale the transformation
    scaled_transformation = transformation.copy()
    scaled_transformation['affine_matrix_from_target_to_src'] = transformation['affine_matrix_from_target_to_src'].copy()
    scaled_transformation['affine_matrix_from_target_to_src'][0, 2] *= scale_x
    scaled_transformation['affine_matrix_from_target_to_src'][1, 2] *= scale_y

    return scaled_transformation

@shared_task(bind=True, name='backend.utilities.warping.warp_photo_task', queue='heavy')
def warp_photo_task(self, photo_name: str, microct_name: str, landmarks: str, warped_photo_path: str, apply_nonlinear_warping: bool = True):
    print(f"🚀 TASK RECEIVED: warp_photo_task with photo={photo_name}, microct={microct_name}")
    LOGGER.critical(f"🚀 TASK RECEIVED: warp_photo_task with photo={photo_name}, microct={microct_name}")
    
    # Update initial state
    self.update_state(
        state='STARTED',
        meta={
            'current': PROGRESS_START,
            'total': PROGRESS_COMPLETE,
            'status': 'Starting warping process...',
            'stage': 'initializing',
            'fraction_complete': PROGRESS_START / PROGRESS_COMPLETE
        }
    )
    
    w_dir = os.path.dirname(warped_photo_path)
    LOGGER.info(f'Creating warped image directory: {w_dir}')
    os.makedirs(w_dir, exist_ok=True)
    
    # Clean up old warped images before creating new one, but preserve current
    cleanup_old_warped_images(warped_photo_path)
    
    # Update progress - Loading images
    self.update_state(
        state='PROGRESS',
        meta={
            'current': PROGRESS_LOAD_IMAGE,
            'total': PROGRESS_COMPLETE,
            'status': 'Loading images...',
            'stage': 'loading',
            'fraction_complete': PROGRESS_LOAD_IMAGE / PROGRESS_COMPLETE
        }
    )
    
    photo_image = Image.open(os.path.join(get_input_path(), photo_name))
    microct_image = Image.open(os.path.join(get_input_path(), microct_name))

    # Update progress - Preprocessing
    self.update_state(
        state='PROGRESS',
        meta={
            'current': PROGRESS_PREPROCESSING,
            'total': PROGRESS_COMPLETE,
            'status': 'Preprocessing images...',
            'stage': 'preprocessing',
            'fraction_complete': PROGRESS_PREPROCESSING / PROGRESS_COMPLETE
        }
    )
    
    photo_downscale, microct_downscale = get_downscale_factors(photo_image, microct_image)
    original_photo_w, original_photo_h, original_microct_w, original_microct_h = get_original_dimensions(photo_image, microct_image)
    new_photo_w, new_photo_h, new_microct_w, new_microct_h = get_downscale_dimensions(original_photo_w, original_photo_h, original_microct_w, original_microct_h, photo_downscale, microct_downscale)
    
    # Update progress - Resizing
    self.update_state(
        state='PROGRESS',
        meta={
            'current': PROGRESS_RESIZING,
            'total': PROGRESS_COMPLETE,
            'status': 'Resizing images...',
            'stage': 'resizing',
            'fraction_complete': PROGRESS_RESIZING / PROGRESS_COMPLETE
        }
    )
    

    photo_image, microct_image = downscale_images(photo_image, microct_image, photo_downscale, microct_downscale, new_photo_w, new_photo_h, new_microct_w, new_microct_h)
    
    # Update progress - Processing landmarks
    self.update_state(
        state='PROGRESS',
        meta={
            'current': PROGRESS_LANDMARKS,
            'total': PROGRESS_COMPLETE,
            'status': 'Processing landmarks...',
            'stage': 'landmarks',
            'fraction_complete': PROGRESS_LANDMARKS / PROGRESS_COMPLETE
        }
    )
    

    source_landmarks, target_landmarks = load_and_scale_landmarks(landmarks, original_photo_w, original_photo_h, original_microct_w, original_microct_h, photo_downscale, microct_downscale)
    
    # Update progress - Calculating transformation
    self.update_state(
        state='PROGRESS',
        meta={
            'current': PROGRESS_TRANSFORM,
            'total': PROGRESS_COMPLETE,
            'status': 'Calculating transformation...',
            'stage': 'transforming',
            'fraction_complete': PROGRESS_TRANSFORM / PROGRESS_COMPLETE
        }
    )
    
    # Calculate transformation
    transformation = calculate_coregistration(target_landmarks, source_landmarks, new_microct_w, new_microct_h)
    
    # Convert photo to numpy array for warping
    photo_array = np.array(photo_image)
    
    # Update progress - Starting warping
    self.update_state(
        state='PROGRESS',
        meta={
            'current': PROGRESS_WARPING,
            'total': PROGRESS_COMPLETE,
            'status': 'Warping image...',
            'stage': 'warping',
            'fraction_complete': PROGRESS_WARPING / PROGRESS_COMPLETE
        }
    )
    
    # Perform warping
    start_time = time.perf_counter()    
    warped_photo = do_warp_image(
        photo_array,
        new_microct_h,
        new_microct_w,
        transformation,
        apply_nonlinear_warping=apply_nonlinear_warping
    )
    end_time = time.perf_counter()
    LOGGER.debug(f'⏱️ Time taken for image warping: {end_time - start_time} seconds.')
    
    # Update progress - Saving result
    self.update_state(
        state='PROGRESS',
        meta={
            'current': PROGRESS_SAVING,
            'total': PROGRESS_COMPLETE,
            'status': 'Saving warped image...',
            'stage': 'saving',
            'fraction_complete': PROGRESS_SAVING / PROGRESS_COMPLETE
        }
    )
    
    # Save the warped photo
    LOGGER.info(f'💾 Saving warped photo to: {warped_photo_path}')
    try:
        # Save directly to the final path
        Image.fromarray(warped_photo).save(warped_photo_path, format='JPEG')
        LOGGER.info('✅ Image saved successfully')
        
        # Verify the file exists and is readable
        if not os.path.exists(warped_photo_path):
            raise RuntimeError(f'File does not exist after saving: {warped_photo_path}')
        
        # Verify it's a valid image
        try:
            with Image.open(warped_photo_path) as img:
                img.verify()
            LOGGER.info('✅ Saved file verified as valid image')
        except Exception as e:
            LOGGER.error(f'❌ Saved file is not a valid image: {str(e)}')
            raise RuntimeError(f'Saved file is not a valid image: {str(e)}')
            
    except Exception as e:
        LOGGER.error(f'❌ Failed to save warped photo: {str(e)}')
        # If save failed and file exists, try to clean it up
        try:
            if os.path.exists(warped_photo_path):
                os.remove(warped_photo_path)
        except:
            pass
        raise RuntimeError(f'Failed to save warped photo: {str(e)}')
    
    # Update progress - Complete
    self.update_state(
        state='SUCCESS',
        meta={
            'current': PROGRESS_COMPLETE,
            'total': PROGRESS_COMPLETE,
            'status': 'Warping completed successfully',
            'stage': 'finished',
            'fraction_complete': PROGRESS_COMPLETE / PROGRESS_COMPLETE
        }
    )
        
    return {
        'status': 'success',
        'message': 'Warping completed successfully',
        'warped_photo_path': warped_photo_path
    }


def get_warped_photo_name(output_name: str):
    """Get the name for a warped photo file.
    
    Args:
        output_name (str): Base name for the output file (e.g. uuid)
        
    Returns:
        str: Name of the warped photo file (e.g. '.w/uuid.jpg')
    """
    # Always use forward slashes for Docker compatibility
    return '.w/' + f'{output_name}.jpg'


def get_warped_photo_path(warped_photo_name: str):
    """Get the full path for a warped photo.
    
    Args:
        warped_photo_name (str): Name of the warped photo file (e.g. '.w/uuid.jpg')
        
    Returns:
        str: Full path to the warped photo in the tiles directory
    """
    # Always use get_output_path() to get the correct tiles directory
    output_path = get_output_path()
    LOGGER.debug(f'Output path for warped photo: {output_path}')
    
    # Use forward slashes for Docker compatibility
    full_path = output_path.replace('\\', '/') + '/' + warped_photo_name.replace('\\', '/')
    LOGGER.debug(f'Full path for warped photo: {full_path}')
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(full_path), mode=0o775, exist_ok=True)
    
    return full_path


def warp_photo(photo_name: str, microct_name: str, landmarks: str, output_name: str, apply_nonlinear_warping: bool = True, force_regenerate: bool = False):
    LOGGER.info('📤 Preparing to warp photo...')
    warped_photo_name = get_warped_photo_name(output_name)
    warped_photo_path = get_warped_photo_path(warped_photo_name)
    
    # If force_regenerate is True or file doesn't exist, generate new warped image
    if force_regenerate or not os.path.exists(warped_photo_path):
        LOGGER.critical(f"🔄 Creating new warped image. force_regenerate={force_regenerate}, exists={os.path.exists(warped_photo_path)}")
        
        # Create Celery task
        task = warp_photo_task.delay(photo_name, microct_name, landmarks, warped_photo_path, apply_nonlinear_warping)
        task_id = task.id
        LOGGER.critical(f"✅ Task created with ID: {task_id}")
        
        return {
            'statusCode': 202,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'warped_photo_name': warped_photo_name,
                'task_id': task_id,
                'message': 'Image warping started'
            })
        }
    else:
        # If the file exists and we're not forcing regeneration, just return its info
        LOGGER.info('✅ Using existing warped image')
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'warped_photo_name': warped_photo_name,
                'task_id': None,
                'message': 'Using existing warped image'
            })
        }
