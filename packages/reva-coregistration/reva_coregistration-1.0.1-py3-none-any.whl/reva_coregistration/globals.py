LOG_LEVEL             = 'info'

MAX_LANDMARKS         = 150

# MIN_IMAGE_PIXELS      = 20_000 ** 2
# MAX_IMAGE_PIXELS      = 30_000 ** 2
MIN_SLICE_PIXELS      =  2_000 ** 2
# MAX_SIDE_LENGTH       = 65_500 # this comes from https://github.com/libjpeg-turbo/libjpeg-turbo/blob/abeca1f0cc638a6492d81f4c3b956c2dec817c3e/jmorecfg.h#L157
MAX_WARPED_PIXELS     = 1_000 ** 2

RBF_FUNCTION          = 'thin_plate'
RBF_SMOOTHNESS        = 2

DASK_BLOCK_SIZE       = (1024, 1024)
DASK_OVERLAP_PIXELS   = 30