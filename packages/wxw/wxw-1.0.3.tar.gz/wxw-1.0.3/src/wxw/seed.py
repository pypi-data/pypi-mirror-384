import os
import torch
import random
import hashlib
import numpy as np
from functools import wraps
from datetime import datetime
from contextlib import contextmanager


def set_random_seed(seed=None, deterministic=True, benchmark=False):
    """
    设置随机种子，支持更多配置选项

    参数:
        seed (int, optional): 随机种子值。如果为None，则自动生成
        deterministic (bool): 是否启用确定性模式（可能影响性能）
        benchmark (bool): 是否启用cudnn benchmark（提升性能但可能影响确定性）

    返回:
        int: 使用的种子值
    """
    # 如果没有提供种子，自动生成一个
    if seed is None:
        seed = generate_random_seed()

    # 设置基础随机种子
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    # CUDA相关设置
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

        # 确定性设置
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        else:
            torch.backends.cudnn.benchmark = benchmark

    # 环境变量
    os.environ["PYTHONHASHSEED"] = str(seed)

    # 设置PyTorch的确定性模式（PyTorch 1.7+）
    if hasattr(torch, "use_deterministic_algorithms"):
        torch.use_deterministic_algorithms(deterministic)

    print(f"Random seed set to {seed}")
    print(f"Deterministic mode: {deterministic}")
    print(f"CUDNN benchmark: {benchmark}")

    return seed


def generate_random_seed():
    """
    生成一个基于时间的随机种子

    返回:
        int: 生成的种子值
    """
    # 使用当前时间生成种子
    current_time = datetime.now().isoformat().encode()
    hash_object = hashlib.md5(current_time)
    seed = int(hash_object.hexdigest()[:8], 16)
    return seed % (2**31)  # 确保种子在合理范围内


def with_random_seed(seed=42):
    """
    装饰器：为函数自动设置随机种子

    参数:
        seed (int): 随机种子值
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 保存当前状态
            python_state = random.getstate()
            numpy_state = np.random.get_state()
            torch_state = torch.get_rng_state()

            if torch.cuda.is_available():
                cuda_state = torch.cuda.get_rng_state()

            try:
                # 设置种子
                set_random_seed(seed)
                # 执行函数
                result = func(*args, **kwargs)
                return result
            finally:
                # 恢复状态
                random.setstate(python_state)
                np.random.set_state(numpy_state)
                torch.set_rng_state(torch_state)

                if torch.cuda.is_available():
                    torch.cuda.set_rng_state(cuda_state)

        return wrapper

    return decorator


@contextmanager
def ctx_random_seed(seed=42):
    """
    上下文管理器：临时设置随机种子

    参数:
        seed (int): 随机种子值
    """
    # 保存当前状态
    python_state = random.getstate()
    numpy_state = np.random.get_state()
    torch_state = torch.get_rng_state()

    if torch.cuda.is_available():
        cuda_state = torch.cuda.get_rng_state()

    try:
        # 设置种子
        set_random_seed(seed)
        yield seed
    finally:
        # 恢复状态
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.set_rng_state(torch_state)

        if torch.cuda.is_available():
            torch.cuda.set_rng_state(cuda_state)
