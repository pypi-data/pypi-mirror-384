from .logger import LOGGER
import os


TILES_ENDPOINT = os.getenv('TILES_ENDPOINT', '/tiles')
IMAGES_ENDPOINT = os.getenv('IMAGES_ENDPOINT', '/input')


def get_output_path():
    output_path = TILES_ENDPOINT
    LOGGER.debug(f"Using output path: {output_path}")
    return output_path


def get_input_path():
    input_path = IMAGES_ENDPOINT
    LOGGER.debug(f"Using input path: {input_path}")
    return input_path
