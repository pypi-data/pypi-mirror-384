##Extra functions - batch creation, timer wrapper, etc.
import time

__all__ = ['timer', 'batch_generator', 'batch_create']

def timer(func,logger=None):
    """
    Decorator to time a function
    Input:
        func: function to be timed
    """
    def wrapper(*args,**kwargs):
        before = time.time()
        a = func(*args,**kwargs)
        if logger:
            logger.info('function time : ',time.time() - before, "seconds" )
        return a
    return wrapper

def batch_generator(iterable, batch_size):
    """
    Generator to create batches of a given size from an iterable
    Input:
        iterable: iterable to be batched
        batch_size: size of the batches
    Output:
        batch: batch of the given size
    """
    l = len(iterable)
    for ndx in range(0, l, batch_size):
        yield iterable[ndx:min(ndx + batch_size, l)]

def batch_create(l, n,logger=None):
    """
    Create batches in a list of a size from a given list
    Input:
        l: list to be batched
        n: size of the batches
    Output:
        batch(list): batch of the given size
    """
    batch_create_list=[]
    for i in range(0, len(l), n):
        batch_create_list.append(l[i:i+n])
    if logger:
        logger.info("batches created : {}".format(len(batch_create_list)))
    return batch_create_list