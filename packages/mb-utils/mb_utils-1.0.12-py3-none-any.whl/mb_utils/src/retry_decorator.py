##function to retry a function if it fails
# Path: mb_utils/src/retry_decorator.py

__all__ = ['retry']

def retry(times, exceptions,logger=None):
    """
    Retry Decorator
    Retries the wrapped function/method `times` times if the exceptions listed
    in ``exceptions`` are thrown
    Input:
        times (int):  The number of times to repeat the wrapped function/method
        exceptions (tuple of exceptiosn):  The exceptions to catch
    Output:
        The wrapped function/method
    """
    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if logger:
                        logger.error(
                        'Exception thrown when attempting to run %s, attempt '
                        '%d of %d' % (func, attempt, times)
                    )
                    attempt += 1
            return func(*args, **kwargs)
        return newfn
    return decorator

##example of how to use the retry decorator
# @retry(times=3, exceptions=(ValueError, TypeError))
# def foo1():
#     print('Some code here ....')
#     print('Oh no, we have exception')
#     raise ValueError('Some error')

# foo1()