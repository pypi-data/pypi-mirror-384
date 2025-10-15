##Function to check paths

import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from tqdm.auto import tqdm
__all__ = ['check_path']

def check_path(path,logger=None,path_column=None,max_threads=16) -> bool:
    """
    Function to check the path.
    Tqdm progress bar is used to show the progress and it updates every 1 second.
    Input:
        path: path to be checked (list or pandas.DataFrame).
        path_column: column name if path is pandas.DataFrame (str, optional)
        logger: logger object (optional)
        max_threads: maximum number of threads to use (int, optional, default=16)
    Output:
        results: list of bools indicating if each path exists.
    """
    if type(path) != list:
        if type(path) != pd.DataFrame or type(path) != pd.core.series.Series:
            raise TypeError("Input should be a list or pandas.DataFrame or pandas.Series")
        path = path[path_column].tolist()
    
    def check_single_path(p):
        return os.path.exists(p)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        results = list(tqdm(executor.map(check_single_path, path), total=len(path), mininterval=1))
        
    if logger:
        logger.info('Path not found: {}'.format(results.count(False)))
    else:
        print('Path not found: {}'.format(results.count(False)))
    return results