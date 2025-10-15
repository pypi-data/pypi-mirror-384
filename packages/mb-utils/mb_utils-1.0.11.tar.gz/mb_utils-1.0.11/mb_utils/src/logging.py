from logging import *
import os
import logging.handlers
from colorama import Fore, Style
from colorama import init as _colorama_init
from .terminal import stty_size
_colorama_init()

__all__ = ['make_logger','logger']

def make_logger(name):
    """
    logger package for user
    Input:
        name: name of the logger
    Output:
        logger object
    """
    logger = getLogger(name)
    if logger is None:
        logger.addHandler(NullHandler())
    logger.setLevel(1) #getting all logs
    #basicConfig(filename='logger.log',filemode='w',level=INFO)

    # determine some max string lengths
    column_length = stty_size()[1]-13
    log_lvl_length = min(max(int(column_length*0.03), 1), 8)
    s1 = '{}.{}s '.format(log_lvl_length, log_lvl_length)
    column_length -= log_lvl_length
    s5 = '-{}.{}s'.format(column_length, column_length)
    
    os.mkdir('logs') if not os.path.exists('logs') else None
    should_roll_over = os.path.isfile('logs/logger.log')
    file_handler = logging.handlers.RotatingFileHandler('logs/logger.log',mode='w' ,maxBytes=1000000, backupCount=3)
    if should_roll_over:  # log already exists, roll over!
        file_handler.doRollover()
    file_handler.setLevel(DEBUG)
    file_formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    std_handler = StreamHandler()
    std_handler.setLevel(DEBUG)
    fmt_str = Fore.CYAN+'%(asctime)s '+Fore.LIGHTGREEN_EX+'%(levelname)'+s1+\
            Fore.LIGHTWHITE_EX+'%(message)'+s5+Fore.RESET
    formatter = Formatter(fmt_str)
    formatter.default_time_format = "%a %H:%M:%S" 
    std_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(std_handler)

    return logger


logger = make_logger('mb_utils')