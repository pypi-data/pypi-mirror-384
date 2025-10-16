from .globals import *
from .logger import LOGGER

import numpy as np
import cv2
from scipy.interpolate import Rbf
from scipy.ndimage import map_coordinates
#import dask.array as da


def calculate_transformation(landmarks_source, landmarks_target):
    '''
    This function calculates the transformation matrix between source and target landmarks.
    
    From source landmarks, an affine transformation is best fit to go to target landmarks.
    The affine-transformed source points are transformed.
    Then, from these affine-transformed landmarks, a thin plate spline is used to go to target.
    This outputs a dictionary containing a linear transformation from source to affine-transformed,
    and from affine-transformed to source.
    It also contains a radial basis function which goes from affine-transformed to target,
    and from target back to affine-transformed.
    
    Parameters:
    landmarks_source: A numpy array of num_landmarks rows and 2 columns (first col is x, second is y)
    landmarks_target: Same array as landmarks_source, but for the target image
    
    Returns:
    dictionary of forward and reverse transformations
    '''
    LOGGER.info(f'🔄 Converting landmarks to float32...')
    src_pts = np.array(landmarks_source, dtype=np.float32)
    tgt_pts = np.array(landmarks_target, dtype=np.float32)

    LOGGER.info(f'🔄 Computing the affine transformation matrix...')
    affine_matrix_from_src_to_target, _ = cv2.estimateAffine2D(src_pts, tgt_pts)
    LOGGER.info(f'✅ Affine transformation matrix computed.')
    LOGGER.debug(f'📝 {affine_matrix_from_src_to_target = }')
    
    affine_transformed_src_points = cv2.transform(np.array([src_pts]), affine_matrix_from_src_to_target)[0]
    LOGGER.debug(f'📐 {affine_transformed_src_points.shape = }')
    
    LOGGER.info(f'🔄 Computing the inverse affine transformation matrix...')
    affine_matrix_from_target_to_src = np.linalg.inv(np.vstack([affine_matrix_from_src_to_target, [0, 0, 1]]))[0:2]
    LOGGER.info(f'✅ Inverse affine transformation matrix computed.')
    LOGGER.debug(f'📝 {affine_matrix_from_target_to_src = }')

    src_x, src_y = zip(*affine_transformed_src_points)
    tgt_x, tgt_y = zip(*landmarks_target)
    
    LOGGER.info(f'🔄 Calculating radial basis functions...')
    rbf_x_affine_to_target = Rbf(src_x, src_y, tgt_x, function=RBF_FUNCTION, smooth=RBF_SMOOTHNESS)
    rbf_y_affine_to_target = Rbf(src_x, src_y, tgt_y, function=RBF_FUNCTION, smooth=RBF_SMOOTHNESS)
    rbf_x_target_to_affine = Rbf(tgt_x, tgt_y, src_x, function=RBF_FUNCTION, smooth=RBF_SMOOTHNESS)
    rbf_y_target_to_affine = Rbf(tgt_x, tgt_y, src_y, function=RBF_FUNCTION, smooth=RBF_SMOOTHNESS)
    LOGGER.info(f'✅ RBF calculated.')    
    
    return {
        'affine_matrix_from_src_to_target': affine_matrix_from_src_to_target,
        'affine_matrix_from_target_to_src': affine_matrix_from_target_to_src,
        'rbf_x_affine_to_target': rbf_x_affine_to_target,
        'rbf_y_affine_to_target': rbf_y_affine_to_target,
        'rbf_x_target_to_affine': rbf_x_target_to_affine,
        'rbf_y_target_to_affine': rbf_y_target_to_affine
    }


def _prepare_coordinates(x: np.ndarray, y: np.ndarray, scale_factor: float, divide: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Prepare coordinates by converting to numpy arrays and applying scaling."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    
    if scale_factor != 1:
        if divide:
            x, y = x / scale_factor, y / scale_factor
        else:
            x, y = x * scale_factor, y * scale_factor
    
    return x, y

def _apply_rbf_transform(x: np.ndarray, y: np.ndarray, rbf_x: Rbf, rbf_y: Rbf) -> tuple[np.ndarray, np.ndarray]:
    """Apply RBF transformation to coordinates."""
    return rbf_x(x, y), rbf_y(x, y)

def _apply_affine_transform(x: np.ndarray, y: np.ndarray, affine_matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Apply affine transformation to coordinates."""
    homogeneous_coords = np.array([x, y, np.ones_like(x)])
    transformed = np.dot(affine_matrix, homogeneous_coords)
    return transformed[0], transformed[1]

def _format_output(x: np.ndarray, y: np.ndarray) -> list:
    """Format output coordinates consistently."""
    if len(x.shape) == 0:
        return list(np.array([x, y]))
    return [x, y]

def transform_point_src_to_tgt(transformation: dict, x: float, y: float, apply_nonlinear_warping: bool = True) -> list:
    """Transform points from source to target coordinate space."""
    # First apply affine, then RBF, then scaling
    x, y = _prepare_coordinates(x, y, scale_factor = 1)
    
    x, y = _apply_affine_transform(
        x, y, 
        transformation['affine_matrix_from_src_to_target']
    )
    
    if apply_nonlinear_warping:
        x, y = _apply_rbf_transform(
            x, y,
            transformation['rbf_x_affine_to_target'],
            transformation['rbf_y_affine_to_target']
        )
    
    x, y = _prepare_coordinates(x, y, transformation['downscale_factor'])
    return _format_output(x, y)

def transform_point_tgt_to_src(transformation: dict, x: float, y: float, apply_nonlinear_warping: bool = True) -> list:
    """Transform points from target to source coordinate space."""
    # First apply scaling, then RBF, then affine
    x, y = _prepare_coordinates(x, y, transformation['downscale_factor'], divide=True)
    
    if apply_nonlinear_warping:
        x, y = _apply_rbf_transform(
            x, y,
            transformation['rbf_x_target_to_affine'],
            transformation['rbf_y_target_to_affine']
        )
    
    x, y = _apply_affine_transform(
        x, y,
        transformation['affine_matrix_from_target_to_src']
    )
    
    return _format_output(x, y)


def get_export_file_name(source_hash, target_hash):
    from .image_utils import truncate_hash
    source_hash = truncate_hash(source_hash)
    target_hash = truncate_hash(target_hash)
    return f'xforms_{source_hash}_{target_hash}.pkl'
