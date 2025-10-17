import logging
import threading
from contextlib import contextmanager

css = """
#col-container {
    margin: 0 auto;
    max-width: 1024px;
    padding-top: 20px;
}
#logo-title {
    text-align: center;
}
#logo-title h2 {
    font-weight: bold;
    font-size: 32px;
    background: linear-gradient(90deg, #FFE178, #B6C791, #91C7FF);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-top: 0;
}
"""


class LogCapture:
    """通用日志捕获器，可直接与 logging.Logger 对接"""

    def __init__(self, max_logs=100):
        self.logs = []
        self.max_logs = max_logs
        self.lock = threading.Lock()

    def write(self, message):
        """捕获标准输出的消息"""
        if message.strip():
            self.add_log(message.strip())

    def flush(self):
        """兼容 file-like 对象接口"""
        pass

    def add_log(self, message):
        """添加一条日志"""
        if message.strip():
            with self.lock:
                self.logs.append(message.strip())
                if len(self.logs) > self.max_logs:
                    self.logs = self.logs[-self.max_logs :]

    def get_logs(self, limit=50):
        """获取最近日志"""
        with self.lock:
            return "\n".join(self.logs[-limit:])

    def clear_logs(self):
        """清空日志"""
        with self.lock:
            self.logs.clear()


class CustomLogHandler(logging.Handler):
    """自定义日志处理器，将日志注入 LogCapture"""

    def __init__(self, log_capture):
        super().__init__()
        self.log_capture = log_capture

    def emit(self, record):
        message = self.format(record)
        self.log_capture.add_log(message)

    def format(self, record):
        return f"{record.levelname}: {record.getMessage()}"


class SDKLogInterceptor:
    """
    SDK 日志拦截器：
    用上下文管理器的方式替换 SDK logger 的 handler

    Usage:
        from wxw.gradio_helper import LogCapture, SDKLogInterceptor
        from mlsdk.utils.logger import get_logger as sdk_get_logger
        log_capture = LogCapture()
        log_interceptor = SDKLogInterceptor(
            log_capture, lambda: sdk_get_logger().get_logger()
        )
    """

    def __init__(self, log_capture, sdk_logger_getter):
        """
        :param log_capture: LogCapture 实例
        :param sdk_logger_getter: 一个函数，返回 SDK 内部的 logging.Logger 对象
        """
        self.log_capture = log_capture
        self.sdk_logger_getter = sdk_logger_getter

    @contextmanager
    def capture(self):
        logger_obj = self.sdk_logger_getter()

        old_handlers = logger_obj.handlers[:]
        old_level = logger_obj.level

        custom_handler = CustomLogHandler(self.log_capture)
        custom_handler.setLevel(old_level)

        logger_obj.addHandler(custom_handler)
        try:
            yield
        finally:
            logger_obj.removeHandler(custom_handler)
            logger_obj.handlers = old_handlers
