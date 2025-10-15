##Function to verify the image
import PIL.Image as Image
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from tqdm.auto import tqdm

__all__ = ['verify_image']

def verify_image(image_paths: list, image_type=None, image_shape=None,logger=None,max_workers=16) -> list:
    """
    Function to verify the image. Checks Path, Type and Size of the image if the later two are provided.
    tqdm progress bar is used to show the progress and it updates every 1 second.
    Input:
        image_paths: list of paths to the images
        image_type (str : optional): type of the image
        image_shape (Tuple : optional): verify if image shape. (width, height) 
    Output:
        results (list : bool): lists of bools indicating if each image is valid. Also returns size_mismatch if image_shape is provided and not correct.
    """
    

    def verify_single_image(image_path,image_type=None, image_shape=None):
        if os.path.isfile(image_path):
            im = Image.open(image_path)
            if image_type and im.format != image_type.upper():
                return 'image_type_mismatch'
            elif not image_type and im.format not in ('JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'JPG'):
                return 'unknown_image_format'
            if image_shape and im.size != image_shape:  # PIL uses (width, height)
                    return 'image_shape_mismatch'
            im.close()
            return True
        else:
            return False
                    
    verify_func = partial(verify_single_image, image_type=image_type, image_shape=image_shape) ### partial function fixes the given arguments
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(verify_func, image_paths), total=len(image_paths),mininterval=1))
    if image_shape:
        if logger:
            logger.info('Image shape mismatch: {}'.format(results.count('image_shape_mismatch')))
        else:
            print('Image shape mismatch: {}'.format(results.count('image_shape_mismatch')))
    if image_type:
        if logger:
            logger.info('Image type mismatch: {}'.format(results.count('image_type_mismatch')))
        else:
            print('Image type mismatch: {}'.format(results.count('image_type_mismatch')))
    if logger:
        logger.info('Image not found: {}'.format(results.count(False)))
    else:
        print('Image not found: {}'.format(results.count(False)))
    return results