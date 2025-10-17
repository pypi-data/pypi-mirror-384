import os
import math
import time
import shutil
import base64
import random
import hashlib
import inspect
import tempfile
import argparse
import os.path as osp
from datetime import datetime
from multiprocessing import Pool
from functools import partial, wraps
from contextlib import contextmanager
from typing import List, Optional, Union

# 可选导入
try:
    import cv2
except ImportError:
    cv2 = None
    print("cv2 not installed.")

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
    print("tqdm not installed.")

try:
    import yaml
except ImportError:
    yaml = None
    print("yaml not installed.")

try:
    import torch
except ImportError:
    torch = None
    print("torch not installed.")

try:
    import psutil
except ImportError:
    psutil = None
    print("psutil not installed.")

try:
    import numpy as np
except ImportError:
    np = None
    print("numpy not installed.")

try:
    import matplotlib.pylab as plt
    import matplotlib.font_manager as fm
except ImportError:
    plt = None
    fm = None
    print("matplotlib not installed.")

try:
    from PIL import __version__ as pl_version
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    pl_version = None
    Image = ImageDraw = ImageFont = None
    print("Pillow not installed.")

from .utils import (
    _calculate_target_size,
    _limit_max_size,
    _resize_image_with_interpolation,
    _largest_rotated_rect,
)

MB_UNIT = 1 << 20
GB_UNIT = 1 << 30
NUM_THREADS = min(8, max(1, os.cpu_count() - 1))


# ===============context manager===============
@contextmanager
def TrackGpuMemory(name=""):
    """上下文管理 GPU 显存使用情况"""
    try:
        # 清理历史峰值记录
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        # 记录开始时显存
        print(f">>>>>>>>>>[{name}] 显存统计开始")
        start_mem = torch.cuda.memory_allocated() / GB_UNIT
        yield  # 让执行权交回给 with 语句内的代码
    finally:
        torch.cuda.synchronize()
        end_mem = torch.cuda.memory_allocated() / GB_UNIT
        peak_mem = torch.cuda.max_memory_allocated() / GB_UNIT
        print(f"[{name}] Begin: {start_mem:.2f} GB")
        print(f"[{name}] Finish: {end_mem:.2f} (+{end_mem - start_mem:.2f}) GB")
        print(f"[{name}] Peak: {peak_mem:.2f} (+{peak_mem - start_mem:.2f}) GB")
        print(f"[{name}] 显存统计结束>>>>>>>>>>")


@contextmanager
def TrackTime(name=""):
    """上下文管理执行耗时"""
    try:
        print(f">>>>>>>>>>[{name}] 耗时统计开始")
        start_time = time.perf_counter()
        yield  # 让执行权交回给 with 语句内的代码
    finally:
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print(f"[{name}] {elapsed_time:.4f}s 耗时统计结束>>>>>>>>>>")


def track_time(name: str = None):
    """
    装饰器：统计函数/协程执行时间

    Args:
        name (str, optional): 自定义名称；默认为函数名

    用法示例:
        @track_time()
        def my_fn():
            pass

        @track_time("数据处理")
        def data_process():
            pass
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            # 异步版本
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                tag = name or func.__name__
                start_time = time.perf_counter()
                result = await func(*args, **kwargs)
                elapsed_time = time.perf_counter() - start_time
                print(f"========== 耗时统计 ==========")
                print(f"[{tag}] {elapsed_time:.4f}s")
                return result

            return async_wrapper
        else:
            # 同步版本
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                tag = name or func.__name__
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed_time = time.perf_counter() - start_time
                print(f"========== 耗时统计 ==========")
                print(f"[{tag}] {elapsed_time:.4f}s")
                return result

            return sync_wrapper

    return decorator


def auto_select_gpu(required_memory_gb=30):
    """
    自动选择显存满足需求的卡，并设置 os.environ["CUDA_VISIBLE_DEVICES"]。
    如果没有满足需求的卡，则选择显存最多的那张卡。
    如果已经手动设置了 CUDA_VISIBLE_DEVICES，则直接使用设置的值。

    参数:
        required_memory_gb (int): 需要的显存量，单位是 GB。默认为 30GB。

    返回:
        str: 选择的 GPU 索引（或用户预设的 CUDA_VISIBLE_DEVICES）。
    """

    # 如果已设置 CUDA_VISIBLE_DEVICES，则直接使用
    if (
        "CUDA_VISIBLE_DEVICES" in os.environ
        and os.environ["CUDA_VISIBLE_DEVICES"].strip()
    ):
        gpu_setting = os.environ["CUDA_VISIBLE_DEVICES"].strip()
        print(f"CUDA_VISIBLE_DEVICES already set to {gpu_setting}, using this setting.")
        return gpu_setting

    try:
        import pynvml
    except:
        print("Auto Select GPU failed, please run: pip install nvidia-ml-py")
        return

    try:
        # 初始化 NVML
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()

        # 将所需的显存量转换为字节
        required_memory_bytes = required_memory_gb * 1024 * 1024 * 1024

        # 遍历所有 GPU，找出满足需求的卡
        max_free_mem = 0
        max_free_idx = 0
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)

            # 如果当前卡的可用显存满足需求，直接返回该卡
            if meminfo.free >= required_memory_bytes:
                pynvml.nvmlShutdown()
                os.environ["CUDA_VISIBLE_DEVICES"] = str(i)
                print(
                    f"Selected GPU {i} with {meminfo.free / 1024**3:.2f} GB free memory."
                )
                return str(i)

            # 记录显存最多的卡
            if meminfo.free > max_free_mem:
                max_free_mem = meminfo.free
                max_free_idx = i

        # 如果没有任何卡满足需求，则选择显存最多的卡
        pynvml.nvmlShutdown()
        os.environ["CUDA_VISIBLE_DEVICES"] = str(max_free_idx)
        print(
            f"Warning: No GPU has enough free memory ({required_memory_gb} GB). "
            f"Selected GPU {max_free_idx} with {max_free_mem / 1024**3:.2f} GB free memory."
        )
        return str(max_free_idx)

    except Exception as e:
        # 如果出现异常，默认选择 GPU 0
        print(
            "Warning: Could not determine GPU with most free memory, defaulting to device 0. Error:",
            e,
        )
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        return "0"


def export_to_video(
    frames: List[np.ndarray], output_video_path: str, fps: int = 10
) -> str:
    """Export a sequence of frames to a video file.

    Each frame should be a NumPy array in BGR format with dtype=uint8.

    Args:
        frames (List[np.ndarray]): List of frames, each frame is a NumPy array
            with shape (height, width, channels) and dtype uint8, in BGR order.
        output_video_path (str): Path to the output video file.
        fps (int, optional): Frames per second for the output video. Default is 10.

    Returns:
        str: Path to the saved video file.

    Raises:
        ValueError: If `frames` is empty or frame shape/channel count is invalid.
    """
    if not frames:
        raise ValueError("`frames` list must not be empty.")
    if frames[0].ndim != 3 or frames[0].shape[2] != 3:
        raise ValueError("Each frame must have shape (height, width, 3).")

    fps = int(fps)
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    for frame in tqdm(frames, total=len(frames)):
        if frame.shape != (height, width, 3):
            raise ValueError("All frames must have the same shape as the first frame.")
        video_writer.write(frame)

    video_writer.release()
    return output_video_path


# =========Files:文件移动和写入============


def get_tmp_file(suffix):
    return tempfile.NamedTemporaryFile(suffix=suffix).name


def multi_process(process_func, data_list, num_workers=1):
    """Run a function in multiple processes.

    Args:
        process_func (function): 需要并行处理的方法.
        data_list (list): 待处理的数据列表.
        num_workers (int, optional): 进程数,默认为1.

    Example:
        def process_func(args):
            worker_idx, data_chunk = args
            # 处理逻辑

        multi_process(process_func, data_list, num_workers=4)
    """
    if num_workers == 1:
        results = [process_func([0, data_list])]
    else:
        total_size = len(data_list)
        chunk_size = int(np.ceil(total_size / num_workers))

        task_args = []
        for worker_idx in range(num_workers):
            chunk_start = worker_idx * chunk_size
            chunk_end = min(chunk_start + chunk_size, total_size)
            task_args.append([worker_idx, data_list[chunk_start:chunk_end]])

        with Pool(num_workers) as pool:
            results = pool.map(process_func, task_args)
    return results


def merge_path(path, flag, interval="_", ignore=None):
    """Merge a path from a specific flag.

    Args:
        path (str):The original path.
        flag (str):The flag to start merging from.
        interval (str):
        ignore (list):Ignore parts

    Returns:
        str:The merged path starting from the flag.
    """
    assert isinstance(path, str)
    if ignore is None:
        ignore = []
    path_parts = path.split(os.sep)
    flag_index = path_parts.index(flag)
    path_parts = path_parts[flag_index:]
    l = len(path_parts)
    ignore = [x % l for x in ignore]
    path_parts = [x for i, x in enumerate(path_parts) if i not in ignore]
    return interval.join(path_parts)


def move_file_pair(
    path,
    dst_folder,
    dst_name=None,
    postfixes=None,
    copy=True,
    execute=False,
    move_empty_file=True,
    delete_empty_file=False,
    ignore_failed=False,
    overwrite=False,
):
    """Move or copy file pairs to a destination folder.

    Args:
        path (str):The source file path.
        dst_folder (str):The destination folder.
        dst_name (str, optional):The destination file name without postfix. Defaults to None.
        postfixes (list, optional):List of postfixes to consider. Defaults to None.
        copy (bool, optional):Whether to copy instead of move. Defaults to True.
        execute (bool, optional):Whether to execute the move/copy. Defaults to False.
        move_empty_file (bool, optional):Whether to move if the file is empty. Defaults to True.
        delete_empty_file (bool, optional):Whether to delete the file if it is empty. Defaults to False.
        ignore_failed (bool, optional):Whether to ignore the options that failed to move or copy. Defaults to False.
        overwrite (bool, optional):Whether to overwrite the file if it exists. Defaults to True.


    Returns:
        None
    """
    # NOTE:'self_postfix' will be the last part after splitting by '.'
    prefix, self_postfix = osp.splitext(path)  # xxx/01.png -> ['xxx/01', '.png']

    if postfixes is None:
        postfixes = [self_postfix]

    pairs_number = 0
    excute_postfixces = []
    for pf in postfixes:
        pairs_number += 1
        if isinstance(pf, list):
            excute_postfixces += pf
        else:
            excute_postfixces.append(pf)
    postfixes = list(set(excute_postfixces))

    src_dir = osp.dirname(prefix)  # 'xxx'
    src_name = osp.basename(prefix)  # '01'

    if dst_name is None:
        dst_name = src_name
    else:
        # simple check:
        for postfix in postfixes:
            postfix_length = len(postfix)
            if postfix == dst_name[-postfix_length:]:
                dst_name = dst_name[:-postfix_length]
                break

    execute_srcs = []
    for postfix in postfixes:
        src = osp.join(src_dir, src_name + postfix)

        if (delete_empty_file or not move_empty_file) and os.path.getsize(src) == 0:
            if delete_empty_file:
                os.remove(path)
            return

        if osp.exists(src):
            dst = osp.join(dst_folder, dst_name + postfix)
            execute_srcs.append([src, dst])

    if not ignore_failed and len(execute_srcs) < pairs_number:
        print(f"warning:[{path}]缺少配对文件[{execute_srcs}]")
        return

    if not execute:
        print("=" * 150)

    for src, dst in execute_srcs:
        if not execute:
            print(f"[move_file_pair]:{src} -> {dst}")
        else:
            if osp.exists(dst) and overwrite:
                os.remove(dst)

            if not osp.exists(dst):
                os.makedirs(osp.dirname(dst), exist_ok=True)
                try:
                    if copy:
                        shutil.copy(src, dst)
                    else:
                        shutil.move(src, dst)
                except Exception as e:
                    if not ignore_failed:
                        raise Exception(e)
                    print(e)
    return execute_srcs


def save_txt_jpg(path, image, content):
    """Save an image as a .png file and optionally save content as a .txt file.

    Args:
        path (str):The base file path.
        image (np.ndarray):The image to be saved.
        content (str, optional):The content to be written to a text file. Defaults to None.

    Returns:
        tuple:A tuple containing the paths to the saved image and text file.
    """
    # Determine the file extension
    file_extension = osp.splitext(path)[-1]

    # Create the .png file path
    png_path = path.replace(file_extension, ".png")

    os.makedirs(osp.dirname(png_path), exist_ok=True)
    # Save the image as a .png file
    cv2.imwrite(png_path, image)

    if content is None:
        return png_path, None

    # Create the .txt file path
    txt_path = path.replace(file_extension, ".txt")

    # Write the content to the .txt file
    with open(txt_path, "w") as file:
        file.writelines(content)

    return png_path, txt_path


# ===============图像处理===============


def random_color(min_value=0, max_value=255) -> tuple:
    """Generate a random color.

    Args:
        min_value (int):The minimum value for the color components.
        max_value (int):The maximum value for the color components.

    Returns:
        tuple:A tuple containing three integers representing the blue, green, and red components of the color.
    """
    blue = np.random.randint(min_value, max_value)
    green = np.random.randint(min_value, max_value)
    red = np.random.randint(min_value, max_value)
    return tuple([blue, green, red])


def create_color_list(num_colors):
    """Create a list of colors.

    REF:https://matplotlib.org/stable/users/explain/colors/colormaps.html#qualitative

    Args:
        num_colors (int):The number of colors to generate.

    Returns:
        np.ndarray:An array of RGB color values.
    """
    if num_colors < 10:
        colors = np.array(plt.cm.tab10.colors)
    else:
        colors = np.array(plt.cm.tab20.colors)

    colors = colors[: num_colors - 1, ::-1] * 255
    colors = np.insert(colors, 0, (0, 0, 0), axis=0)
    return [tuple([int(x) for x in xx]) for xx in colors]


def image_info(img, name=None):
    """Returns information about the image.

    Args:
        img:The image to analyze. Can be a PIL Image or a NumPy array.
        name:Optional; the name of the image. Defaults to 'img'.

    Returns:
        A formatted string containing the image's shape, value range, dtype, device, and unique values.
    """
    import torch

    info = ""
    name = name or "img"
    if isinstance(img, Image.Image):
        img = np.array(img)
        info = "PIL Image"

    device = img.device if torch.is_tensor(img) else "cpu"
    dtype = img.dtype
    img_shape = img.shape
    min_val, max_val = img.min(), img.max()
    img = img.cpu() if torch.is_tensor(img) else img

    unique_values = np.unique(img).tolist()
    unique_values_str = ", ".join([f"{x}" for x in unique_values[:5]])
    if len(unique_values) > 5:
        unique_values_str += ", ... " + f"{max_val}"
    return (
        f"\n{'-' * 100}\n" + info + "\n"
        f"[{name}] shape is {img_shape}, "
        f"values range are [{min_val}, {max_val}], "
        f"dtype is {dtype}, "
        f"on {device} device.\n"
        f"unique: [{unique_values_str}]"
        f"\n{'-' * 100}\n"
    )


def pad_image(
    img, target=None, border_type=None, value=(0, 0, 0), center=True, align=8
):
    """
    对输入图像进行pad,并同步返回mask,mask尺寸与pad后图像一致,pad区域为0,原图区域为255

    Args:
        img (np.ndarray): 输入图像
        target (tuple or int, optional): 目标尺寸.如果未指定,则短边pad到长边
        border_type (int, optional): 边界类型,默认cv2.BORDER_CONSTANT
        value (tuple, optional): pad区域颜色,默认(0,0,0)
        center (bool, optional): 是否居中pad,默认True
        align (int, optional): pad后尺寸对齐到多少的倍数,默认8

    Returns:
        tuple: (pad后的图像, (left, top), (right, bottom), mask)
            mask: np.uint8, pad区域为0,原图区域为255
    """
    border_type = border_type if border_type else cv2.BORDER_CONSTANT
    height, width = img.shape[:2]

    # 计算目标尺寸
    if target is None:
        target_height = target_width = max(height, width)
    else:
        if isinstance(target, int):
            target_height = target_width = target
        else:
            target_width, target_height = target

    if target_width < width:
        print(f"width pad value too small:{width} -> {target_width}")
    if target_height < height:
        print(f"height pad value too small:{height} -> {target_height}")

    # 对齐到align的倍数
    target_height, target_width = (
        divisibility(x, r=align) for x in [target_height, target_width]
    )

    # 计算pad的上下左右
    top, left = 0, 0
    if center:
        top = max((target_height - height) // 2, 0)
        left = max((target_width - width) // 2, 0)

    bottom = max(target_height - height - top, 0)
    right = max(target_width - width - left, 0)

    # pad图像
    if border_type == cv2.BORDER_CONSTANT:
        img_padded = cv2.copyMakeBorder(
            img, top, bottom, left, right, border_type, value=value
        )
    else:
        img_padded = cv2.copyMakeBorder(
            img, top, bottom, left, right, borderType=border_type
        )

    # 构建mask,pad区域为0,原图区域为255
    mask = np.zeros((target_height, target_width), dtype=np.uint8)
    mask[top : top + height, left : left + width] = 255
    mask = np.stack([mask] * 3, axis=-1)

    return img_padded, (left, top), (right, bottom), mask


def random_pad_image(
    image, target_size, border_type=cv2.BORDER_CONSTANT, border_value=(0, 0, 0)
):
    """Randomly pads an image to the target size.

    Args:
        image (numpy.ndarray):The input image to be padded.
        target_size (int or tuple):The target size for padding. If an integer is provided, both width and height will
        be set to this value. If a tuple is provided, it should be in the form (width, height).
        border_type (int, optional):Border type to be used for padding. Defaults to cv2.BORDER_CONSTANT.
        border_value (tuple, optional):Border color value for padding. Defaults to (0, 0, 0).

    Returns:
        tuple:The padded image and the x, y coordinates of the top-left corner of the original image within the padded image.
    """
    height, width = image.shape[:2]

    if isinstance(target_size, int):
        target_height = target_width = target_size
    else:
        target_width, target_height = target_size

    top, left = 0, 0
    bottom, right = max(target_height - height - top, 0), max(
        target_width - width - left, 0
    )

    if bottom - top > 1:
        top = np.random.randint(0, bottom)
        bottom -= top

    if right - left > 1:
        left = np.random.randint(0, right)
        right -= left

    padded_image = cv2.copyMakeBorder(
        image, top, bottom, left, right, borderType=border_type, value=border_value
    )

    return pad_image(
        padded_image,
        target_size,
        center=False,
        border_type=border_type,
        value=border_value,
    )


def crop_region(image, region):
    """Crops a region from an image.

    This function takes an image and a region specified by normalized coordinates,
    and returns the cropped region of the image along with the pixel coordinates of the region.

    Args:
        image (numpy.ndarray): The input image from which the region will be cropped.
        region (list of float): A list of four float values representing the normalized coordinates
                                of the region to crop in the format [left, right, top, bottom].

    Returns:
        tuple: A tuple containing:
            - numpy.ndarray: The cropped region of the image.
            - list of int: A list of four integer values representing the pixel coordinates
                           of the cropped region in the format [left, right, top, bottom].
    """
    height, width = image.shape[:2]
    left, right, top, bottom = region
    left, right = round(left * width), round(right * width)
    top, bottom = round(top * height), round(bottom * height)
    return image[top:bottom, left:right, ...], [left, right, top, bottom]


def center_crop(image, size=np.inf):
    """Crops the center of the image to create a square image.

    Args:
        image (numpy.ndarray):The input image to be cropped.
        size (int, optional):size of cropped. default inf

    Returns:
        tuple:The cropped image and the x, y coordinates of the top-left corner of the cropped area.
    """
    height, width = image.shape[:2]
    side_length = min(height, width, size)
    x_start = int(np.ceil((width - side_length) // 2))
    y_start = int(np.ceil((height - side_length) // 2))
    x_end, y_end = x_start + side_length, y_start + side_length
    cropped_image = image[y_start:y_end, x_start:x_end, ...]
    return cropped_image, (x_start, y_start), (x_end, y_end)


def random_crop(image, aspect_ratio=1, area_ratio=0.5, crop_area_range=(0, 1.0)):
    """Randomly crops a region from an image with a specified aspect ratio.

    Args:
        image (numpy.ndarray):The input image from which to crop.
        aspect_ratio (float):The desired aspect ratio (width/height) of the cropped region.
        area_ratio (float, optional):The ratio of the crop area to the image area. Defaults to 0.5.
        crop_area_range (tuple, optional):The range of the crop area as a fraction of the image size. Defaults to (0, 1.0).

    Returns:
        numpy.ndarray:The cropped image region.
    """
    img_height, img_width = image.shape[:2]

    area_ratio = np.sqrt(area_ratio)
    target_ratio = abs(crop_area_range[1] - crop_area_range[0])
    assert len(crop_area_range) == 2
    # Calculate the target crop height and width based on the aspect ratio
    if aspect_ratio < 1:
        # If the image's aspect ratio is greater than the target ratio,
        # set the crop height to a random value and calculate the crop width
        crop_height = int(area_ratio * img_height * target_ratio)
        crop_width = int(crop_height * aspect_ratio)
    else:
        # If the image's aspect ratio is less than or equal to the target ratio,
        # set the crop width to a random value and calculate the crop height
        crop_width = int(area_ratio * img_width * target_ratio)
        crop_height = int(crop_width / aspect_ratio)

    # Randomly select the top-left corner of the crop region
    x_start = np.random.randint(
        int(img_width * min(crop_area_range)),
        int(img_width * max(crop_area_range)) - crop_width + 1,
    )
    y_start = np.random.randint(
        int(img_height * min(crop_area_range)),
        int(img_height * max(crop_area_range)) - crop_height + 1,
    )

    # Crop the image
    x_end, y_end = x_start + crop_width, y_start + crop_height
    cropped_image = image[y_start:y_end, x_start:x_end]
    return cropped_image, (x_start, y_start), (x_end, y_end)


def to_pil(image):
    """
    Converts the input image to a Pillow Image object.

    The input can be a Pillow Image object or a numpy.ndarray (in BGR format, as read by OpenCV).
    Returns a Pillow Image object in RGB format.

    Args:
        image: The input image, which can be a PIL.Image.Image or a numpy.ndarray.

    Returns:
        PIL.Image.Image: The converted Pillow image.
    """

    if isinstance(image, Image.Image):
        return image
    elif isinstance(image, np.ndarray):
        # 判断是否为灰度图
        if image.ndim == 2:
            return Image.fromarray(image)
        # 判断是否为带alpha通道的图像
        if image.shape[2] == 4:
            # OpenCV读取的顺序是BGRA，需转换为RGBA
            image = image[..., [2, 1, 0, 3]]
            return Image.fromarray(image, mode="RGBA")
        elif image.shape[2] == 3:
            # OpenCV读取的顺序是BGR，需转换为RGB
            image = image[..., ::-1]
            return Image.fromarray(image, mode="RGB")
        else:
            raise ValueError("不支持的ndarray图像通道数: {}".format(image.shape))
    else:
        raise TypeError("输入类型必须为PIL.Image.Image或numpy.ndarray")


def to_cv2(image):
    """
    将输入图像转换为OpenCV格式的numpy.ndarray（BGR格式）。

    输入可以是PIL.Image.Image对象或numpy.ndarray（RGB或BGR格式）。
    返回值为BGR格式的numpy.ndarray。

    Args:
        image: 输入图像，可以是PIL.Image.Image或numpy.ndarray。

    Returns:
        numpy.ndarray: 转换后的BGR格式图像。

    Raises:
        TypeError: 输入类型不是PIL.Image.Image或numpy.ndarray时抛出。
        ValueError: 不支持的ndarray图像通道数时抛出。
    """

    if isinstance(image, np.ndarray):
        # 如果已经是BGR格式，直接返回
        if image.ndim == 2:
            return image
        elif image.shape[2] == 3:
            # 判断是否为RGB格式（常见于PIL转np），如果是则转换为BGR
            # 简单判断：如果均值R>均值B，可能是RGB
            if image[..., 0].mean() < image[..., 2].mean():
                # 可能已经是BGR
                return image
            else:
                # RGB转BGR
                return image[..., ::-1]
        elif image.shape[2] == 4:
            # RGBA或BGRA，需转换为BGRA
            # 判断是否为RGBA
            if image[..., 0].mean() > image[..., 2].mean():
                # RGBA转BGRA
                return image[..., [2, 1, 0, 3]]
            else:
                # 已经是BGRA
                return image
        else:
            raise ValueError("不支持的ndarray图像通道数: {}".format(image.shape))
    elif isinstance(image, Image.Image):
        # PIL转BGR
        if image.mode == "RGB":
            return np.array(image)[..., ::-1]
        elif image.mode == "RGBA":
            arr = np.array(image)
            return arr[..., [2, 1, 0, 3]]
        elif image.mode == "L":
            return np.array(image)
        else:
            # 其他模式先转为RGB
            image = image.convert("RGB")
            return np.array(image)[..., ::-1]
    else:
        raise TypeError("输入类型必须为PIL.Image.Image或numpy.ndarray")


def calculate_resize_size(orig_width, orig_height, max_length=4096, **kwargs):
    """
    计算图像resize的目标尺寸

    Args:
        orig_width (int): 原始图像宽度
        orig_height (int): 原始图像高度
        max_length (int, optional): 宽度或高度的最大允许长度,默认为4096
        **kwargs: 调整大小的附加关键字参数
            - align (int, optional): 可整除的对齐值,默认为1
            - hard (int or tuple, optional): 硬目标尺寸
            - short (int, optional): 较短维度的目标尺寸
            - long (int, optional): 较长维度的目标尺寸
            - target_height (int, optional): 调整大小的目标高度
            - target_width (int, optional): 调整大小的目标宽度

    Returns:
        tuple: (target_width, target_height) 或 (None, None) 如果无法计算
    """
    # 创建对齐函数
    align_function = partial(divisibility, r=kwargs.get("align", 1))

    # 根据不同的参数计算目标尺寸
    target_width, target_height = _calculate_target_size(
        orig_height, orig_width, align_function, kwargs
    )

    # 限制最大尺寸
    target_width, target_height = _limit_max_size(
        target_width, target_height, max_length
    )

    return target_width, target_height


def size_pre_process(image, max_length=8000, **kwargs):
    """
    根据各种条件预处理图像尺寸

    Args:
        image (numpy.ndarray): 要调整大小的输入图像
        max_length (int, optional): 宽度或高度的最大允许长度,默认为4096
        **kwargs: 调整大小的附加关键字参数
            - interpolation (int, optional): 调整大小的插值方法,默认为None
            - align (int, optional): 可整除的对齐值,默认为32
            - hard (int or tuple, optional): 硬目标尺寸
            - short (int, optional): 较短维度的目标尺寸
            - long (int, optional): 较长维度的目标尺寸
            - height (int, optional): 调整大小的目标高度
            - width (int, optional): 调整大小的目标宽度

    Returns:
        numpy.ndarray: 调整大小后的图像
    """
    height, width = image.shape[:2]

    # 计算目标尺寸
    target_width, target_height = calculate_resize_size(
        width, height, max_length, **kwargs
    )

    # 执行图像缩放
    return _resize_image_with_interpolation(
        image, target_width, target_height, **kwargs
    )


def warp_regions(image, box):
    """
    对图像中由四边形box定义的区域进行透视变换(仿射变换只能处理三点,四点需用透视变换).

    Args:
        image (numpy.ndarray): 输入图像.
        box (list or np.ndarray): 四个点的列表或数组,顺序为 [p0, p1, p2, p3],通常为左上、右上、右下、左下.

    Returns:
        numpy.ndarray: 变换后的图像区域.
    """
    box = np.array(box, dtype=np.float32)
    if box.shape != (4, 2):
        raise ValueError("box 应为4个二维点的列表或数组,形状为(4,2)")

    # 计算目标宽高
    width_top = np.linalg.norm(box[0] - box[1])
    width_bottom = np.linalg.norm(box[3] - box[2])
    width = int(max(width_top, width_bottom))

    height_left = np.linalg.norm(box[0] - box[3])
    height_right = np.linalg.norm(box[1] - box[2])
    height = int(max(height_left, height_right))

    dst_pts = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )

    perspective_matrix = cv2.getPerspectiveTransform(box, dst_pts)
    warped_image = cv2.warpPerspective(image, perspective_matrix, (width, height))
    return warped_image


def rotate_image(
    image,
    angle,
    center_point=None,
    scale=1.0,
    border_mode=cv2.BORDER_CONSTANT,
    border_value=(0, 0, 0),
):
    """Rotates an image counterclockwise by a specified angle without cropping.

    Args:
        image (numpy.ndarray):The input image to be rotated.
        angle (float):The angle by which to rotate the image counterclockwise.
        center_point (tuple, optional):The point around which to rotate the image. Defaults to the center of the image.
        scale (float, optional):The scaling factor. Defaults to 1.0.
        border_mode (int, optional):Pixel extrapolation method. Defaults to cv2.BORDER_CONSTANT.

    Returns:
        numpy.ndarray:The rotated image without cropping.
    """
    height, width = image.shape[:2]
    if center_point is None:
        center_point = (width // 2, height // 2)

    # 计算旋转后的图像尺寸,避免裁剪
    angle_rad = abs(angle) * np.pi / 180.0
    cos_angle = abs(np.cos(angle_rad))
    sin_angle = abs(np.sin(angle_rad))

    # 计算旋转后需要的画布大小
    new_width = int(width * cos_angle + height * sin_angle)
    new_height = int(width * sin_angle + height * cos_angle)

    # 调整旋转中心点位置
    center_x, center_y = center_point
    new_center_x = new_width // 2
    new_center_y = new_height // 2

    # 计算平移量,将原图居中放置在新画布上
    translation_x = new_center_x - center_x
    translation_y = new_center_y - center_y

    # 创建旋转矩阵
    rotation_matrix = cv2.getRotationMatrix2D((center_x, center_y), angle, scale)

    # 添加平移变换
    rotation_matrix[0, 2] += translation_x
    rotation_matrix[1, 2] += translation_y

    # 执行仿射变换,使用新的画布尺寸
    rotated_image = cv2.warpAffine(
        image,
        rotation_matrix,
        (new_width, new_height),
        borderMode=border_mode,
        borderValue=border_value,
    )
    return rotated_image


def rotate_image_crop(image, angle_deg):
    h, w = image.shape[:2]

    # 旋转中心
    center = (w / 2, h / 2)

    # 计算旋转矩阵
    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)

    # 旋转（保留原图大小）
    rotated = cv2.warpAffine(image, M, (w, h))

    # 最大内接矩形宽高
    angle_rad = math.radians(angle_deg % 180)
    if angle_rad > math.pi / 2:
        angle_rad = math.pi - angle_rad

    rect_w, rect_h = _largest_rotated_rect(w, h, angle_rad)

    # 中心裁剪结果
    rect_w, rect_h = int(rect_w), int(rect_h)
    x1 = int(center[0] - rect_w / 2)
    y1 = int(center[1] - rect_h / 2)
    cropped = rotated[y1 : y1 + rect_h, x1 : x1 + rect_w]

    return cropped


def rotate_location(angle, rect):
    """Rotates the coordinates of a rectangle by a given angle.

    Args:
        angle (float):The angle by which to rotate the rectangle, in degrees.
        rect (tuple):A tuple (x, y, width, height) representing the rectangle.

    Returns:
        list:A list of tuples representing the new coordinates of the rectangle's corners.
    """
    angle_radians = -angle * np.pi / 180.0
    cos_angle = np.cos(angle_radians)
    sin_angle = np.sin(angle_radians)

    x, y, width, height = rect
    x1 = x - 0.5 * width
    y1 = y - 0.5 * height

    x0 = x + 0.5 * width
    y0 = y1

    x2 = x1
    y2 = y + 0.5 * height

    x3 = x0
    y3 = y2

    x0_new = (x0 - x) * cos_angle - (y0 - y) * sin_angle + x
    y0_new = (x0 - x) * sin_angle + (y0 - y) * cos_angle + y

    x1_new = (x1 - x) * cos_angle - (y1 - y) * sin_angle + x
    y1_new = (x1 - x) * sin_angle + (y1 - y) * cos_angle + y

    x2_new = (x2 - x) * cos_angle - (y2 - y) * sin_angle + x
    y2_new = (x2 - x) * sin_angle + (y2 - y) * cos_angle + y

    x3_new = (x3 - x) * cos_angle - (y3 - y) * sin_angle + x
    y3_new = (x3 - x) * sin_angle + (y3 - y) * cos_angle + y

    return [(x0_new, y0_new), (x1_new, y1_new), (x2_new, y2_new), (x3_new, y3_new)]


def cv_img_to_base64(image, quality=100):
    """Converts an OpenCV image to a base64 encoded string.

    Args:
        image (numpy.ndarray):The input image to be converted.
        quality (int, optional):The quality of the JPEG encoding. Defaults to 100.

    Returns:
        str:The base64 encoded string of the image.
    """
    img_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encoded_img = cv2.imencode(".jpg", image, img_params)
    base64_str = base64.b64encode(encoded_img).decode()
    return base64_str


# =============图像debug=============


def memory_info():
    # 获取虚拟内存信息
    ram_usage = psutil.virtual_memory()
    total = ram_usage.total / GB_UNIT
    available = ram_usage.available / GB_UNIT
    usage = ram_usage.used / GB_UNIT
    percent = ram_usage.percent
    string = (
        f"total: {ram_usage.total / GB_UNIT:.2f} GB, "
        f"available: {ram_usage.available / GB_UNIT:.2f} GB, "
        f"used: {ram_usage.used / GB_UNIT:.2f} GB({ram_usage.percent}%)."
    )
    return total, available, usage, percent, string


def export_args(args):
    data = vars(args)
    keys = sorted(list(data))
    lines = []
    for key in keys:
        value = data[key]
        flag = "# " if not value else ""
        if isinstance(value, str):
            value = f"'{value}'"
        lines.append(f"{flag}{key}: {value}")
    for line in lines:
        print(line)


def update_args(
    old_: Union[argparse.Namespace, dict], new_: Union[argparse.Namespace, dict]
) -> argparse.Namespace:
    """
    Update the arguments from old_ with new_.

    Args:
        old_ : The original arguments.
        new_ : The new arguments to update with.

    Returns:
        argparse.Namespace:The updated arguments as a Namespace object.
    """
    if isinstance(old_, argparse.Namespace):
        old_ = vars(old_)
    if isinstance(new_, argparse.Namespace):
        new_ = vars(new_)

    if isinstance(old_, str) and old_.endswith(".yaml"):
        with open(old_, "r") as file:
            old_ = yaml.safe_load(file)
    if isinstance(new_, str) and new_.endswith(".yaml"):
        with open(new_, "r") as file:
            new_ = yaml.safe_load(file)
    assert isinstance(old_, dict) and isinstance(new_, dict), print(
        type(old_), type(new_)
    )
    old_.update(new_)
    return argparse.Namespace(**old_)


def safe_replace(
    src: str, _old: Union[str, List[str]], _new: Union[str, List[str]]
) -> Optional[str]:
    """
    Safely replace occurrences of _old with _new in src.

    Args:
        src (str):The source string.
        _old (list or str):The substring to be replaced.
        _new (list or str):The substring to replace with.

    Returns:
        str:The modified string, or None if no replacement was made.
    """
    if isinstance(_old, str):
        _old = [_old]
        _new = [_new]
    assert len(_old) == len(_new)
    dst = src
    for _o, _n in zip(_old, _new):
        dst = dst.replace(_o, _n)
    if dst == src:
        raise ValueError("No replacement made!")
    return dst


def has_chinese(text):
    """Checks if a string contains any Chinese characters.

    Args:
        text (str):The input string to be checked.

    Returns:
        bool:True if the string contains Chinese characters, False otherwise.
    """
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True
    return False


def put_text(
    image,
    text: str,
    position=None,
    bg_color=None,
    text_color=None,
    text_size=None,
    thickness=1,
    chinese_font_path="",
    force_opencv=False,
    valid_region=None,
):
    """
    在图像上绘制文本，简化版接口，调用 put_text_with_region 并返回绘制后的图像。

    Args:
        image (numpy.ndarray): 输入图像。
        text (str): 要绘制的文本。
        position (tuple, optional): 文本位置 (x, y)。默认值为 None。
        bg_color (tuple, optional): 背景颜色。默认值为 None（无背景）。
        text_color (tuple, optional): 文本颜色。默认值为 None（使用默认颜色）。
        text_size (float, optional): 文本大小。默认值为 None。
        thickness (int, optional): 文本厚度。默认值为 1。
        chinese_font_path (str, optional): 中文字体文件路径。默认值为 ""。
        force_opencv (bool, optional): 强制使用 OpenCV 绘制文本。默认值为 False。
        valid_region (tuple, optional): 有效绘制区域 (x1, y1, x2, y2)。默认值为 None。

    Returns:
        numpy.ndarray: 添加文本后的图像。
    """
    # 调用 put_text_with_region，并返回第一个结果（图像）
    return put_text_with_region(
        image=image,
        text=text,
        position=position,
        bg_color=bg_color,
        text_color=text_color,
        text_size=text_size,
        thickness=thickness,
        chinese_font_path=chinese_font_path,
        force_opencv=force_opencv,
        valid_region=valid_region,
    )[0]


def put_text_with_region(
    image,
    text,
    position=None,
    bg_color=None,
    text_color=None,
    text_size=None,
    thickness=1,
    chinese_font_path="",
    force_opencv=False,
    valid_region=None,
):
    text = str(text)
    is_gray = image.ndim == 2

    if position is None:
        position = (0, 0)
    if bg_color is None:
        bg_color = (0, 0, 0)
    if text_color is None:
        text_color = 255 if is_gray else (255, 255, 255)

    height, width = image.shape[:2]
    if text_size is None:  # base 30 for pillow equal 1 for opencv
        text_size = max(1, int(0.02 * np.sqrt(height**2 + width**2)))

    has_chinese_char = has_chinese(text)

    if valid_region is None:
        height, width = image.shape[:2]
        valid_region = [0, 0, width, height]

    # Convert image to contiguous array
    image = np.ascontiguousarray(image)
    if force_opencv or not has_chinese_char:
        img_with_text, text_region = put_text_using_opencv(
            image,
            position,
            text,
            text_size / 30,
            bg_color,
            text_color,
            thickness,
            valid_region,
        )
    else:
        text_region = []
        img_with_text = put_text_use_pillow(
            image,
            position,
            text,
            text_size,
            bg_color,
            text_color,
            chinese_font_path,
        )

    return img_with_text, text_region, text_size


def put_text_using_opencv(
    image,
    position,
    text,
    font_scale,
    bg_color,
    text_color,
    thickness,
    valid_region,
):
    image = np.ascontiguousarray(image)
    tlx, tly, brx, bry = valid_region
    width = brx - tlx
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Offset position
    x1, y1 = np.array(position, dtype=int)
    x2, y2 = x1, y1
    font_sizes = []
    texts = text.replace("\r", "\n").split("\n")
    cur_texts = []
    (char_width, char_height), baseline = cv2.getTextSize(
        "1234567890gj", font, font_scale, thickness
    )
    char_height = int(char_height + baseline)
    char_width = int(char_width / 12 + 2)

    for line in texts:
        cur_text = [line]
        while cur_text:
            line = cur_text.pop()
            if len(line) == 0:
                continue
            text_width, text_height = char_width * len(line), char_height
            if text_width > width and len(line) > 1:
                mid = max(int(width / char_width), 1)
                cur_text.append(line[mid:])
                cur_text.append(line[:mid])
            else:
                x2 = max(x2, x1 + text_width)
                y2 += text_height + 2
                font_sizes.append([text_width, text_height])
                cur_texts.append(line)

    x1, _ = get_offset_coordinates(x1, x2, tlx, brx)  # 起始位置
    y1, _ = get_offset_coordinates(y1, y2, tly, bry)  # 起始位置

    text_region = []
    for idx, (line, (tw, th)) in enumerate(zip(cur_texts, font_sizes)):
        left_x, right_x = x1, x1 + tw
        top_y, bottom_y = y1, y1 + th

        top_left = (left_x - 1, top_y)
        bottom_right = (right_x + 1, bottom_y)
        if idx == 0:
            text_region += list(top_left)
        if idx == len(cur_texts) - 1:
            text_region += list(bottom_right)

        if bg_color != -1:
            try:
                cv2.rectangle(
                    image,
                    top_left,
                    bottom_right,
                    bg_color,
                    -1,
                    cv2.LINE_AA,
                )
            except Exception as e:
                print(
                    f"[put_text_using_opencv]:{e}, coordinates:{(left_x - 1, top_y), (right_x + 1, bottom_y)}"
                )
        cv2.putText(
            image,
            line,
            (left_x, bottom_y - baseline),
            font,
            font_scale,
            text_color,
            thickness,
        )
        x1, y1 = left_x, bottom_y + 1
    return image, text_region


def put_text_use_pillow(
    image, position, text, text_size, bg_color, text_color, chinese_font_path
):
    """Adds text to an image using Pillow, with support for Chinese characters.

    Args:
        image (numpy.ndarray, BGR):The input image to which text will be added.
        position (tuple):The (x, y) coordinates for the text position.
        text (str):The text to be added to the image.
        text_size (int):The size of the text.
        bg_color (tuple or int):The background color for the text.
        text_color (tuple or int):The color of the text.
        chinese_font_path (str):The path to the Chinese font file.

    Returns:
        numpy.ndarray:The image with the added text.
    """
    if osp.exists(chinese_font_path):
        font = ImageFont.truetype(chinese_font_path, int(max(text_size, 10)))
    else:
        chinese_font_path = fm.findfont(fm.FontProperties(family="AR PL UKai CN"))
        if osp.exists(chinese_font_path):
            font = ImageFont.truetype(chinese_font_path, int(max(text_size, 10)))
        else:
            print("[put_text_use_pillow]:有中文, 但没有对应的字体.")
            font = None

    if font is None:
        return put_text_using_opencv(
            image, position, text, text_size, bg_color, text_color
        )

    height, width = image.shape[:2]

    # Offset position
    x1, y1 = np.array(position, dtype=int)
    x2, y2 = x1, y1
    font_sizes = []
    texts = text.replace("\r", "\n").split("\n")
    cur_texts = []

    for line in texts:
        cur_text = [line]
        while cur_text:
            line = cur_text.pop()
            if len(line) == 0:
                continue
            if pl_version < "9.5.0":  # 9.5.0 later
                left, top, right, bottom = font.getbbox(line)
                text_width, text_height = right - left, bottom - top
            else:
                text_width, text_height = font.getsize(line)
            text_width += 2
            if text_width > width and len(line) > 1:
                mid = max(int(width / (text_width / len(line))), 1)
                cur_text.append(line[mid:])
                cur_text.append(line[:mid])
            else:
                x2 = max(x2, x1 + text_width)
                y2 += text_height + 2
                font_sizes.append([text_width, text_height])
                cur_texts.append(line)

    x1, _ = get_offset_coordinates(x1, x2, 0, width)
    y1, _ = get_offset_coordinates(y1, y2, 0, height)

    img_pillow = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pillow)

    for line, (tw, th) in zip(cur_texts, font_sizes):
        left_top_x, left_top_y = x1, y1
        right_bottom_x, right_bottom_y = x1 + tw, y1 + th
        if bg_color != -1:
            # fixme:这里矩形框有偏移
            draw.rectangle(
                [left_top_x, left_top_y - 1, right_bottom_x, right_bottom_y + 1],
                fill=bg_color,
            )
        draw.text((left_top_x, left_top_y), line, font=font, fill=text_color)
        x1, y1 = left_top_x, right_bottom_y + 1

    image = np.asarray(img_pillow)

    return image


def norm_for_show(array):
    """Normalizes an array for display purposes.

    Args:
        array (numpy.ndarray):The input array to be normalized.

    Returns:
        numpy.ndarray:The normalized array, scaled to the range [0, 255] and converted to uint8.
    """
    normalized_array = (
        (array - np.min(array)) / (np.max(array) - np.min(array) + 1e-4) * 255
    ).astype(np.uint8)
    if normalized_array.ndim == 2:
        normalized_array = np.stack([normalized_array] * 3, axis=-1)
    return normalized_array


def merge_images(img1, img2, pt1, pt2, debug=False):
    """
    合并两张图像，使各自指定的点重合，同时支持可调权重与自适应模式选择。

    Args:
        img1 (np.ndarray): 第一张图像.
        img2 (np.ndarray): 第二张图像.
        pt1 (tuple/list/np.ndarray): 在 img1 中对齐的点坐标 (x, y).
        pt2 (tuple/list/np.ndarray): 在 img2 中对齐的点坐标 (x, y).
        alpha_img1 (float): img1 在融合中的权重.
        alpha_img2 (float): img2 在融合中的权重.
        debug (bool): 是否显示调试标记.

    Returns:
        tuple: (fused_image, debug_image)
    """
    alpha_img1, alpha_img2 = 1.0, 1.0
    # ===== 封装坐标转为 int =====
    x1, y1 = np.array(pt1, dtype=int).tolist()
    x2, y2 = np.array(pt2, dtype=int).tolist()
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    # ===== 初步计算需扩展的边界 =====
    top = max(0, -y1)
    left = max(0, -x1)
    bottom = max(0, y1 - h1)
    right = max(0, x1 - w1)

    # 新坐标
    x3, y3 = x1 + left, y1 + top
    h3, w3 = h1 + top + bottom, w1 + left + right

    # 再扩展保证 img2 能放下
    top += max(y2 - y3, 0)
    left += max(x2 - x3, 0)
    bottom += max((h2 - y2) - (h3 - y3), 0)
    right += max((w2 - x2) - (w3 - x3), 0)

    # 新画布上坐标
    x4, y4 = x1 + left, y1 + top  # pt1 坐标
    x5, y5 = x4 - x2, y4 - y2  # img2 左上角
    x6, y6 = x5 + w2, y5 + h2  # img2 右下角

    x7, y7 = x4 - x1, y4 - y1  # img1 左上角
    x8, y8 = x7 + w1, y7 + h1  # img1 右下角

    # 重叠区域
    union_x1 = max(x5, x7)
    union_y1 = max(y5, y7)
    union_x2 = min(x6, x8)
    union_y2 = min(y6, y8)
    union_h, union_w = union_y2 - union_y1, union_x2 - union_x1

    # ===== 检查 faster 模式可用性 =====
    # img2 必须完全位于 img1 范围
    faster = not (x5 < 0 or y5 < 0 or x6 > w1 or y6 > h1)

    # ===== 合成 =====
    if faster:
        res = img1.copy()
        if union_h > 0 and union_w > 0:
            im1x1 = union_x1 - x7
            im1y1 = union_y1 - y7
            im1x2 = union_x2 - x7
            im1y2 = union_y2 - y7

            im2x1 = union_x1 - x5
            im2y1 = union_y1 - y5
            im2x2 = union_x2 - x5
            im2y2 = union_y2 - y5

            res[im1y1:im1y2, im1x1:im1x2, :] = cv2.addWeighted(
                res[im1y1:im1y2, im1x1:im1x2, :],
                alpha_img1,
                img2[im2y1:im2y2, im2x1:im2x2, :],
                alpha_img2,
                0,
            )
        img_show = res.copy()
    else:
        padded_img1 = cv2.copyMakeBorder(
            img1, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(0, 0, 0)
        )
        padded_img1[y5:y6, x5:x6, :] = cv2.addWeighted(
            padded_img1[y5:y6, x5:x6, :], alpha_img1, img2, alpha_img2, 0
        )
        res = padded_img1[y7:y8, x7:x8, :]
        img_show = padded_img1.copy()

    # ===== Debug 可视化 =====
    if debug:
        # img2 边框
        cv2.rectangle(img_show, (x5, y5), (x6, y6), (0, 0, 222), 2)
        # img1 边框
        cv2.rectangle(img_show, (x7, y7), (x8, y8), (0, 222, 222), 2)
        # 重合点
        cv2.circle(img_show, (x4, y4), 8, (222, 0, 0), -1)
        # 重叠区域
        cv2.rectangle(
            img_show, (union_x1, union_y1), (union_x2, union_y2), (0, 222, 0), 1
        )

    return res, img_show


def create_image_grid(
    images, nrow=None, ncol=None, show_info=None, infos=None, resort=True
):
    """Creates a grid of images with optional padding and resizing.

    Args:
        images (list):List of images as NumPy arrays.
        nrow (int, optional):Number of rows in the grid. Defaults to None.
        ncol (int, optional):Number of columns in the grid. Defaults to None.

    Returns:
        np.ndarray:The final image grid.
    """
    assert len(images) > 0, "The images list should not be empty."
    images = [convert_rgb(x) for x in images]

    # Add text info
    if show_info:
        if infos is None:
            infos = list(range(len(images)))
        assert len(infos) == len(images)

        def put_info(x, info):
            font_size = int(sum(x.shape[:2]) / 2 * 0.1)
            return put_text(x, f"{info}", (0, 0), text_size=font_size)

        images = [put_info(x, info) for x, info in zip(images, infos)]

    # Add padding to each image
    images = [
        cv2.copyMakeBorder(
            x, 10, 10, 10, 10, borderType=cv2.BORDER_CONSTANT, value=(222, 222, 222)
        )
        for x in images
    ]

    # Calculate the number of rows and columns if not provided
    total = len(images)
    if nrow is None and ncol is None:
        nrow = int(np.ceil(np.sqrt(total)))
    if nrow is None:
        nrow = int(np.ceil(total / ncol))
    if ncol is None:
        ncol = int(np.ceil(total / nrow))

    if resort:  # 先对横/竖图做分类，再在每个类别内部按高宽比排序
        images.sort(key=lambda x: (x.shape[1] >= x.shape[0], x.shape[0] / x.shape[1]))

    # Group images into rows
    images = [images[i : i + ncol] for i in range(0, len(images), ncol)]

    # Resize images in each row to have the same height
    tmps = []
    for xx in images:
        tmp = []
        for x in xx:
            x = size_pre_process(x, height=xx[0].shape[0])
            tmp.append(x)
        tmps.append(tmp)
    images = tmps

    # Concatenate the first row of images horizontally
    img1 = np.concatenate(images.pop(0), axis=1)

    # Concatenate remaining rows vertically
    while images:
        h1, w1 = img1.shape[:2]
        img2 = images.pop(0)
        img2_number = len(img2)
        img2 = np.concatenate(img2, axis=1)
        h2, w2 = img2.shape[:2]

        # Resize img2 to match the width of img1
        if img2_number < ncol:
            img2 = size_pre_process(img2, height=int(h2 / (h1 + h2) * w1))
        else:
            img2 = size_pre_process(img2, width=w1)

        # Merge img1 and img2 vertically
        _, img1 = merge_images(img1, img2, (0, h1), (0, 0))
    return img1


def convert_rgb(image):
    if isinstance(image, Image.Image):
        image = np.array(image)[..., ::-1]
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)

    if image.dtype != np.uint8:
        image = norm_for_show(image)
    return image


def concatenate_images(images: list, axis=None):
    """
    Concatenates a list of images into a single image.

    Args:
        images (list):List of images to concatenate. Each image should be a NumPy array.

    Returns:
        np.ndarray:Concatenated image or None if the input list is empty.
    """
    assert isinstance(images, list), "Input must be a list of images."

    if len(images) == 0:
        return None
    if len(images) == 1:
        return images[0]
    images = [convert_rgb(x) for x in images]
    height, width = images[0].shape[:2]
    concatenated_images = []
    if not axis:
        axis = int(height > width)
    for image in images:
        if axis == 1:
            image = size_pre_process(image, height=height, align=1)
            axis = 1
        else:
            image = size_pre_process(image, width=width, align=1)
            axis = 0

        concatenated_images.append(image)
    try:
        concatenated_image = np.concatenate(concatenated_images, axis=axis)
    except:

        for c in concatenated_images:
            print(c.shape)

    return concatenated_image


def imshow(
    window_name,
    image: Union[List[np.ndarray], np.ndarray],
    wk=True,
    original_size=False,
    delay: int = 0,
    exit_key: str = "\x1b",
):
    """Displays an image in a window.

    Args:
        window_name (str):The name of the window.
        image (Union[List[np.ndarray], np.ndarray]):The image or list of images to be displayed.
        wk (bool, optional):Whether to call waitKey. Defaults to True.
        original_size (bool, optional):Whether to display the image in its original size. Defaults to False.
        delay (int, optional):The delay in milliseconds for the waitKey function. Defaults to 0.
        exit_key (str, optional):The key code to exit the display. Defaults to 'ESC'.

    Returns:
        int:The key code pressed during the display, or None if waitKey is not called.
    """
    if isinstance(image, list):
        image = create_image_grid(image)

    if image is not None:
        if not original_size:
            height, width = image.shape[:2]
            if width > height and width > 2048:
                image = size_pre_process(image, width=2048)
            if height > 1024:
                image = size_pre_process(image, height=1024)

        cv2.imshow(window_name, image)
    if wk:
        key = cv2.waitKey(delay)
        if key == ord(exit_key):
            exit()
        return key
    return None


def imwrite(file_path, image, overwrite=True):
    """Writes an image to a file.

    Args:
        file_path (str):The path to save the image.
        image (numpy.ndarray):The image to be saved.
        overwrite (bool, optional):Whether to overwrite the file if it exists. Defaults to True.
    """
    if not file_path:
        print("Write failed! file_path is ", file_path)
        return
    if not overwrite and osp.exists(file_path):
        print(f"{file_path} already exists!")
        return
    if osp.dirname(file_path):
        os.makedirs(osp.dirname(file_path), exist_ok=True)
    cv2.imwrite(file_path, image)
    return osp.abspath(file_path)


def plt2array():
    """Convert a Matplotlib plot to a NumPy array.

    Returns:
        np.ndarray:The RGBA image as a NumPy array.
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    # Convert the Matplotlib plot to a NumPy array
    canvas = FigureCanvasAgg(plt.gcf())
    canvas.draw()

    # Get the width and height of the canvas
    width, height = canvas.get_width_height()

    # Decode the string to get the ARGB image
    buffer = np.frombuffer(canvas.tostring_argb(), dtype=np.uint8)

    # Reshape the buffer to (width, height, 4) for ARGB
    buffer.shape = (height, width, 4)

    # Convert ARGB to RGBA
    buffer = np.roll(buffer, 3, axis=2)

    # Create an Image object from the buffer
    image = Image.frombytes("RGBA", (width, height), buffer.tobytes())

    # Convert the Image object to a NumPy array
    plt.clf()
    return np.asarray(image)


def get_timestamp():
    # 获取当前时间
    now = datetime.now()
    # 格式化时间戳
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp


def get_utc_timestamp():
    # 获取当前UTC时间
    utc_now = datetime.utcnow()
    return utc_now


# =============================Math Helper=============================


def get_offset_coordinates(start_point, end_point, min_value: float, max_value: float):
    """
    Adjust the start and end points of a line segment to ensure they fall within the specified range.
    If the length of the line segment is greater than the range, a warning is printed and the original points are returned.

    Args:
        start_point (float):The initial start point of the line segment.
        end_point (float):The initial end point of the line segment.
        min_value (float):The minimum allowable value.
        max_value (float):The maximum allowable value.

    Returns:
        tuple:The adjusted start and end points of the line segment.
    """
    if end_point - start_point > max_value - min_value:
        print(
            f"[get_offset_coordinates] warning:"
            f"end_point - start_point > max_value - min_value:"
            f"{end_point - start_point} > {max_value - min_value}"
        )
        return start_point, end_point

    end_offset = max([0, min_value - start_point])
    start_point = max(min_value, start_point)
    start_offset = max([0, end_point - max_value])
    end_point = min(max_value, end_point)
    start_point = max(start_point - start_offset, min_value)
    end_point = min(end_point + end_offset, max_value)

    return start_point, end_point


def xywh2xyxy(pts):
    """
    Convert bounding boxes from (center x, center y, width, height) format to (x1, y1, x2, y2) format.

    Args:
        pts (np.ndarray or list):Array of bounding boxes in (cx, cy, w, h) format.

    Returns:
        np.ndarray:Array of bounding boxes in (x1, y1, x2, y2) format.
    """
    pts = np.reshape(pts, [-1, 4])
    cx, cy, w, h = np.split(pts, 4, 1)
    x1 = cx - w / 2
    x2 = cx + w / 2
    y1 = cy - h / 2
    y2 = cy + h / 2
    res = np.concatenate([x1, y1, x2, y2], axis=1)
    res = np.clip(res, 0, np.inf)
    return res


def xyxy2xywh(pts):
    """
    Convert bounding boxes from (x1, y1, x2, y2) format to (center x, center y, width, height) format.

    Args:
        pts (np.ndarray or list):Array of bounding boxes in (x1, y1, x2, y2) format.

    Returns:
        np.ndarray:Array of bounding boxes in (cx, cy, w, h) format.
    """
    pts = np.reshape(pts, [-1, 4])
    x1, y1, x2, y2 = np.split(pts, 4, 1)
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    w = np.abs(x1 - x2)
    h = np.abs(y1 - y2)
    res = np.concatenate([cx, cy, w, h], axis=1)
    res = np.clip(res, 0, np.inf)
    return res


def get_min_rect(pts):
    """
    Get the minimum bounding rectangle for a set of points.

    Args:
        pts (np.ndarray or list):Array of points with shape (N, 2).

    Returns:
        np.ndarray:Array containing [x_min, y_min, x_max, y_max, cx, cy, w, h].
    """
    pts = np.reshape(pts, (-1, 2))
    x_min = min(pts[:, 0])
    x_max = max(pts[:, 0])
    y_min = min(pts[:, 1])
    y_max = max(pts[:, 1])
    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2
    w = x_max - x_min
    h = y_max - y_min
    return np.array([x_min, y_min, x_max, y_max, cx, cy, w, h])


def clockwise_points(pts):
    """
    按顺时针顺序对四个点进行排序.

    Args:
        pts (list or np.ndarray): 点的列表或数组,格式为 [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]

    Returns:
        list: 按顺时针顺序排列的点列表 [左上, 右上, 右下, 左下]

    说明:
        1. 先按x坐标升序排序,得到左侧和右侧的两个点
        2. 左侧两个点中,y较小的是左上,y较大的是左下
        3. 右侧两个点中,y较小的是右上,y较大的是右下
    """
    if isinstance(pts, np.ndarray):
        pts = pts.tolist()
    if len(pts) != 4:
        raise ValueError("clockwise_points 只支持4个点的输入")
    # 按x坐标排序
    pts_sorted = sorted(pts, key=lambda x: x[0])
    left = pts_sorted[:2]
    right = pts_sorted[2:]
    # 左侧点：y小为左上,y大为左下
    left = sorted(left, key=lambda x: x[1])
    left_top, left_bottom = left[0], left[1]
    # 右侧点：y小为右上,y大为右下
    right = sorted(right, key=lambda x: x[1])
    right_top, right_bottom = right[0], right[1]
    # 顺时针返回：左上、右上、右下、左下
    return [left_top, right_top, right_bottom, left_bottom]


def softmax_np(x, dim=0):
    # 减去最大值以提高数值稳定性
    x_max = np.max(x, axis=dim, keepdims=True)
    e_x = np.exp(x - x_max)
    return e_x / np.sum(e_x, axis=dim, keepdims=True)


def simplify_number(decimal_value):
    """
    将小数转换为最简分数形式.

    Args:
        decimal_value (float): 需要转换的小数.

    Returns:
        tuple: 包含分数字符串、分子、分母的元组.
    """
    from fractions import Fraction

    # 将小数转换为最简分数
    simple_fraction = Fraction(decimal_value).limit_denominator()

    # 构建分数字符串表示
    fraction_str = f"{simple_fraction.numerator}/{simple_fraction.denominator}"

    return fraction_str, simple_fraction.numerator, simple_fraction.denominator


def divisibility(a: float, r: int = 32) -> int:
    """
    计算a是否能被r整除,如果不能则返回大于a的最小r的倍数.

    Args:
        a (float): 要检查的数字
        r (int, optional): 用于整除的基数,默认为32

    Returns:
        int: 大于或等于a的最小r的倍数
    """
    if r == 1:
        return int(a)
    return int(math.ceil(a / r) * r)


def md5sum(file_path: str) -> str:
    """
    Calculate the MD5 checksum of a file.

    Args:
        file_path (str):The path to the file.

    Returns:
        str:The MD5 checksum of the file.
    """
    with open(file_path, "rb") as file:
        md5_hash = hashlib.md5()
        while True:
            data = file.read(4096)  # 每次读取4KB数据
            if not data:
                break
            md5_hash.update(data)
    return md5_hash.hexdigest()
