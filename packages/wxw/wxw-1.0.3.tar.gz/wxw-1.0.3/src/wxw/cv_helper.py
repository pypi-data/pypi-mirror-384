import cv2
import numpy as np
from .common import get_utc_timestamp

# ==============图像获取================


def select_region(image=None):
    """Allows the user to select a rectangular region in an image.

    This function displays an image and allows the user to draw a rectangle by clicking and dragging the mouse.
    The selected region's coordinates are returned as normalized values.

    Args:
        image (numpy.ndarray, optional): The input image in which the region is to be selected.
                                         If None, a screenshot of the screen is captured.

    Returns:
        tuple: A tuple containing four float values representing the normalized coordinates
               of the selected region in the format (x1, y1, x2, y2).
               Returns None if the selection is not completed.
    """
    if image is None:
        image = capture_screen_as_numpy()
    height, width = image.shape[:2]
    region = []

    def select_rectangle(event, x, y, flags, param):
        nonlocal region
        image_copy = image.copy()
        if event == cv2.EVENT_LBUTTONDOWN:
            region = [(x, y)]
        elif event == cv2.EVENT_MOUSEMOVE:
            if len(region) == 1:
                cv2.rectangle(image_copy, region[0], (x, y), (0, 255, 0), 2)
                cv2.imshow("Image", image_copy)
        elif event == cv2.EVENT_LBUTTONUP:
            region.append((x, y))
            cv2.rectangle(image_copy, region[0], region[1], (0, 255, 0), 2)
            cv2.imshow("Image", image_copy)

    while True:
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", select_rectangle)
        key = imshow("Image", image)
        if key == ord("q") and len(region) == 2:
            x1, y1 = region[0]
            x2, y2 = region[1]
            cv2.destroyAllWindows()
            return x1 / width, y1 / height, x2 / width, y2 / height
        return None


def capture_screen_as_numpy():
    """Captures the entire screen and returns it as a numpy array.

    This function takes a screenshot of the entire screen, converts it to a numpy array,
    and changes the color format from RGB to BGR.

    Returns:
        numpy.ndarray: The captured screen image in BGR format.
    """
    import pyautogui

    # 获取屏幕截图
    screenshot = pyautogui.screenshot()
    # 将截图转换为numpy数组
    frame = np.array(screenshot)
    # 将RGB格式转换为BGR格式(OpenCV使用BGR格式)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame


def capture_screen_from_region(region=None):
    """Captures a specified region of the screen and yields it as a numpy array.

    This function captures a specified region of the screen in a loop, converts it to a numpy array,
    and changes the color format from RGB to BGR. If no region is specified, it prompts the user to select one.

    Args:
        region (list of float, optional): A list of four float values representing the normalized coordinates
                                          of the region to capture in the format [left, top, right, bottom].
                                          If None, the user is prompted to select a region.

    Yields:
        tuple: A tuple containing:
            - int: The current iteration count.
            - numpy.ndarray: The captured region image in BGR format.
            - float: The current UTC timestamp.
    """
    import pyautogui

    if region is None:
        region = select_region()
    for ci in count():
        screen_width, screen_height = pyautogui.size()
        left = int(region[0] * screen_width)
        top = int(region[1] * screen_height)
        width = int((region[2] - region[0]) * screen_width)
        height = int((region[3] - region[1]) * screen_height)
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        yield (ci, frame, get_utc_timestamp())


# ===========屏幕截图方式================


# ===============camera ============
class ImageCapture:
    """
    图片序列读取器：用于按指定文件模式批量读取图片文件。

    该类支持根据通配符模式（如'./images/*.jpg'）递归查找并顺序读取图片，常用于批量推理、数据集遍历等场景。

    属性说明:
        all_path (List[str]): 匹配到的所有图片文件路径，已排序。
        idx (int): 当前读取到的图片索引。
        path (str|None): 当前读取的图片路径。

    方法说明:
        __len__(): 返回图片总数。
        read(): 读取下一个图片，返回(是否成功, 图片数据)。
        isOpened(): 判断是否还有未读取的图片。
    """

    def __init__(self, pattern, recursive=True):
        """
        初始化图片读取器。

        参数:
            pattern (str): 文件通配符模式，如'./images/*.jpg'。
            recursive (bool): 是否递归查找子目录，默认True。
        """
        self.all_path = glob.glob(pattern, recursive=recursive)
        self.all_path.sort()
        self.idx = 0
        self.path = None
        print(f"Collected {len(self)} frames!")

    def __len__(self):
        """
        获取图片总数。

        返回:
            int: 匹配到的图片文件数量。
        """
        return len(self.all_path)

    def read(self):
        """
        顺序读取下一个图片。

        返回:
            Tuple[bool, np.ndarray|None]: (读取是否成功, 图片数据或None)
        """
        if self.idx >= len(self):
            self.path = None
            return False, None
        self.path = self.all_path[self.idx]
        frame = cv2.imread(self.path)
        self.idx += 1
        return True, frame

    def isOpened(self):
        """
        判断是否还有未读取的图片。

        返回:
            bool: True表示还有图片可读，False表示已读完。
        """
        return self.idx < len(self)
