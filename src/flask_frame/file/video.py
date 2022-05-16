def is_video(ext):
    """判断是否是视频"""
    if ext in ["mp4", "m4v", 'mkv', 'webm', 'mov', 'avi', 'wmv', 'mpg', 'flv']:
        return True

    return False
