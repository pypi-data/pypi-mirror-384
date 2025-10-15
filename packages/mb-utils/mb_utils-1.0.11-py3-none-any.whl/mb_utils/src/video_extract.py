## python file to extract video frames from a video/youtube file to image

from typing import Optional
from logging import Logger
import os


def write_vid_to_img(url : str,folder : str =None,logger : Optional[Logger]=None):
    """
    Function for converting video to img
    Args:
        url : str : url of the video file
        folder : str : folder to save the images
        logger : logger : logger object
    """

    if folder is None:
        folder = os.path.join(os.getcwd(),"video_frames")
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    try:
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(r'url')
        video.write_images_sequence(folder + "/frame%04d.png")
    except Exception as e:
        if logger:
            logger.error(e)
        else:
            print(e)
    
def download_yt_vid(url : str,folder: str = None,file_name : str ='yt_output.mp4',res = 'high',logger : Optional[Logger]=None):
    """
    Function for downloading youtube video
    Args:
        url : str : url of the youtube video
        folder : str : folder to save the video
        file_name : str : name of the (Default : yt_output.mp4)
        res : str : resolution of the video (Default : high), else get lowest resolution
        logger : logger : logger object
    """
    if folder is None:
        folder = os.path.join(os.getcwd(),"yt_videos")
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    try:
        from pytubefix import YouTube
        yt = YouTube(url)
        if res == 'high':
            ys = yt.streams.get_highest_resolution()
        else:
            ys = yt.streams.get_lowest_resolution()
        filepath = os.path.join(folder,file_name)
        ys.download(filepath)
    except Exception as e:
        if logger:
            logger.error(e)
        else:
            print(e)