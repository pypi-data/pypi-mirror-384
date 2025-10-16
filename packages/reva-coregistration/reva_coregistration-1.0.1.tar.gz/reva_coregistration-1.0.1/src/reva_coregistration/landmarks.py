from .globals import *
from .logger import LOGGER
from scipy.spatial import Delaunay
import numpy as np


def interpolate_landmarks(landmarks_L, landmarks_R):
    LOGGER.debug(f'🔄 Interpolating points using Delaunay triangulation...')
    while landmarks_L.shape[0] < MAX_LANDMARKS:
        previous_landmarks_length = landmarks_L.shape[0]
        LOGGER.info('🔄 Interpolating points...')
        landmarks_L, landmarks_R = delauney_interpolation(landmarks_L, landmarks_R)
        if landmarks_L.shape[0] == previous_landmarks_length:
            LOGGER.info('🔍 No new landmarks added, breaking the loop...')
            break
        previous_landmarks_length = landmarks_L.shape[0]
    return landmarks_L, landmarks_R


def delauney_interpolation(existing_landmarks_L, existing_landmarks_R):
    LOGGER.debug(f'🔍 Interpolating points...')
    
    min_landmarks = 5
    if len(existing_landmarks_L) < min_landmarks or len(existing_landmarks_R) < min_landmarks:
        LOGGER.debug(f'⚠️ Not enough points for interpolation. Skipping...')
        return existing_landmarks_L, existing_landmarks_R

    # Perform Delaunay triangulation on the left landmarks
    delaunay_triangles_L = Delaunay(existing_landmarks_L)
    LOGGER.debug(f'📐 {delaunay_triangles_L.simplices.shape = }')
    
    # Apply the same triangulation to the right landmarks
    delaunay_triangles_R = existing_landmarks_R[delaunay_triangles_L.simplices]
    LOGGER.debug(f'📐 {delaunay_triangles_R.shape = }')
    
    # Calculate the centroids of each triangle for both left and right landmarks
    centroids_L = np.mean(delaunay_triangles_L.points[delaunay_triangles_L.simplices], axis=1)
    centroids_R = np.mean(delaunay_triangles_R, axis=1)
    LOGGER.debug(f'📐 {centroids_L.shape = }')
    LOGGER.debug(f'📐 {centroids_R.shape = }')
    
    # Add the centroids to the existing landmarks
    interpolated_landmarks_L = np.concatenate((existing_landmarks_L, centroids_L), axis=0)
    interpolated_landmarks_R = np.concatenate((existing_landmarks_R, centroids_R), axis=0)
    LOGGER.debug(f'📐 {interpolated_landmarks_L.shape = }')
    LOGGER.debug(f'📐 {interpolated_landmarks_R.shape = }')
    
    LOGGER.debug(f'✅ Points interpolated.')
    
    return interpolated_landmarks_L, interpolated_landmarks_R


def limit_landmark_count(user_selected_count: int, landmarks_L, landmarks_R):
    
    if landmarks_L.shape[0] <= MAX_LANDMARKS:
        return landmarks_L, landmarks_R
        
    LOGGER.info(f'🔍 Limiting the number of landmarks...')
    original_landmarks_L = landmarks_L[:user_selected_count]
    original_landmarks_R = landmarks_R[:user_selected_count]
    extra_landmarks_L = landmarks_L[user_selected_count:]
    extra_landmarks_R = landmarks_R[user_selected_count:]
    LOGGER.debug(f'📏 Lengths - original_landmarks_L: {len(original_landmarks_L)}, original_landmarks_R: {len(original_landmarks_R)}, extra_landmarks_L: {len(extra_landmarks_L)}, extra_landmarks_R: {len(extra_landmarks_R)}')

    # Create an array of indices and shuffle them to ensure L and R landmarks are shuffled the same
    LOGGER.debug('🔀 Shuffling interpolated landmarks...')
    indices = np.arange(extra_landmarks_L.shape[0])
    np.random.shuffle(indices)
    LOGGER.debug(f'📏 Length of indices after shuffling: {len(indices)}')
    
    # Apply the shuffled indices to L and R landmarks
    shuffled_extra_landmarks_L = extra_landmarks_L[indices]
    shuffled_extra_landmarks_R = extra_landmarks_R[indices]
    LOGGER.debug(f'🔀 Shuffled extra landmarks. {len(shuffled_extra_landmarks_L) = }')
    
    # Concatenate the original and shuffled extra landmarks
    LOGGER.debug(f'🔀 Concatenating original and shuffled extra landmarks...')
    landmarks_L = np.concatenate((original_landmarks_L, shuffled_extra_landmarks_L[:MAX_LANDMARKS - user_selected_count]))
    landmarks_R = np.concatenate((original_landmarks_R, shuffled_extra_landmarks_R[:MAX_LANDMARKS - user_selected_count]))
    LOGGER.debug(f'🔀 Concatenated original and shuffled extra landmarks.')
    
    LOGGER.info(f'📐 After downsizing, {landmarks_L.shape = }')
    LOGGER.info(f'📐 After downsizing, {landmarks_R.shape = }')
    
    return landmarks_L, landmarks_R


def percentage_to_pixel(percentage_x, percentage_y, image_width, image_height):
    LOGGER.debug(f'📥 {percentage_x = }, {percentage_y = }, {image_width = }, {image_height = }')
    x = np.asarray(percentage_x) * image_width if percentage_x is not None else None
    y = np.asarray(percentage_y) * image_height if percentage_y is not None else None
    return x, y


def load_landmarks(landmarks_as_percentage, left_image_width, left_image_height, right_image_width, right_image_height):
    """
    The input landmarks will be as paired percentage coordinates.
    """
    LOGGER.debug(f'📍 Loading landmarks...')
    def process_landmarks(side: str, image_width: int, image_height: int) -> np.ndarray:
        return np.array([
            percentage_to_pixel(landmark[side]['x'], landmark[side]['y'], image_width, image_height)
            for landmark in landmarks_as_percentage
        ])

    landmarks_L = process_landmarks('L', left_image_width, left_image_height)
    landmarks_R = process_landmarks('R', right_image_width, right_image_height)
    LOGGER.debug(f'📍 Landmarks loaded. {landmarks_L.shape = }, {landmarks_R.shape = }')
    return landmarks_L, landmarks_R
    
def ensure_min_landmarks(target_landmarks, source_landmarks, target_image_width, target_image_height):
    num_landmarks = len(target_landmarks)
    LOGGER.debug('🔍 Ensuring minimum landmarks...')
    additional_points_target = []
    additional_points_source = []
    
    if num_landmarks >= 5:
        LOGGER.info('✅ Minimum landmarks already present.')
        return target_landmarks, source_landmarks
    
    if num_landmarks > 0:
        offset = min(target_image_width, target_image_height) * 0.6
        LOGGER.debug(f'📏 {offset = } pixels')
    
    LOGGER.debug('🔍 Checking number of landmarks for minimum requirement...')
    if num_landmarks == 0:
        LOGGER.info('🔍 Generating a pentagon for zero landmarks...')
        center_target = [target_image_width / 2, target_image_height / 2]
        LOGGER.debug(f'📌 Center for target: {center_target}')
        center_source = [target_image_width / 2, target_image_height / 2]  # Assuming similar dimensions for source
        LOGGER.debug(f'📌 Center for source: {center_source}')
        for i in range(4):
            angle = 2 * np.pi * i / 4
            offset = min(target_image_width, target_image_height) * 0.2  # 20% of the smaller dimension
            additional_points_target.append([center_target[0] + np.cos(angle) * offset, center_target[1] + np.sin(angle) * offset])
            additional_points_source.append([center_source[0] + np.cos(angle) * offset, center_source[1] + np.sin(angle) * offset])
        additional_points_target.append(center_target)
        additional_points_source.append(center_source)
        LOGGER.debug(f'📌 Additional points for target: {additional_points_target}')
        LOGGER.debug(f'📌 Additional points for source: {additional_points_source}')
    elif num_landmarks == 1:
        def get_diamond_points(x, y):
            return [[x, y - offset], [x + offset, y], [x, y + offset], [x - offset, y]]
        LOGGER.info('🔍 Generating a diamond shape for one landmark...')
        x_target, y_target = target_landmarks[0]
        x_source, y_source = source_landmarks[0]
        LOGGER.info('🔍 Generating diamond points for target and source...')
        diamond_points_target = get_diamond_points(x_target, y_target)
        diamond_points_source = get_diamond_points(x_source, y_source)
        additional_point_target = [x_target, y_target - 2 * offset]  # Additional point above the diamond for target
        additional_point_source = [x_source, y_source - 2 * offset]  # Additional point above the diamond for source
        additional_points_target = diamond_points_target + [additional_point_target]
        additional_points_source = diamond_points_source + [additional_point_source]
        LOGGER.debug(f'📌 Additional points for target: {additional_points_target}')
        LOGGER.debug(f'📌 Additional points for source: {additional_points_source}')
        LOGGER.debug(f'📌 Additional points for source: {additional_points_source}')
    elif num_landmarks == 2:
        LOGGER.info('🔍 Extending a rectangle formed by two landmarks...')
        additional_points_target = []
        additional_points_source = []
        LOGGER.info('🔍 Calculating additional points for two landmarks...')
        for landmark_type, landmarks in [('target', target_landmarks), ('source', source_landmarks)]:
            for i in range(3):  # Calculate 3 additional points
                angle = 2 * np.pi * i / 3
                x, y = landmarks[0]
                additional_point = [x + np.cos(angle) * offset, y + np.sin(angle) * offset]
                if landmark_type == 'target':
                    additional_points_target.append(additional_point)
                else:
                    additional_points_source.append(additional_point)
            LOGGER.debug(f'📌 Additional points for {landmark_type}: {additional_points_target if landmark_type == "target" else additional_points_source}')
        LOGGER.debug(f'📌 Additional points for source: {additional_points_source}')
    elif num_landmarks == 3:
        LOGGER.info('🔍 Forming a triangle and adding centroid and an external point for three landmarks...')
        centroid_target = np.mean(target_landmarks, axis=0)
        centroid_source = np.mean(source_landmarks, axis=0)
        LOGGER.debug(f'📌 Centroid for target: {centroid_target}')
        LOGGER.debug(f'📌 Centroid for source: {centroid_source}')
        external_point_target = centroid_target + [offset, offset]  # Example external point
        external_point_source = centroid_source + [offset, offset]
        additional_points_target = [centroid_target, external_point_target]
        additional_points_source = [centroid_source, external_point_source]
        LOGGER.debug(f'📌 Additional points for target: {additional_points_target}')
        LOGGER.debug(f'📌 Additional points for source: {additional_points_source}')
    elif num_landmarks == 4:
        LOGGER.info('🔍 Calculating the centroid for four landmarks...')
        centroid_target = np.mean(target_landmarks, axis=0)
        centroid_source = np.mean(source_landmarks, axis=0)
        LOGGER.debug(f'📌 Centroid for target: {centroid_target}')
        LOGGER.debug(f'📌 Centroid for source: {centroid_source}')
        # Determine a direction vector for adding the fifth landmark
        # This example uses a simple strategy of extending from the centroid towards the top-right corner
        # Adjust the magnitude as needed to ensure the point is outside but close to the quadrilateral
        direction_vector = np.array([1, 1])  # Direction towards top-right
        magnitude = min(target_image_width, target_image_height) * 0.1  # 10% of the smaller dimension
        LOGGER.info('🔍 Adding additional points for four landmarks...')
        additional_points_target.append(centroid_target + direction_vector * magnitude)
        additional_points_source.append(centroid_source + direction_vector * magnitude)
        LOGGER.debug(f'📌 Additional points for target after adding: {additional_points_target}')
        LOGGER.debug(f'📌 Additional points for source after adding: {additional_points_source}')
        
    LOGGER.info('🔄 Updating landmarks with additional points...')
    if num_landmarks == 0:
        target_landmarks = np.array(additional_points_target)
        source_landmarks = np.array(additional_points_source)
    elif len(additional_points_target) > 0 and len(additional_points_source) > 0:
        target_landmarks = np.vstack((target_landmarks, additional_points_target))
        source_landmarks = np.vstack((source_landmarks, additional_points_source))
        LOGGER.debug('📝 Landmarks updated with additional points.')
    else:
        LOGGER.debug('🚫 No additional points to update for landmarks.')
    return target_landmarks, source_landmarks
    
    
def downscale_landmarks(landmarks, target_image_height: int, target_image_width: int):
    target_image_pixels = target_image_height * target_image_width
    LOGGER.info(f'🔍 Checking if target image size exceeds maximum allowed pixels of {MAX_WARPED_PIXELS}...')
    if target_image_pixels > MAX_WARPED_PIXELS:
        LOGGER.info(f'🚨 Target image size exceeds maximum allowed pixels. Downsizing...')
        downscale_factor = np.sqrt(target_image_pixels / MAX_WARPED_PIXELS)
        target_image_height = int(target_image_height / downscale_factor)
        target_image_width = int(target_image_width / downscale_factor)
        landmarks /= downscale_factor
        LOGGER.info(f'✅ Target image and landmarks downsized.')
    else:
        LOGGER.info(f'✅ Target image size is within the maximum allowed pixels.')
        downscale_factor = 1
    return landmarks, target_image_height, target_image_width, downscale_factor