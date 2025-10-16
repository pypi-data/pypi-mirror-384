from .image_utils import get_upscaled_image_size
from .landmarks import load_landmarks, percentage_to_pixel
from .coregistration import calculate_coregistration, transform_point_src_to_tgt, transform_point_tgt_to_src
from .logger import LOGGER
import numpy as np


def convert_numpy_types(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


class Viewer:
    def __init__(self, x_percentage, y_percentage, slice_width, slice_index, max_slices, target_image_width, target_image_height, source_image_width, source_image_height, landmarks, from_source: bool = False, apply_nonlinear_warping: bool = True):
        LOGGER.info('🔄 Converting percentage coordinates to image coordinates...')
        LOGGER.debug(f'📥 {x_percentage = }, {y_percentage = }, {source_image_width = }, {source_image_height = }')
        if from_source:
            x_y_in_image_coords = percentage_to_pixel(x_percentage, y_percentage, source_image_width, source_image_height)
        else:
            x_y_in_image_coords = percentage_to_pixel(x_percentage, y_percentage, target_image_width, target_image_height)
        LOGGER.debug(f'📥 {x_y_in_image_coords = }')
        self.x = x_y_in_image_coords[0]
        self.y = x_y_in_image_coords[1]
        LOGGER.info('✅ Converted percentage coordinates to image coordinates.')
        if self.x is not None and self.y is not None and (isinstance(self.x, (list, np.ndarray)) and len(self.x) > 0) and (isinstance(self.y, (list, np.ndarray)) and len(self.y) > 0):
            LOGGER.debug(f'📥 {len(self.x) = }, {len(self.y) = }')
        else:
            LOGGER.debug(f'📥 {self.x = }, {self.y = }')
        
        self.slice_width = slice_width
        self.slice_index = slice_index
        self.max_slices = max_slices
        self.target_image_width = target_image_width
        self.target_image_height = target_image_height
        self.source_image_width = source_image_width
        self.source_image_height = source_image_height  
        LOGGER.debug(f'📥 {self.target_image_width = }, {self.target_image_height = }, {self.source_image_width = }, {self.source_image_height = }')
        self.landmarks = landmarks
        self.apply_nonlinear_warping = apply_nonlinear_warping
        LOGGER.info('🔄 Attempting coregistration calculation...')
        try:
            LOGGER.info('🔄 Loading landmarks...')
            target_landmarks, source_landmarks = load_landmarks(
                landmarks,
                self.target_image_width,
                self.target_image_height,
                self.source_image_width,
                self.source_image_height
            )
            LOGGER.debug(f'📥 {target_landmarks = }, {source_landmarks = }')
            LOGGER.info('🔄 Calculating coregistration...')
            self.transformation = calculate_coregistration(
                target_landmarks,
                source_landmarks,
                self.target_image_width,
                self.target_image_height
            )
            LOGGER.debug(f'✅ Coregistration calculation successful: {self.transformation = }')
        except Exception as error:
            LOGGER.error(f'❌ Coregistration calculation failed: {error}')
            self.transformation = None
        self.calculate_coordinates_functions = {
            'S': self.calculate_coordinates_from_S,
            'L': self.calculate_coordinates_from_L,
            'C': self.calculate_coordinates_from_C,
            'R': self.calculate_coordinates_from_R
        }

    def _initialize_output(self, from_viewer):
        LOGGER.debug('🔄 Initializing output...')
        output = {viewer_id: {'x': None, 'y': None} for viewer_id in ['L', 'R', 'C', 'S']}
        output[from_viewer] = {'x': self.x, 'y': self.y}
        LOGGER.debug(f'📤 {output = }')
        return output

    def _calculate_slice_coordinates(self, x_value):
        """Calculate S viewer coordinates from an x value"""
        if self.slice_width is not None:
            LOGGER.debug('🔄 Calculating slice_x for S viewer...')
            target_x_percent = x_value / self.target_image_width
            slice_x = np.rint(target_x_percent * self.slice_width).astype(int)
            self.output['S']['x'] = slice_x
            LOGGER.debug(f'📤 {slice_x = }')

    def _set_left_center_coordinates(self, x, y):
        """Set coordinates for L and C viewers"""
        self.output['L'] = {'x': x, 'y': y}
        if self.transformation:
            self.output['C'] = {
                'x': x / self.transformation['downscale_factor'] if x is not None else None,
                'y': y / self.transformation['downscale_factor'] if y is not None else None
            }
        else:
            self.output['C'] = {'x': x, 'y': y}

    def _transform_and_set_right_coordinates(self, x, y, transform_func):
        """Transform and set coordinates for R viewer"""
        if x is not None and y is not None and (isinstance(x, (list, np.ndarray)) and len(x) > 0) and (isinstance(y, (list, np.ndarray)) and len(y) > 0):
            LOGGER.debug(f'📥 {len(x) = }, {len(y) = }')
            LOGGER.debug(f'📥 {x[0:10] = }, {y[0:10] = }')
        else:
            LOGGER.debug(f'📥 {x = }, {y = }')
        LOGGER.debug(f'📥 {self.transformation = }')
        LOGGER.debug(f'📥 {self.apply_nonlinear_warping = }')
        transformed = transform_func(self.transformation, x, y, apply_nonlinear_warping=self.apply_nonlinear_warping)
        right_x, right_y = transformed
        LOGGER.debug(f'🔄 Transformed coordinates for R viewer: {right_x = }, {right_y = }')
        self.output['R'] = {'x': right_x, 'y': right_y}
        return right_x, right_y

    def calculate_coordinates_from_S(self):
        LOGGER.debug('🔄 Calculating coordinates from S viewer...')
        x_percent = self.x / self.slice_width
        left_x = x_percent * self.target_image_width
        self._set_left_center_coordinates(left_x, None)
        
        if self.slice_index is not None and self.max_slices is not None:
            left_y = self.target_image_height * self.slice_index / self.max_slices
            self._transform_and_set_right_coordinates(left_x, left_y, transform_point_tgt_to_src)
        
        return self.output

    def calculate_coordinates_from_L(self):
        LOGGER.debug('🔄 Calculating coordinates from L viewer...')
        self._set_left_center_coordinates(self.x, self.y)
        self._calculate_slice_coordinates(self.x)
        self._transform_and_set_right_coordinates(self.x, self.y, transform_point_tgt_to_src)
        return self.output

    def calculate_coordinates_from_R(self):
        if self.x is not None and self.y is not None and (isinstance(self.x, (list, np.ndarray)) and len(self.x) > 0) and (isinstance(self.y, (list, np.ndarray)) and len(self.y) > 0):
            LOGGER.debug(f'📥 {len(self.x) = }, {len(self.y) = }')
            LOGGER.debug(f'📥 {self.x[0:10] = }, {self.y[0:10] = }')
        else:
            LOGGER.debug(f'📥 {self.x = }, {self.y = }')
        LOGGER.debug(f'📥 {self.transformation = }')
        LOGGER.debug(f'📥 {self.apply_nonlinear_warping = }')
        left_x, left_y = self._transform_and_set_right_coordinates(self.x, self.y, transform_point_src_to_tgt)
        self._set_left_center_coordinates(left_x, left_y)
        self._calculate_slice_coordinates(left_x)
        return self.output

    def calculate_coordinates_from_C(self):
        LOGGER.info('🔄 Calculating coordinates from C viewer...')
        LOGGER.info(f'🔄 {self.transformation = }')
        self.x = np.asarray(self.x, dtype=np.float64) * self.transformation['downscale_factor']
        self.y = np.asarray(self.y, dtype=np.float64) * self.transformation['downscale_factor']
        return self.calculate_coordinates_from_L()

    def calculate_associated_coordinates(self, from_viewer):
        LOGGER.debug('🔄 Starting to calculate coregistration and transform point...')
        try:
            self.output = self._initialize_output(from_viewer)
            self.output = self.calculate_coordinates_functions[from_viewer]()
            LOGGER.debug('✅ Coregistration calculated and point transformed.')
        except Exception as error:
            LOGGER.warning(f'🚨 Failed to calculate coregistration and transform point: {error}')
        return self.output


def get_associated_coordinates(
    x_percentage: float,
    y_percentage: float, 
    source_image_width: int,
    source_image_height: int,
    source_is_photograph: bool,
    target_image_width: int,
    target_image_height: int,
    apply_nonlinear_warping: bool,
    landmarks: list[dict],
) -> dict[str, dict[str, float | None]]:
    """
    Set source_is_photograph to True if the x_percentage and y_percentage are
    the coordinate locations from the photograph, and the target is the microCT.

    Set source_is_photograph to False if the x_percentage and y_percentage are
    the coordinate locations from the microCT, and the target is the photograph.
    """
    source_viewer = 'R' if source_is_photograph else 'L'
    return get_associated_coordinates_from_any_viewer(
        x_percentage, y_percentage,
        source_image_width, source_image_height, source_viewer,
        target_image_width, target_image_height,
        None, None, None,
        landmarks,
        apply_nonlinear_warping
    )


def get_associated_coordinates_from_any_viewer(
    x_percentage: float,
    y_percentage: float, 
    source_image_width: int,
    source_image_height: int,
    source_viewer: str,
    target_image_width: int,
    target_image_height: int,
    slice_width: float | None,
    slice_index: int | None,
    max_slices: int | None,
    landmarks: list[dict],
    apply_nonlinear_warping: bool,
) -> dict[str, dict[str, float | None]]:
    from_source = source_viewer == 'R'
    LOGGER.info(f'🔄 Calculating associated coordinates...')
    viewer = Viewer(
        x_percentage, y_percentage,
        slice_width, slice_index, max_slices,
        target_image_width, target_image_height,
        source_image_width, source_image_height,
        landmarks,
        from_source,
        apply_nonlinear_warping
    )
    coordinates = viewer.calculate_associated_coordinates(source_viewer)
    # LOGGER.debug(f'📤 {coordinates = }')
    return coordinates


def get_associated_coordinates_from_payload(payload):
    LOGGER.debug('🔄 Starting to process associated coordinates...')
    
    from_viewer = payload.get('from_viewer')
    x_percentage = payload.get('x_percentage')
    y_percentage = payload.get('y_percentage')
    apply_nonlinear_warping = payload.get('apply_nonlinear_warping', True)
    LOGGER.debug(f'📥 {x_percentage = }, {y_percentage = }, {from_viewer = }, {apply_nonlinear_warping = }')
        
    landmarks = payload.get('landmarkPairs')
    # logger.debug(f'📥 {landmarks = }')
    
    tile_sources = payload.get('tileSources')
    LOGGER.debug(f'📥 {tile_sources = }')

    upscaled_size = get_upscaled_image_size(tile_sources['L'])
    if upscaled_size is None:
        LOGGER.warning('🚨 No reference tile source found in payload')
        return None
    target_image_width, target_image_height = upscaled_size
    LOGGER.debug(f'📥 {target_image_width = }, {target_image_height = }')
    
    upscaled_size = get_upscaled_image_size(tile_sources['R'])
    if upscaled_size is None:
        if from_viewer == 'R':
            LOGGER.warning('🚨 Cannot calculate coordinates from viewer R when R is not loaded')
            return None
        LOGGER.warning('🚨 No source image (R) loaded, will only calculate coordinates for L, C, and S viewers')
        source_image_width, source_image_height = None, None
    else:
        source_image_width, source_image_height = upscaled_size
    LOGGER.debug(f'📥 {source_image_width = }, {source_image_height = }')

    slice_index = payload.get('slice_index')
    max_slices = payload.get('max_slices')
    slice_width = get_upscaled_image_size(tile_sources['S'])[0] if tile_sources['S'] else None
    LOGGER.debug(f'📥 {slice_index = }, {max_slices = }, {slice_width = }')

    return get_associated_coordinates_from_any_viewer(
        x_percentage, y_percentage,
        source_image_width, source_image_height,
        from_viewer,
        target_image_width, target_image_height,
        slice_width, slice_index, max_slices,
        landmarks,
        apply_nonlinear_warping
    )