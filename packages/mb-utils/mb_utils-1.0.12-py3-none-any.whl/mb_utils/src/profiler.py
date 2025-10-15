import cProfile
import subprocess
import os
import functools
import sys

__all__ = ['run_with_snakeviz','line_profile']

def run_with_snakeviz(func, *args, save_only=False,file_path=None, **kwargs):
    """
    Profiles a function, saves to 'profiler.prof' in the current directory,
    and optionally opens SnakeViz.

    Args:
        func: The function to profile.
        *args, **kwargs: Arguments to pass to the function.
        save_only (bool): If True, only saves the file and does not launch SnakeViz.
        file_path (str): Path to save the profile file. If None, saves to 'profiler.prof' in the current directory.
    
    Examples:
    @run_with_snakeviz
    def my_function():
        pass
    """
    if file_path is None:
        file_path = os.path.join(os.getcwd(), "profiler.prof")

    profiler = cProfile.Profile()
    profiler.enable()
    try:
        result = func(*args, **kwargs)
    finally:
        profiler.disable()
        profiler.dump_stats(file_path)
        print(f"[Profiler] Saved to {file_path}")

        if not save_only:
            print("[Profiler] Launching SnakeViz")
            subprocess.run(["snakeviz", file_path])

    return result

def line_profile(func):
    """
    A decorator that profiles the function line-by-line using line_profiler.
    Compatible with IPython/Jupyter. 

    Examples:
    @line_profile
    def my_function():
        pass
    """
    from line_profiler import LineProfiler
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = LineProfiler()
        profiler.add_function(func)
        result = profiler(func)(*args, **kwargs)
        profiler.print_stats(stream=sys.stdout)
        return result
    return wrapper