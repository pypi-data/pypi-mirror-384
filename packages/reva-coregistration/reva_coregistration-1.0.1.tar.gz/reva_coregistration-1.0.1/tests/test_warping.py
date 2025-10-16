import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pytest
from unittest.mock import patch
import numpy as np
from PIL import Image
from reva_coregistration.warping import do_warp_image, warp_photo, get_upscale_factor, warp_photo_task, get_warped_photo_path, get_warped_photo_name
from reva_coregistration.globals import DASK_BLOCK_SIZE
from reva_coregistration.transformations import transform_point_src_to_tgt, transform_point_tgt_to_src


@pytest.fixture(autouse=True)
def setup_env(tmp_path):
    """Set up test environment with separate paths for input and output."""
    # Create separate directories for input and output
    input_dir = tmp_path / "input"
    tiles_dir = tmp_path / "tiles"
    input_dir.mkdir(exist_ok=True)
    tiles_dir.mkdir(exist_ok=True)
    
    # Configure Celery to use Redis
    os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    
    # Configure Celery queues for testing
    from app import celery
    celery.conf.task_routes = {
        'reva_coregistration.tiles.generate_tiles_task': {'queue': 'heavy'},
        'reva_coregistration.warping.warp_photo_task': {'queue': 'heavy'},
        '*': {'queue': 'light'}
    }
    
    with patch.dict(os.environ, {
        'IMAGE_ENDPOINT': str(input_dir),
        'TILES_ENDPOINT': str(tiles_dir)
    }):
        yield

@pytest.fixture
def sample_image():
    """Create a sample test image."""
    size = (256, 256)
    # Create a gradient test pattern
    x = np.linspace(0, 1, size[0])
    y = np.linspace(0, 1, size[1])
    X, Y = np.meshgrid(x, y)
    # Create RGB image with different patterns in each channel
    image = np.zeros((*size, 3), dtype=np.uint8)
    image[..., 0] = (X * 255).astype(np.uint8)  # Red channel
    image[..., 1] = (Y * 255).astype(np.uint8)  # Green channel
    image[..., 2] = ((X + Y) * 127).astype(np.uint8)  # Blue channel
    return image

@pytest.fixture
def sample_transformation():
    """Create a sample transformation dictionary."""
    # Create inverse matrices for both directions
    matrix_target_to_src = np.array([
        [1.1, 0.1, 2.0],
        [-0.1, 0.9, -1.0],
        [0.0, 0.0, 1.0]
    ])
    matrix_src_to_target = np.linalg.inv(matrix_target_to_src)
    
    return {
        'affine_matrix_from_target_to_src': matrix_target_to_src,
        'affine_matrix_from_src_to_target': matrix_src_to_target,
        'rbf_x_target_to_affine': lambda x, y: x + 0.1 * np.sin(y / 10),
        'rbf_y_target_to_affine': lambda x, y: y + 0.1 * np.cos(x / 10),
        'rbf_x_affine_to_target': lambda x, y: x - 0.1 * np.sin(y / 10),
        'rbf_y_affine_to_target': lambda x, y: y - 0.1 * np.cos(x / 10),
        'target_image_height': 256,
        'target_image_width': 256,
        'downscale_factor': 1.0
    }

def test_do_warp_image_shape(sample_image, sample_transformation):
    """Test if warped image has correct shape."""
    target_h, target_w = 300, 400
    warped = do_warp_image(sample_image, target_h, target_w, sample_transformation)
    assert warped.shape == (target_h, target_w, 3)
    assert warped.dtype == sample_image.dtype

def test_do_warp_image_without_nonlinear(sample_image, sample_transformation):
    """Test warping with only affine transformation."""
    warped = do_warp_image(sample_image, 256, 256, sample_transformation, apply_nonlinear_warping=False)
    assert warped.shape == (256, 256, 3)
    # The result should be different from input due to affine transform
    assert not np.array_equal(warped, sample_image)

def test_do_warp_image_with_nonlinear(sample_image, sample_transformation):
    """Test warping with both affine and nonlinear transformation."""
    warped_linear = do_warp_image(sample_image, 256, 256, sample_transformation, apply_nonlinear_warping=False)
    warped_nonlinear = do_warp_image(sample_image, 256, 256, sample_transformation, apply_nonlinear_warping=True)
    # Results should be different due to nonlinear component
    assert not np.array_equal(warped_linear, warped_nonlinear)

def test_do_warp_image_preserves_range(sample_image, sample_transformation):
    """Test if warping preserves the valid range of pixel values."""
    warped = do_warp_image(sample_image, 256, 256, sample_transformation)
    assert warped.min() >= 0
    assert warped.max() <= 255

def test_do_warp_image_block_size(sample_image, sample_transformation):
    """Test if warping works with different block sizes."""
    # Test with small blocks
    global DASK_BLOCK_SIZE
    original_block_size = DASK_BLOCK_SIZE
    try:
        DASK_BLOCK_SIZE = (64, 64)
        warped_small = do_warp_image(sample_image, 256, 256, sample_transformation)
        DASK_BLOCK_SIZE = (128, 128)
        warped_large = do_warp_image(sample_image, 256, 256, sample_transformation)
        # Results should be nearly identical regardless of block size
        np.testing.assert_allclose(warped_small, warped_large, rtol=1e-5)
    finally:
        DASK_BLOCK_SIZE = original_block_size

@patch('reva_coregistration.warping.get_input_path')
@patch('reva_coregistration.warping.get_upscaled_image_size')
def test_warped_image_creation(mock_get_upscaled_size, mock_get_input_path, tmp_path):
    """Test that warped images are created in the correct location with proper path handling."""
    # Setup test directories
    tiles_dir = tmp_path / "tiles"
    input_dir = tmp_path / "input"
    tiles_dir.mkdir(exist_ok=True)
    input_dir.mkdir(exist_ok=True)
    
    # Create .w directory in tiles directory
    w_dir = tiles_dir / ".w"
    w_dir.mkdir(exist_ok=True)
    
    # Setup environment and mocks
    os.environ['TILES_ENDPOINT'] = str(tiles_dir)
    os.environ['IMAGE_ENDPOINT'] = str(input_dir)
    mock_get_input_path.return_value = str(input_dir)
    mock_get_upscaled_size.return_value = (100, 100)  # No upscaling needed
    
    # Create test input image
    input_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    photo_path = input_dir / "test_photo.jpg"
    input_image.save(photo_path)
    
    # Create test microCT image
    microct_image = Image.fromarray(np.zeros((200, 200, 3), dtype=np.uint8))
    microct_path = input_dir / "test_microct.jpg"
    microct_image.save(microct_path)
    
    # Create test landmarks
    landmarks = [
        {
            'L': {'x': 0.0, 'y': 0.0},
            'R': {'x': 100.0, 'y': 100.0}
        },
        {
            'L': {'x': 0.0, 'y': 0.0},
            'R': {'x': 200.0, 'y': 200.0}
        }
    ]
    
    # Setup warped image path
    output_name = "test_output"
    warped_photo_name = get_warped_photo_name(output_name)
    warped_photo_path = get_warped_photo_path(warped_photo_name)
    
    print(f"Test paths:")
    print(f"INPUT_ENDPOINT: {os.getenv('IMAGE_ENDPOINT')}")
    print(f"TILES_ENDPOINT: {os.getenv('TILES_ENDPOINT')}")
    print(f"Input path (mocked): {mock_get_input_path.return_value}")
    print(f"Photo path: {photo_path}")
    print(f"MicroCT path: {microct_path}")
    print(f"Warped photo name: {warped_photo_name}")
    print(f"Warped photo path: {warped_photo_path}")
    
    # Run warping task
    warp_photo_task(
        photo_name="test_photo.jpg",  # Just the filename, not the full path
        microct_name="test_microct.jpg",
        landmarks=landmarks,
        warped_photo_path=warped_photo_path,
        apply_nonlinear_warping=True
    )
    
    # Verify file creation
    assert os.path.exists(warped_photo_path), f"Warped image not found at {warped_photo_path}"
    
    # Verify file is readable
    try:
        Image.open(warped_photo_path)
    except Exception as e:
        pytest.fail(f"Failed to open warped image: {e}")

@patch('reva_coregistration.warping.get_image_hash')
@patch('reva_coregistration.warping.get_upscaled_image_size', autospec=True)
@patch('reva_coregistration.warping.get_input_path')
def test_get_upscale_factor(mock_get_input_path, mock_get_upscaled_size, mock_get_image_hash, tmp_path):
    """Test upscale factor calculation."""
    # Create input directory
    input_dir = tmp_path / "input"
    input_dir.mkdir(exist_ok=True)
    
    # Set up the mocks
    mock_get_input_path.return_value = str(input_dir)
    mock_get_image_hash.return_value = "test_hash"
    mock_get_upscaled_size.return_value = (200, 200)  # 2x upscale of our 100x100 test image

    # Create a temporary test image
    test_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    image_path = os.path.join(input_dir, "test.jpg")
    test_image.save(image_path)

    # Test the function
    factor, size, image = get_upscale_factor("test.jpg")
    
    # Verify the results
    assert factor == 2.0  # 200/100 = 2.0
    assert size == (100, 100)
    assert isinstance(image, Image.Image)
    
    # Verify our mocks were called correctly
    assert mock_get_input_path.call_count == 2  # Called twice: once for hash, once for image loading
    mock_get_image_hash.assert_called_once_with(os.path.join(str(input_dir), "test.jpg"))
    mock_get_upscaled_size.assert_called_once_with("test_hash")

def test_warp_photo_error_handling():
    """Test error handling in warp_photo function."""
    # Test with non-existent input files
    with pytest.raises(FileNotFoundError):
        warp_photo_task(
            photo_name="nonexistent.jpg",
            microct_name="nonexistent.jpg",
            landmarks="[]",
            warped_photo_path="/tmp/test.jpg",
            apply_nonlinear_warping=True
        )

def test_transform_point_consistency(sample_transformation):
    """Test if forward and inverse point transformations are consistent."""
    # Test point
    x, y = 100.0, 100.0
    
    # Transform forward then backward
    transformed = transform_point_src_to_tgt(sample_transformation, x, y)
    back_transformed = transform_point_tgt_to_src(sample_transformation, transformed[0], transformed[1])
    
    # Should approximately recover original coordinates
    np.testing.assert_allclose([x, y], back_transformed, rtol=1e-3)

def test_transform_point_nonlinear_effect(sample_transformation):
    """Test if nonlinear transformation has expected effect."""
    x, y = 100.0, 100.0
    
    # Transform with and without nonlinear component
    linear = transform_point_src_to_tgt(sample_transformation, x, y, apply_nonlinear_warping=False)
    nonlinear = transform_point_src_to_tgt(sample_transformation, x, y, apply_nonlinear_warping=True)
    
    # Results should be different
    assert not np.allclose(linear, nonlinear)

if __name__ == "__main__":
    pytest.main()

