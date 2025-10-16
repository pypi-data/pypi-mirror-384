import unittest
import os
import time
import requests
import tempfile
import shutil
from PIL import Image
import numpy as np
from unittest.mock import patch
import pyvips

class TestTileGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Use actual mounted directories
        cls.input_dir = r"C:\Users\aaron\Downloads\reva_downloads"
        cls.output_dir = r"C:\Users\aaron\Downloads\reva_tiles"
        
        # Test images that should exist in the input directory
        cls.test_images = [
            'SR004_postRemoval_wholeNerve_ROTATED.JPG',
            'sam-SR004-CR1.png'
        ]
        
        # Verify test images exist
        for img_name in cls.test_images:
            img_path = os.path.join(cls.input_dir, img_name)
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Test image not found: {img_path}")
        
        # API endpoints
        cls.base_url = "http://localhost:5001"
        cls.start_tile_generation_endpoint = f"{cls.base_url}/start-tile-generation"
        cls.tiles_ready_endpoint = f"{cls.base_url}/tiles-ready"
        cls.task_progress_endpoint = f"{cls.base_url}/task-progress"
        cls.viewer_progress_endpoint = f"{cls.base_url}/slices-task-progress"

        # Test if server is running
        try:
            response = requests.get(cls.base_url)
            if response.status_code not in [200, 404]:
                raise ConnectionError("Flask server is not running")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Flask server is not running")

    def setUp(self):
        """Set up before each test."""
        # Set up path mocks to use actual directories
        self.input_patcher = patch('reva_coregistration.paths.get_input_path')
        self.output_patcher = patch('reva_coregistration.paths.get_output_path')
        
        self.mock_input_path = self.input_patcher.start()
        self.mock_output_path = self.output_patcher.start()
        
        # Set mock paths to actual mounted directories
        self.mock_input_path.return_value = "/input"  # Docker container path
        self.mock_output_path.return_value = "/tiles"  # Docker container path

    def tearDown(self):
        """Clean up after each test."""
        # Stop all mocks
        self.input_patcher.stop()
        self.output_patcher.stop()

    @classmethod
    def tearDownClass(cls):
        """Clean up test files."""
        # No need to clean up since we're using actual directories
        pass

    def verify_progress_response(self, progress):
        """Helper method to verify progress response structure."""
        required_fields = ['state', 'current', 'total', 'status', 'stage', 'fraction_complete']
        for field in required_fields:
            self.assertIn(field, progress, f"Progress response missing required field: {field}")
        
        self.assertGreaterEqual(progress['current'], 0)
        self.assertGreaterEqual(progress['total'], progress['current'])
        self.assertGreaterEqual(progress['fraction_complete'], 0.0)
        self.assertLessEqual(progress['fraction_complete'], 1.0)
    
    def wait_for_tiles_ready(self, file_hash, timeout=300):
        """Wait for tiles to be ready with timeout."""
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                self.fail(f"Timed out waiting for tiles after {timeout} seconds")
            
            response = requests.get(f"{self.tiles_ready_endpoint}/{file_hash}")
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('ready', False):
                print(f"✅ Tiles are ready for hash: {file_hash}")
                return True
            elif response.status_code == 202:
                print(f"⏳ Tiles still generating for hash: {file_hash}")
                time.sleep(0.5)  # Increased delay to allow for progress updates
            else:
                print(f"❌ Unexpected response checking tiles ready: {response.status_code}")
                print(f"Response: {response.text}")
                self.fail(f"Unexpected response checking tiles ready: {response.status_code}")
    
    def start_tile_generation_and_wait(self, filename, viewer_id):
        """Helper function to start tile generation and wait for completion."""
        print(f"\nStarting tile generation for: {filename}")
        
        # Start tile generation
        data = {
            'filename': filename,
            'viewer_suffix': viewer_id
        }
        response = requests.post(self.start_tile_generation_endpoint, json=data)
        if response.status_code not in [200, 202]:
            print(f"Response: {response.json()}")
            self.fail(f"Tile generation request failed with status {response.status_code}")
        
        data = response.json()
        hash_id = data['hash']
        task_ids = data['task_ids']
        
        # If no task IDs, tiles already exist
        if not task_ids:
            print("Tiles already exist, no tasks to monitor")
            # Return a simulated successful progress update
            return [{
                'state': 'SUCCESS',
                'current': 100,
                'total': 100,
                'status': 'Tiles already exist',
                'stage': 'finished',
                'fraction_complete': 1.0
            }]
        
        # Monitor task progress
        progress_updates = []
        all_complete = False
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while not all_complete and time.time() - start_time < timeout:
            all_complete = True
            for task_id in task_ids:
                response = requests.get(f"{self.task_progress_endpoint}/{task_id}")
                progress = response.json()
                progress_updates.append(progress)
                print(f"Task state: {progress.get('state')}, Status: {progress.get('status')}")
                
                if progress['state'] not in ['SUCCESS', 'FAILURE']:
                    all_complete = False
                elif progress['state'] == 'FAILURE':
                    self.fail(f"Task failed: {progress.get('status')}")
            
            if not all_complete:
                time.sleep(0.5)
        
        if not all_complete:
            self.fail(f"Timed out waiting for tasks after {timeout} seconds")
        
        # Check if tiles are ready
        response = requests.get(f"{self.tiles_ready_endpoint}/{hash_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ready', False))
        
        return progress_updates
    
    def test_single_image_tile_generation(self):
        """Test tile generation with progress tracking for a single image."""
        test_image = self.test_images[0]
        viewer_id = "L"
        
        print(f"\nTesting tile generation for: {test_image}")
        start_time = time.time()
        
        progress_updates = self.start_tile_generation_and_wait(test_image, viewer_id)
        
        end_time = time.time()
        print(f"Tile generation took {end_time - start_time:.2f} seconds")
        
        self.assertTrue(len(progress_updates) > 0, "Should have received progress updates")
        
        # Verify progress sequence
        progress_values = [update.get('fraction_complete', 0) for update in progress_updates]
        has_intermediate = any(0.4 <= p <= 0.9 for p in progress_values)  # Check for values in the 40-90% range
        self.assertTrue(has_intermediate, "Should have received intermediate progress updates in the 40-90% range")
        
        # Verify final state
        final_update = progress_updates[-1]
        self.assertEqual(final_update['state'], 'SUCCESS')
        self.assertEqual(final_update['fraction_complete'], 1.0)
        
        print(f"\nReceived {len(progress_updates)} progress updates")
        print("Progress values:", [f"{p*100:.1f}%" for p in progress_values])
        print(f"Final status: {final_update.get('status')}")
    
    def test_concurrent_image_tile_generation(self):
        """Test generating tiles for multiple images concurrently."""
        print("\nTesting concurrent tile generation")
        start_time = time.time()
        
        tasks = []
        for i, test_image in enumerate(self.test_images):
            viewer_id = "L" if i == 0 else "R"
            tasks.append((test_image, viewer_id))
        
        all_progress = []
        for filename, viewer_id in tasks:
            progress = self.start_tile_generation_and_wait(filename, viewer_id)
            all_progress.append(progress)
        
        end_time = time.time()
        print(f"Concurrent tile generation took {end_time - start_time:.2f} seconds")
        
        for i, progress_updates in enumerate(all_progress):
            self.assertTrue(len(progress_updates) > 0,
                          f"Should have received progress updates for {self.test_images[i]}")
            print(f"\nImage {self.test_images[i]}:")
            print(f"Received {len(progress_updates)} progress updates")
            print(f"Final status: {progress_updates[-1].get('status')}")
    
    def test_task_cancellation(self):
        """Test cancellation of a running task."""
        test_image = self.test_images[0]
        viewer_id = "L"
        
        print(f"\nTesting task cancellation for: {test_image}")
        
        # Start the task
        data = {
            'filename': test_image,
            'viewer_suffix': viewer_id
        }
        response = requests.post(self.start_tile_generation_endpoint, json=data)
        self.assertIn(response.status_code, [200, 202])
        
        start_data = response.json()
        print(f"Start response: {start_data}")
        
        self.assertIn('task_ids', start_data)
        self.assertIn('hash', start_data)
        
        # If no task IDs, tiles already exist
        if not start_data['task_ids']:
            print("Tiles already exist, skipping cancellation test")
            return
        
        task_id = start_data['task_ids'][0]
        max_wait = 30  # Maximum time to wait for task to start
        start_time = time.time()
        
        # Wait for task to start or complete
        print("Waiting for task to start or complete...")
        task_state = None
        while True:
            if time.time() - start_time > max_wait:
                self.fail(f"Task did not start or complete within {max_wait} seconds")
            
            response = requests.get(f"{self.task_progress_endpoint}/{task_id}")
            self.assertEqual(response.status_code, 200)
            progress = response.json()
            task_state = progress.get('state')
            print(f"Task state: {task_state}, Status: {progress.get('status')}")
            
            if task_state in ['STARTED', 'PROGRESS', 'SUCCESS']:
                print(f"Task entered state: {task_state}")
                break
            
            time.sleep(0.1)
        
        # If task completed successfully (tiles already existed), we can't test cancellation
        if task_state == 'SUCCESS':
            print("Task completed successfully (tiles likely already existed), skipping cancellation test")
            return
        
        # Cancel the task
        print("Cancelling task...")
        cancel_response = requests.post(f"{self.task_progress_endpoint}/{task_id}/cancel")
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.json().get('status'), 'canceled')
        
        # Wait for task to be marked as cancelled
        print("Waiting for task to be cancelled...")
        start_time = time.time()
        while True:
            if time.time() - start_time > max_wait:
                self.fail(f"Task was not cancelled within {max_wait} seconds")
            
            response = requests.get(f"{self.task_progress_endpoint}/{task_id}")
            self.assertEqual(response.status_code, 200)
            progress = response.json()
            print(f"Task state: {progress.get('state')}, Status: {progress.get('status')}")
            
            # Check for cancellation states
            if (progress.get('state') in ['REVOKED', 'FAILURE'] and 
                'cancel' in progress.get('status', '').lower()):
                print("Task successfully cancelled")
                break
            
            time.sleep(0.1)
        
        # Verify final state
        response = requests.get(f"{self.task_progress_endpoint}/{task_id}")
        final_state = response.json()
        self.assertIn(final_state.get('state'), ['REVOKED', 'FAILURE'])
        self.assertIn('cancel', final_state.get('status', '').lower())
    
    def test_error_handling(self):
        """Test error handling in progress tracking."""
        # Test with non-existent task ID
        response = requests.get(f"{self.task_progress_endpoint}/nonexistent-task-id")
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['state'], 'PENDING')
        self.assertEqual(response_data['status'], 'Task is waiting to start...')
        
        # Test with invalid file
        data = {
            'filename': 'nonexistent.jpg',
            'viewer_suffix': 'L'
        }
        response = requests.post(self.start_tile_generation_endpoint, json=data)
        self.assertEqual(response.status_code, 500)
        error_data = response.json()
        self.assertIn('error', error_data)

class TestPyvipsProgress(unittest.TestCase):
    """Focused test class for verifying pyvips progress reporting functionality."""
    
    def setUp(self):
        # Use the same paths as the main test class
        self.test_images_dir = r"C:\Users\aaron\Downloads\reva_downloads"
        self.output_dir = r"C:\Users\aaron\Downloads\reva_tiles"
        self.test_image = "SR004_postRemoval_wholeNerve_ROTATED.JPG"
        
        # Ensure test image exists
        self.image_path = os.path.join(self.test_images_dir, self.test_image)
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Test image not found: {self.image_path}")
            
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def test_pyvips_progress_reporting(self):
        """Test that we can get progress updates from pyvips during dzsave."""
        # Create a progress tracking list
        progress_updates = []
        output_path = None
        
        def eval_handler(image, progress=None):
            """Handler for eval signal from pyvips"""
            try:
                if progress is not None:
                    # Try to get the fraction value from the progress object
                    try:
                        # Print the progress object to see what attributes it has
                        print(f"Progress object: {dir(progress)}")
                        progress_val = 0  # Default value
                        
                        # First try to get the percent directly
                        if hasattr(progress, 'percent'):
                            progress_val = float(progress.percent)
                        # Then try to get the fraction and convert to percent
                        elif hasattr(progress, 'run'):
                            progress_val = (float(progress.run) / float(progress.eta)) * 100 if progress.eta > 0 else 0
                        
                        progress_updates.append(progress_val)
                        # Only print if progress has changed by at least 1%
                        if len(progress_updates) == 1 or progress_val - progress_updates[-2] >= 1:
                            print(f"Progress update: {progress_val:.1f}%")
                    except Exception as e:
                        print(f"Error getting progress value: {str(e)}")
                        progress_val = 0
            except Exception as e:
                print(f"Error in progress handler: {str(e)}")
            return 0  # Return 0 to continue, non-zero to abort
        
        try:
            print("\nLoading image with pyvips...")
            image = pyvips.Image.new_from_file(self.image_path)
            print(f"Image size: {image.width}x{image.height}")
            
            # Set up progress monitoring
            image.set_progress(True)
            image.signal_connect('eval', eval_handler)
            
            print("\nStarting dzsave operation...")
            output_path = os.path.join(self.output_dir, "progress_test")
            image.dzsave(output_path,
                        suffix='.jpg[Q=80]',
                        tile_size=256,
                        overlap=1)
            
            # Verify we got progress updates
            self.assertTrue(len(progress_updates) > 0, 
                          "Should have received progress updates")
            
            # Verify progress values are in expected range
            for progress in progress_updates:
                self.assertGreaterEqual(progress, 0)
                self.assertLessEqual(progress, 100)
            
            # Verify we got updates showing progression
            has_intermediate = any(0 < p < 100 for p in progress_updates)
            self.assertTrue(has_intermediate,
                          "Should have received intermediate progress values")
            
            print(f"\nReceived {len(progress_updates)} progress updates")
            print("First few updates:", progress_updates[:5])
            print("Last few updates:", progress_updates[-5:])
            print("\nProgress distribution:")
            ranges = [(0,25), (25,50), (50,75), (75,100)]
            for start, end in ranges:
                count = sum(1 for p in progress_updates if start <= p < end)
                print(f"{start}-{end}%: {count} updates")
            
        finally:
            # Clean up test files
            if output_path:
                dzi_file = output_path + ".dzi"
                tiles_dir = output_path + "_files"
                
                if os.path.exists(dzi_file):
                    os.remove(dzi_file)
                if os.path.exists(tiles_dir):
                    import shutil
                    shutil.rmtree(tiles_dir)
            
            # Reset progress monitoring
            if 'image' in locals():
                image.set_progress(False)

if __name__ == '__main__':
    unittest.main() 