from .paths import get_output_path
from .logger import LOGGER
from PIL import Image
import hashlib
import os
import xml.etree.ElementTree as ET


# Image.MAX_IMAGE_PIXELS = 30_000 ** 2


def get_image_size(path: str):
    LOGGER.debug(f'🔗 Loading image size for {path}...')
    
    with Image.open(path) as img:
        width, height = img.size
    LOGGER.debug(f'🖼️ Image size loaded (width={width}, height={height}).')
    return width, height


def get_image_pixels(path: str):
    w, h = get_image_size(path)
    return w * h

image_hashes_cache = {}
def get_image_hash(full_path):
    global image_hashes_cache
    if full_path in image_hashes_cache: 
        LOGGER.debug(f'🔍 Found {full_path} in cache. Retrieving hash from cache...')
        return image_hashes_cache[full_path]

    LOGGER.debug(f"Calculating hash for image: {full_path}")
    hash_result = hashlib.sha256(open(full_path, 'rb').read()).hexdigest()
    LOGGER.debug(f"Generated hash: {hash_result}")
    image_hashes_cache[full_path] = hash_result
    return hash_result


def truncate_hash(hash):
    TRUNCATE_HASH_LENGTH = int(os.getenv('TRUNCATE_HASH_LENGTH', 20))
    if len(hash) > TRUNCATE_HASH_LENGTH:
        hash = hash[:TRUNCATE_HASH_LENGTH]
    return hash


upscaled_sizes_cache = {}
def get_upscaled_image_size(tiles_name: str):
    if tiles_name is None:
        LOGGER.warning('🚨 tiles_name is None. Returning None.')
        return None
    global upscaled_sizes_cache
    if tiles_name in upscaled_sizes_cache:
        LOGGER.debug(f'🔍 Found {tiles_name} in cache. Retrieving upscaled image size from cache...')
        return upscaled_sizes_cache[tiles_name]

    image_key = f'{tiles_name}.dzi'
    LOGGER.debug(f'🔗 Loading image size for {image_key}...')
    tiles_folder = get_output_path()
    LOGGER.debug(f'📝 {tiles_folder = }')
    
    # Handle slice paths differently
    if '_' in tiles_name:
        # Assuming format is hash_slicenum (e.g., 2c821...744_0)
        base_hash = tiles_name.rsplit('_', 1)[0]
        # For slices, look in the _slices subfolder
        local_path = os.path.join(tiles_folder, f"{base_hash}_slices", image_key)
    else:
        # Regular (non-slice) image path
        local_path = os.path.join(tiles_folder, image_key)
    
    LOGGER.debug(f'🔗 {local_path = }')
    
    LOGGER.info('🔍 Reading XML content from file...')
    with open(local_path, 'r') as xml_file:
        xml_content = xml_file.read()
    LOGGER.debug(f'📄 XML content successfully read. {xml_content = }')

    LOGGER.info('🔍 Parsing XML content to extract image size...')
    xml_content = xml_content.split('\n', 1)[1]
    root = ET.fromstring(xml_content)
    image_size_element = root.find('{http://schemas.microsoft.com/deepzoom/2008}Size')
    upscaled_image_width = int(image_size_element.get('Width'))
    upscaled_image_height = int(image_size_element.get('Height'))
    LOGGER.debug(f'📏 Upscaled image size extracted: width={upscaled_image_width}, height={upscaled_image_height}.')

    upscaled_sizes_cache[tiles_name] = (upscaled_image_width, upscaled_image_height)
    LOGGER.debug(f'📦 {tiles_name} added to cache with size: width={upscaled_image_width}, height={upscaled_image_height}.')

    return upscaled_image_width, upscaled_image_height
