def is_video(info) -> bool:
    """判断是否是视频
    Args:
        info (_type_): 扩展名或者文件信息

    Returns:
        bool: 判断结果
    """
    ext_list = ["mp4", "m4v", "mkv", "webm", "mov", "avi", "wmv", "mpg", "flv"]
    if info in ext_list:
        return True

    # todo 根据其他方式检测
    elif isinstance(info, dict):
        if info.get("ext") in ext_list:
            return True

    # 默认返回false
    return False
