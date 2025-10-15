##Functions related to terminal size
#Functions taken from mtbase : https://github.com/inteplus/mtbase/tree/master/mt/base 
import shutil


__all__ = ['stty_imgres', 'stty_size']


def stty_size() -> list:
    '''Gets the terminal size.
    Returns the Linux-compatible console's number of rows and number of characters per
    row. If the information does not exist, returns (72, 128).'''

    res = shutil.get_terminal_size(fallback=(128, 72))
    return [res[1], res[0]]


def stty_imgres() -> list:
    '''Gets the terminal resolution.
    Returns the Linux-compatible console's number of letters per row and the number of
    rows. If the information does not exist, returns (128, 72).'''

    res = shutil.get_terminal_size(fallback=(128, 72))
    return [res[0], res[1]]