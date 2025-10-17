import math
import warnings
from functools import wraps

import cv2
import numpy as np


def _deprecated(func):
    """
    这是一个装饰器，用于标记函数为已弃用。当使用该函数时，会发出警告。

    Args:
        func (function): 被装饰的函数。

    Returns:
        function: 包装后的新函数。
    """

    @wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter("always", DeprecationWarning)  # 关闭过滤器
        warnings.warn(
            f"调用已弃用的函数 {func.__name__}.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter("default", DeprecationWarning)  # 恢复过滤器
        return func(*args, **kwargs)

    return new_func


def _calculate_target_size(height, width, align_function, kwargs):
    """
    根据参数计算目标尺寸

    Args:
        height (int): 图像高度
        width (int): 图像宽度
        align_function: 对齐函数
        kwargs (dict): 参数字典

    Returns:
        tuple: (target_width, target_height) 或 (None, None)
    """
    if "hard" in kwargs:
        return _handle_hard_size(kwargs["hard"], align_function)
    elif "short" in kwargs:
        return _handle_short_size(height, width, kwargs["short"], align_function)
    elif "long" in kwargs:
        return _handle_long_size(height, width, kwargs["long"], align_function)
    elif "height" in kwargs:
        return _handle_height_size(height, width, kwargs["height"], align_function)
    elif "width" in kwargs:
        return _handle_width_size(height, width, kwargs["width"], align_function)
    elif "area" in kwargs:
        return _handle_with_area(height, width, kwargs["area"], align_function)
    else:
        raise ValueError(f"Invalid kwargs: {kwargs}")


def _handle_hard_size(hard_value, align_function):
    """处理硬尺寸参数"""
    if isinstance(hard_value, int):
        target_size = align_function(hard_value)
        return target_size, target_size
    else:
        target_width, target_height = hard_value
        return align_function(target_width), align_function(target_height)


def _handle_short_size(height, width, short_side, align_function):
    """处理短边尺寸参数"""
    if height > width:
        target_width = short_side
        target_height = align_function(height / width * target_width)
    else:
        target_height = short_side
        target_width = align_function(width / height * target_height)
    return target_width, target_height


def _handle_long_size(height, width, long_side, align_function):
    """处理长边尺寸参数"""
    if height < width:
        target_width = long_side
        target_height = align_function(height / width * target_width)
    else:
        target_height = long_side
        target_width = align_function(width / height * target_height)
    return target_width, target_height


def _handle_height_size(height, width, target_height, align_function):
    """处理高度参数"""
    target_height = align_function(target_height)
    target_width = align_function(width / height * target_height)
    return target_width, target_height


def _handle_width_size(height, width, target_width, align_function):
    """处理宽度参数"""
    target_width = align_function(target_width)
    target_height = align_function(height / width * target_width)
    return target_width, target_height


def _handle_with_area(height, width, area, align_function):
    """处理面积参数"""
    r = width / height
    new_height = np.sqrt(area / r)
    new_width = r * new_height
    return align_function(new_width), align_function(new_height)


def _limit_max_size(target_width, target_height, max_length):
    """
    限制最大尺寸

    Args:
        target_width (int): 目标宽度
        target_height (int): 目标高度
        max_length (int): 最大长度

    Returns:
        tuple: 限制后的 (target_width, target_height)
    """
    if target_width > max_length:
        print(f"[size_pre_process] target_width({target_width}->{max_length})")
        target_width = max_length
    if target_height > max_length:
        print(f"[size_pre_process] target_height({target_height}->{max_length})")
        target_height = max_length
    return target_width, target_height


def _get_interpolation_method(target_width, target_height, height, width, kwargs):
    """
    获取插值方法

    Args:
        target_width (int): 目标宽度
        target_height (int): 目标高度
        height (int): 原始高度
        width (int): 原始宽度
        kwargs (dict): 参数字典

    Returns:
        int: 插值方法
    """
    interpolation_method = kwargs.get("interpolation", None)
    if interpolation_method is None:
        if target_width * target_height > height * width:
            interpolation_method = cv2.INTER_LINEAR
        else:
            interpolation_method = cv2.INTER_AREA
    return interpolation_method


def _resize_image_with_interpolation(image, target_width, target_height, **kwargs):
    """
    使用指定的插值方法对图像进行resize

    Args:
        image (numpy.ndarray): 要调整大小的输入图像
        target_width (int): 目标宽度
        target_height (int): 目标高度
        **kwargs: 调整大小的附加关键字参数
            - interpolation (int, optional): 调整大小的插值方法,默认为None

    Returns:
        numpy.ndarray: 调整大小后的图像
    """
    height, width = image.shape[:2]

    # 确定插值方法
    interpolation_method = _get_interpolation_method(
        target_width, target_height, height, width, kwargs
    )

    # 执行图像缩放
    return cv2.resize(
        image, (target_width, target_height), interpolation=interpolation_method
    )


def _largest_rotated_rect(w, h, angle):
    """
    计算旋转后能完全显示在原图内的最大矩形
    w, h: 原图宽高
    angle: 旋转角度（弧度）
    """
    if w <= 0 or h <= 0:
        return 0, 0

    width_is_longer = w >= h
    side_long, side_short = (w, h) if width_is_longer else (h, w)

    sin_a, cos_a = abs(math.sin(angle)), abs(math.cos(angle))

    if side_short <= 2.0 * sin_a * cos_a * side_long:
        # 半对角线到长边的夹角
        x = 0.5 * side_short
        wr = x / sin_a
        hr = x / cos_a
    else:
        cos_2a = cos_a * cos_a - sin_a * sin_a
        wr = (w * cos_a - h * sin_a) / cos_2a
        hr = (h * cos_a - w * sin_a) / cos_2a

    return abs(wr), abs(hr)
