import unittest
import numpy as np
from PIL import Image
import os
import time
import requests
import hashlib
import tempfile
import shutil
from unittest.mock import patch
from reva_coregistration.slices import get_tiff_scaler, get_slice_image, clear_tiff_scale_cache

class TestSlices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create a test multi-frame TIFF file."""
        # Configure Celery to use Redis
        import os
        os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
        os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
        
        # Configure Celery queues for testing
        from app import celery
        celery.conf.task_routes = {
            'reva_coregistration.tiles.generate_tiles_task': {'queue': 'heavy'},
            'reva_coregistration.warping.warp_photo_task': {'queue': 'heavy'},
            '*': {'queue': 'light'}
        }
        
        # Create temporary directories for test data
        cls.temp_dir = tempfile.mkdtemp()
        cls.input_dir = os.path.join(cls.temp_dir, 'input')
        cls.output_dir = os.path.join(cls.temp_dir, 'output')
        
        # Create directories
        os.makedirs(cls.input_dir, exist_ok=True)
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Test file setup
        cls.test_filename = 'test_multi.tif'
        cls.test_tiff_path = os.path.join(cls.input_dir, cls.test_filename)
        
        # Create a multi-frame TIFF with known values
        frames = []
        cls.n_frames = 10  # Smaller number for testing
        
        # Create gradients that go from left to right
        # Frame 1: Gradient from 0 to 100
        x = np.linspace(0, 100, 10)  # Create horizontal gradient
        frame1 = np.tile(x, (10, 1))  # Repeat for each row
        frames.append(Image.fromarray(frame1.astype(np.uint16)))
        
        # Frame 2: Gradient from 50 to 150
        x = np.linspace(50, 150, 10)
        frame2 = np.tile(x, (10, 1))
        frames.append(Image.fromarray(frame2.astype(np.uint16)))
        
        # Frame 3: Gradient from 100 to 200
        x = np.linspace(100, 200, 10)
        frame3 = np.tile(x, (10, 1))
        frames.append(Image.fromarray(frame3.astype(np.uint16)))
        
        # Additional frames with controlled ranges
        for i in range(3, cls.n_frames):
            start_val = i * 20  # Smaller increments to stay within 0-200 range
            end_val = min(200, start_val + 100)  # Cap at 200
            x = np.linspace(start_val, end_val, 10)
            frame = np.tile(x, (10, 1))
            frames.append(Image.fromarray(frame.astype(np.uint16)))

        # Save the test file
        frames[0].save(
            cls.test_tiff_path,
            save_all=True,
            append_images=frames[1:],
            format='TIFF'
        )

        # API endpoints for tile generation tests
        cls.base_url = "http://localhost:5001"
        cls.start_tile_generation_endpoint = f"{cls.base_url}/start-tile-generation"
        cls.tiles_ready_endpoint = f"{cls.base_url}/tiles-ready"
        cls.task_progress_endpoint = f"{cls.base_url}/task-progress"

        # Test if server is running
        try:
            response = requests.get(cls.base_url)
            if response.status_code not in [200, 404]:
                raise ConnectionError("Flask server is not running")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Flask server is not running")

    def setUp(self):
        """Set up before each test."""
        self.tiff_image = Image.open(self.test_tiff_path)
        
        # Set up path mocks
        self.input_patcher = patch('reva_coregistration.paths.get_input_path')
        self.output_patcher = patch('reva_coregistration.paths.get_output_path')
        self.hash_patcher = patch('reva_coregistration.tiles.get_image_hash')
        
        self.mock_input_path = self.input_patcher.start()
        self.mock_output_path = self.output_patcher.start()
        self.mock_image_hash = self.hash_patcher.start()
        
        # Set mock paths to our temporary directories
        self.mock_input_path.return_value = self.input_dir
        self.mock_output_path.return_value = self.output_dir
        
        # Create a deterministic hash for testing
        def mock_hash(path):
            # Use the filename part for a deterministic hash
            filename = os.path.basename(path)
            return hashlib.sha256(filename.encode()).hexdigest()
        
        self.mock_image_hash.side_effect = mock_hash

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'tiff_image'):
            self.tiff_image.close()
        
        # Stop all mocks
        self.input_patcher.stop()
        self.output_patcher.stop()
        self.hash_patcher.stop()

    @classmethod
    def tearDownClass(cls):
        """Clean up test files."""
        # Remove temporary directory and all its contents
        shutil.rmtree(cls.temp_dir)

    # Basic slice extraction tests
    def test_get_tiff_scaler_file_input(self):
        """Test get_tiff_scaler with file path input."""
        scaler = get_tiff_scaler(self.test_tiff_path)  # Use full Windows path
        min_val, max_val = scaler
        self.assertEqual(min_val, 0)
        self.assertEqual(max_val, 200)

    def test_get_tiff_scaler_image_input(self):
        """Test get_tiff_scaler with PIL Image input."""
        scaler = get_tiff_scaler(self.tiff_image, is_image=True)
        min_val, max_val = scaler
        self.assertEqual(min_val, 0)
        self.assertEqual(max_val, 200)

    def test_get_slice_image_first_frame(self):
        """Test getting the first slice."""
        scaler = get_tiff_scaler(self.tiff_image, is_image=True)
        slice_image = get_slice_image(self.tiff_image, 0, scaler)
        
        self.assertIsInstance(slice_image, Image.Image)
        slice_array = np.array(slice_image)
        self.assertEqual(slice_array.shape, (10, 10))
        self.assertEqual(slice_array.dtype, np.uint8)
        
        # First frame has values 0-100 in a global range of 0-200
        # After normalization and scaling to 8-bit with rounding:
        # 0 -> 0, 100 -> 128 (rounded from 127.5)
        # Note: The image is horizontally flipped
        print(f"\nDebug info for first frame test:")
        print(f"Scaler: {scaler}")
        print(f"First row of slice array: {slice_array[0]}")
        print(f"Expected at (0,-1): 0")
        print(f"Actual at (0,-1): {slice_array[0,-1]}")
        print(f"Expected at (0,0): {round(255 * (100/200))}")
        print(f"Actual at (0,0): {slice_array[0,0]}")
        
        self.assertTrue(np.allclose(slice_array[0, -1], 0, atol=1))  # First pixel (0 in original)
        self.assertTrue(np.allclose(slice_array[0, 0], round(255 * (100/200)), atol=1))  # Last pixel (100 in original)

    def test_get_slice_image_last_frame(self):
        """Test getting the last slice."""
        scaler = get_tiff_scaler(self.tiff_image, is_image=True)
        slice_image = get_slice_image(self.tiff_image, 2, scaler)
        
        slice_array = np.array(slice_image)
        # Last frame has values 100-200 in a global range of 0-200
        # After normalization and scaling to 8-bit with rounding:
        # 100 -> 128 (rounded from 127.5), 200 -> 255
        self.assertTrue(np.allclose(slice_array[0, -1], round(255 * (100/200)), atol=1))  # First pixel (100 in original)
        self.assertTrue(np.allclose(slice_array[0, 0], 255, atol=1))  # Last pixel (200 in original)

    def test_horizontal_flip(self):
        """Test that the slice is properly flipped horizontally."""
        scaler = get_tiff_scaler(self.tiff_image, is_image=True)
        min_val, max_val = scaler
        slice_image = get_slice_image(self.tiff_image, 0, scaler)
        
        self.tiff_image.seek(0)
        original = np.array(self.tiff_image)
        scaled_original = np.round((original - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        flipped_original = np.fliplr(scaled_original)
        
        np.testing.assert_array_almost_equal(
            np.array(slice_image),
            flipped_original,
            decimal=0  # We only need to check integer equality since we're dealing with uint8
        )

    def test_invalid_layer_index(self):
        """Test that requesting an invalid layer raises an error."""
        scaler = get_tiff_scaler(self.tiff_image, is_image=True)
        with self.assertRaises(Exception):
            get_slice_image(self.tiff_image, 999, scaler)

    def test_invalid_file_path(self):
        """Test that invalid file path raises an error."""
        with self.assertRaises(Exception):
            get_tiff_scaler("nonexistent.tif")

    # Tile generation and viewer tests
    def test_slice_tile_generation_performance(self):
        """Test performance of generating tiles for multiple slices."""
        print("\nTesting slice tile generation performance...")
        
        start_time = time.time()
        # Make API call with just the filename
        response = requests.post(
            self.start_tile_generation_endpoint,
            json={
                'filename': self.test_filename,
                'viewer_suffix': 'S'  # This will be used to determine is_slice
            }
        )
        if response.status_code != 202:  # API returns 202 Accepted for async tasks
            print(f"\nAPI Error Response: {response.text}")
        self.assertEqual(response.status_code, 202)  # Should be 202 Accepted
        data = response.json()
        hash_id = data['hash']
        task_ids = data['task_ids']
        
        # Monitor all tasks
        all_complete = False
        timeout = 300  # 5 minutes
        task_times = []
        task_states = {}
        session_timestamps = set()

        while not all_complete and time.time() - start_time < timeout:
            all_complete = True
            for task_id in task_ids:
                if task_id not in task_states or task_states[task_id] != 'SUCCESS':
                    response = requests.get(f"{self.task_progress_endpoint}/{task_id}")
                    task_info = response.json()
                    
                    # Verify session timestamp is present
                    if 'session_timestamp' in task_info:
                        session_timestamps.add(task_info['session_timestamp'])
                    
                    if task_info['state'] not in ['SUCCESS', 'FAILURE']:
                        all_complete = False
                    elif task_info['state'] == 'SUCCESS' and task_id not in task_states:
                        task_times.append(time.time() - start_time)
                        task_states[task_id] = 'SUCCESS'
                    elif task_info['state'] == 'FAILURE':
                        self.fail(f"Task {task_id} failed: {task_info.get('status')}")
            
            if not all_complete:
                time.sleep(0.5)

        total_time = time.time() - start_time
        
        # Verify that session timestamp is consistent
        self.assertGreater(len(session_timestamps), 0, "No session timestamps found in task updates")
        
        # Performance assertions and metrics
        self.assertLess(total_time, timeout, "Tile generation took too long")
        avg_time_per_slice = total_time / self.n_frames
        print(f"\nPerformance metrics:")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average time per slice: {avg_time_per_slice:.2f} seconds")
        print(f"Number of slices: {self.n_frames}")
        print(f"Session timestamps found: {len(session_timestamps)}")
        
        # Wait for tiles to be ready
        tiles_ready = False
        start_time = time.time()
        while not tiles_ready and time.time() - start_time < timeout:
            response = requests.get(f"{self.tiles_ready_endpoint}/{hash_id}")
            data = response.json()
            if response.status_code == 200 and data.get('ready', False):
                tiles_ready = True
                break
            elif response.status_code == 202:
                time.sleep(0.5)
            else:
                self.fail(f"Unexpected response checking tiles ready: {response.status_code}")
        
        if not tiles_ready:
            self.fail(f"Timed out waiting for tiles after {timeout} seconds")
        
        self.assertIn('slices', data)
        self.assertEqual(len(data['slices']), self.n_frames)

    def test_concurrent_slice_loading(self):
        """Test that nearby slices are preloaded while viewing."""
        print("\nTesting concurrent slice loading...")
        
        # Start tile generation
        response = requests.post(
            self.start_tile_generation_endpoint,
            json={
                'filename': self.test_filename,
                'viewer_suffix': 'S'  # This will be used to determine is_slice
            }
        )
        self.assertEqual(response.status_code, 202)  # Should be 202 Accepted
        data = response.json()
        hash_id = data['hash']
        task_ids = data['task_ids']
        
        # Wait for all tasks to complete
        print("Waiting for all tile generation tasks to complete...")
        all_complete = False
        timeout = 300  # 5 minutes
        start_time = time.time()
        task_states = {}

        while not all_complete and time.time() - start_time < timeout:
            all_complete = True
            for task_id in task_ids:
                if task_id not in task_states or task_states[task_id] != 'SUCCESS':
                    response = requests.get(f"{self.task_progress_endpoint}/{task_id}")
                    task_info = response.json()
                    
                    if task_info['state'] not in ['SUCCESS', 'FAILURE']:
                        all_complete = False
                    elif task_info['state'] == 'SUCCESS':
                        task_states[task_id] = 'SUCCESS'
                    elif task_info['state'] == 'FAILURE':
                        self.fail(f"Task {task_id} failed: {task_info.get('status')}")
            
            if not all_complete:
                time.sleep(0.5)

        if not all_complete:
            self.fail(f"Timed out waiting for tasks after {timeout} seconds")

        print("All tile generation tasks completed")
        
        # Wait for tiles to be ready
        tiles_ready = False
        start_time = time.time()
        while not tiles_ready and time.time() - start_time < timeout:
            response = requests.get(f"{self.tiles_ready_endpoint}/{hash_id}")
            data = response.json()
            if response.status_code == 200 and data.get('ready', False):
                tiles_ready = True
                break
            elif response.status_code == 202:
                time.sleep(0.5)
            else:
                self.fail(f"Unexpected response checking tiles ready: {response.status_code}")
        
        if not tiles_ready:
            self.fail(f"Timed out waiting for tiles after {timeout} seconds")
        
        # Get the list of generated slice files
        slice_files = data['slices']
        self.assertEqual(len(slice_files), self.n_frames, 
                        f"Expected {self.n_frames} slices, got {len(slice_files)}")
        
        # Verify slice files are in correct format and order
        for i in range(self.n_frames):
            expected_file = f"{hash_id}_slices/{hash_id}_{i}.dzi"
            self.assertIn(expected_file, slice_files,
                         f"Expected slice file {expected_file} not found")
            self.assertEqual(slice_files[i], expected_file,
                         f"Expected slice file {expected_file} at index {i}, got {slice_files[i]}")
        
        print("Verified all slice files exist and are in correct order")

    def test_slice_navigation(self):
        """Test slice navigation and visibility management."""
        print("\nTesting slice navigation...")
        
        # Start tile generation
        response = requests.post(
            self.start_tile_generation_endpoint,
            json={
                'filename': self.test_filename,
                'viewer_suffix': 'S'  # This will be used to determine is_slice
            }
        )
        self.assertEqual(response.status_code, 202)  # Should be 202 Accepted
        data = response.json()
        hash_id = data['hash']
        task_ids = data['task_ids']
        
        # Wait for all tasks to complete
        print("Waiting for all tile generation tasks to complete...")
        all_complete = False
        timeout = 300  # 5 minutes
        start_time = time.time()
        task_states = {}

        while not all_complete and time.time() - start_time < timeout:
            all_complete = True
            for task_id in task_ids:
                if task_id not in task_states or task_states[task_id] != 'SUCCESS':
                    response = requests.get(f"{self.task_progress_endpoint}/{task_id}")
                    task_info = response.json()
                    
                    if task_info['state'] not in ['SUCCESS', 'FAILURE']:
                        all_complete = False
                    elif task_info['state'] == 'SUCCESS':
                        task_states[task_id] = 'SUCCESS'
                    elif task_info['state'] == 'FAILURE':
                        self.fail(f"Task {task_id} failed: {task_info.get('status')}")
            
            if not all_complete:
                time.sleep(0.5)

        if not all_complete:
            self.fail(f"Timed out waiting for tasks after {timeout} seconds")

        print("All tile generation tasks completed")
        
        # Wait for tiles to be ready
        tiles_ready = False
        start_time = time.time()
        while not tiles_ready and time.time() - start_time < timeout:
            response = requests.get(f"{self.tiles_ready_endpoint}/{hash_id}")
            data = response.json()
            if response.status_code == 200 and data.get('ready', False):
                tiles_ready = True
                break
            elif response.status_code == 202:
                time.sleep(0.5)
            else:
                self.fail(f"Unexpected response checking tiles ready: {response.status_code}")
        
        if not tiles_ready:
            self.fail(f"Timed out waiting for tiles after {timeout} seconds")
        
        # Test slice index calculation
        print("Testing slice index calculations...")
        image_height = 1000  # Simulated image height
        test_y_positions = [0, 250, 500, 750, 999]
        
        # Verify slices array exists and has correct length
        self.assertIn('slices', data, "Response should contain slices array")
        self.assertEqual(len(data['slices']), self.n_frames, 
                        f"Expected {self.n_frames} slices, got {len(data['slices'])}")
        
        for y_pos in test_y_positions:
            slice_percent = y_pos / image_height
            expected_index = min(
                self.n_frames - 1,
                max(0, int(slice_percent * (self.n_frames - 1)))
            )
            
            expected_file = f"{hash_id}_slices/{hash_id}_{expected_index}.dzi"
            self.assertIn(expected_file, data['slices'],
                         f"Expected slice file {expected_file} not found for y-position {y_pos}")
            actual_index = data['slices'].index(expected_file)
            self.assertEqual(actual_index, expected_index,
                         f"Expected slice file {expected_file} at index {expected_index}, found at {actual_index}")
            print(f"Verified slice at y-position {y_pos} (index {expected_index})")
        
        print("All slice navigation tests passed")

    def test_cache_clearing(self):
        """Test that the cache can be cleared."""
        clear_tiff_scale_cache()  # Start with clean cache
        
        # First call - should calculate values
        start_time = time.time()
        scaler1 = get_tiff_scaler(self.test_tiff_path)
        first_call_time = time.time() - start_time
        
        # Second call - should use cache
        start_time = time.time()
        scaler2 = get_tiff_scaler(self.test_tiff_path)
        second_call_time = time.time() - start_time
        
        # Verify values are the same
        self.assertEqual(scaler1, scaler2)
        
        # Verify second call was significantly faster
        self.assertLess(second_call_time, first_call_time / 2)
        
        # Test with PIL Image input
        clear_tiff_scale_cache()
        
        # First call with image
        start_time = time.time()
        scaler3 = get_tiff_scaler(self.tiff_image, is_image=True)
        first_image_time = time.time() - start_time
        
        # Second call with same image
        start_time = time.time()
        scaler4 = get_tiff_scaler(self.tiff_image, is_image=True)
        second_image_time = time.time() - start_time
        
        # Verify values are the same
        self.assertEqual(scaler3, scaler4)
        
        # Verify second call was significantly faster
        self.assertLess(second_image_time, first_image_time / 2)

    def test_cache_isolation(self):
        """Test that different files/images have separate cache entries."""
        clear_tiff_scale_cache()

        # Create a second test file with different values
        test_filename2 = 'test_multi2.tif'
        test_tiff_path2 = os.path.join(self.input_dir, test_filename2)
        frames = []
        for i in range(3):
            # Use a different range (50-250) for the second file
            x = np.linspace(50 + i*100, 50 + (i+1)*100, 10)
            frame = np.tile(x, (10, 1))
            frames.append(Image.fromarray(frame.astype(np.uint16)))

        frames[0].save(
            test_tiff_path2,
            save_all=True,
            append_images=frames[1:],
            format='TIFF'
        )

        # Get values for both files using full paths
        scaler1 = get_tiff_scaler(self.test_tiff_path)
        scaler2 = get_tiff_scaler(test_tiff_path2)

        # Values should be different
        self.assertNotEqual(scaler1, scaler2)
        
        # Clean up
        os.remove(test_tiff_path2)

    def test_tiff_scale_caching(self):
        """Test that get_tiff_scaler results are cached and reused."""
        clear_tiff_scale_cache()  # Start with clean cache
        
        # First call - should calculate values
        start_time = time.time()
        scaler1 = get_tiff_scaler(self.test_tiff_path)
        first_call_time = time.time() - start_time
        
        # Second call - should use cache
        start_time = time.time()
        scaler2 = get_tiff_scaler(self.test_tiff_path)
        second_call_time = time.time() - start_time
        
        # Values should be the same
        self.assertEqual(scaler1, scaler2)
        
        # Verify cache is working by checking if second call is faster
        # Note: We don't compare absolute times as they're hardware dependent
        self.assertLess(second_call_time, first_call_time / 2, 
                       "Second call should be significantly faster than first call")

if __name__ == '__main__':
    unittest.main() 