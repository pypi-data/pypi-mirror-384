import os
import sys
import pickle
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from reva_coregistration.warping import do_warp_image
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

def add_landmarks_to_image(img, landmarks, side='L'):
    # Create a drawing object
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    image_width, image_height = img.size
    # Calculate marker size based on image dimensions
    marker_size = int(min(img.size) * 0.01)  # 1% of smallest dimension
    
    for landmark in landmarks:
        # Determine if this is a target (microCT) or source (photo) image based on dimensions
        x = landmark[side]['x'] * image_width
        y = landmark[side]['y'] * image_height
            
        # Draw a filled red circle for each landmark
        draw.ellipse([x - marker_size, y - marker_size, 
                     x + marker_size, y + marker_size], 
                     fill='red', outline='red')
    
    return img

def load_sample_data():
    pickle_path = r"C:\Users\aaron\Downloads\xforms_1b2fc1399bc3b28971d5_9dbbf0ad760b57a3ec26 (2).pkl"
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    return data

def load_images():
    # Load images
    microct_path = r"F:\Projects\REVA Vagus\reva_downloads\sam-SR004-CR1.png"
    photo_path = r"F:\Projects\REVA Vagus\reva_downloads\SR004_postRemoval_wholeNerve_ROTATED.JPG"

    microct_img_raw = Image.open(microct_path)
    photo_img_raw = Image.open(photo_path)

    return microct_img_raw, photo_img_raw

def test_load_landmarks():
    # Load the pickle file
    pickle_path = r"C:\Users\aaron\Downloads\xforms_1b2fc1399bc3b28971d5_9dbbf0ad760b57a3ec26 (2).pkl"
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)

    # Extract data
    landmarks = data['landmarks']

    print(f"Loaded transformation data from {pickle_path}")
    print(f"Number of landmark pairs: {len(landmarks)}")

    # Let's inspect the structure of the first landmark
    print("\nFirst landmark structure:")
    print(landmarks[0])

    # Load images
    microct_img_raw, photo_img_raw = load_images()

    microct_img = add_landmarks_to_image(microct_img_raw, landmarks)
    photo_img = add_landmarks_to_image(photo_img_raw, landmarks, side='R')

    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 15))

    # Display images
    ax1.imshow(microct_img, cmap='gray')
    ax1.set_title('MicroCT MAP Image')
    ax1.axis('off')

    ax2.imshow(photo_img)
    ax2.set_title('Photo Image')
    ax2.axis('off')

    plt.tight_layout()
    plt.show()

def test_warp_photo():
    data = load_sample_data()
    transformation = data['transformation']
    landmarks = data['landmarks']
    target_width = data['target_image_width']
    target_height = data['target_image_height']
    source_width = data['source_image_width']
    source_height = data['source_image_height']
    
    microct_img_raw, photo_img_raw = load_images()

    photo_img_array = np.array(photo_img_raw)
    warped_photo_img = do_warp_image(photo_img_array, target_height, target_width, transformation)

    warped_photo_img_pil = Image.fromarray(warped_photo_img)

    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 15))

    # Display the warped photo image
    ax1.imshow(warped_photo_img_pil)
    ax1.set_title('Warped Photo Image')
    ax1.axis('off')

if __name__ == "__main__":
    # test_load_landmarks()
    test_warp_photo()