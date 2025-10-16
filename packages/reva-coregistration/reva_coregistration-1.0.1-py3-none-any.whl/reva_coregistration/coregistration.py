from .globals         import *
from .transformations import *
from .landmarks       import *
from .logger          import LOGGER
import time


transformations_cache = {}
def calculate_coregistration(target_landmarks, source_landmarks, target_image_width, target_image_height):
    global transformations_cache
    LOGGER.info('🔄 Starting coregistration calculation...')
    LOGGER.debug(f'📥 {len(target_landmarks) = }, {len(source_landmarks) = }, {target_image_width = }, {target_image_height = }')
    cache_key = (tuple(map(tuple, target_landmarks)), tuple(map(tuple, source_landmarks)), target_image_width, target_image_height)
    LOGGER.debug(f'📥 {cache_key = }')
    if cache_key in transformations_cache:
        LOGGER.info('🔍 Found transformation in cache...')
        return transformations_cache[cache_key]
    else:
        LOGGER.info('🚀 Starting new coregistration calculation...')

    landmarks_input_length = len(target_landmarks)
    LOGGER.debug(f'📥 {landmarks_input_length = }')

    LOGGER.info('🔄 Ensuring minimum landmarks...')
    target_landmarks, source_landmarks = ensure_min_landmarks(target_landmarks, source_landmarks, target_image_width, target_image_height)
    LOGGER.debug(f'📥 {len(target_landmarks) = }, {len(source_landmarks) = }')
    LOGGER.info('🔄 Interpolating landmarks...')
    target_landmarks, source_landmarks = interpolate_landmarks(target_landmarks, source_landmarks)
    LOGGER.debug(f'📥 {len(target_landmarks) = }, {len(source_landmarks) = }')

    LOGGER.info('🔄 Limiting landmark count...')
    target_landmarks, source_landmarks = limit_landmark_count(landmarks_input_length, target_landmarks, source_landmarks)
    LOGGER.debug(f'📥 {len(target_landmarks) = }, {len(source_landmarks) = }')

    LOGGER.info('🔄 Downscaling landmarks...')
    target_landmarks, target_image_height, target_image_width, downscale_factor = downscale_landmarks(target_landmarks, target_image_height, target_image_width)
    LOGGER.debug(f'📥 {len(target_landmarks) = }, {target_image_height = }, {target_image_width = }, {downscale_factor = }')
    LOGGER.debug(f'📝 {source_landmarks.shape = }')
    LOGGER.debug(f'📝 {target_landmarks.shape = }')
    LOGGER.debug(f'📝 Target image height = {target_image_height}, width = {target_image_width}')
    
    LOGGER.info('🔄 Calculating transformation...')
    start_time = time.perf_counter()
    transformation = calculate_transformation(source_landmarks, target_landmarks)
    end_time = time.perf_counter()
    LOGGER.debug(f'⏱️ Time taken for transformation calculation: {end_time - start_time} seconds.')

    transformation['target_image_height'] = target_image_height
    transformation['target_image_width'] = target_image_width
    transformation['downscale_factor'] = downscale_factor
    LOGGER.info('✅ Transformation calculated.')
    
    transformations_cache[cache_key] = transformation
    LOGGER.debug('📦 Transformation cached.')
    
    return transformation