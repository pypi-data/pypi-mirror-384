import sys
import time
from collections.abc import Callable
from io import TextIOWrapper
from functools import wraps
from .data_structures import Stack
from typing import Any, Optional


class _CapturingStream:
    """内部类：自定义流对象，转发内容到原始stdout并捕获"""
    def __init__(self, original_stdout: Optional[TextIOWrapper], capture_chunks: Stack[str]):
        self.original_stdout = original_stdout  # 持有原始标准输出（用于转发）
        self.capture_chunks = capture_chunks    # 存储捕获的字符块

    def write(self, text: str) -> int:
        """核心逻辑：先转发到原始stdout（保持原有打印），再存入捕获列表"""
        try:
            # 让原有打印生效
            self.original_stdout.write(text)
            # 捕获信息
            self.capture_chunks.push(text) if text != '\n' else None
            # recyclable = self.capture_chunks.push(text)
        except Exception as e:
            print(f"Error writing to stdout: {e}", file=sys.stderr)

        return len(text)  # 符合sys.stdout.write的接口约定（返回写入字符数）

    def flush(self) -> None:
        """转发 flush 请求，确保及时输出（如print(..., flush=True)）"""
        self.original_stdout.flush()


def monitor_print(capture_length: Optional[int] = None) -> Callable:
    """
    单函数打印监测装饰器：
    - 仅捕获被装饰函数的打印输出，不影响其他函数。
    - 支持设置捕获内容的最大长度（满员后自动移除最早元素）。
    - 可获取捕获的内容，或重置捕获状态。

    :param capture_length: 捕获内容的最大元素个数（None表示无限制）
    :return: 装饰器函数
    >>> @monitor_print()
    >>> def func():
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with output_monitor:
                result = func(*args, **kwargs)

            return result
        return wrapper
    return decorator


def timer(func=None):
    """计时器（可以当装饰器和函数使用）"""
    if callable(func):  # 当函数使用
        global _used_time

        start = time.perf_counter()
        result = func()
        end = time.perf_counter()

        _used_time = end - start
        return result
    else:  # 当装饰器使用
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                global _used_time

                w_start = time.perf_counter()
                w_result = f(*args, **kwargs)
                w_end = time.perf_counter()

                _used_time = w_end - w_start
                return w_result
            return wrapper
        return decorator


class _OutputMonitor:
    def __init__(self, capture_length: Optional[int] = None):
        self.capture_length = capture_length
        self.captured_chunks: Stack[str] = Stack[str](max_len=capture_length)
        self._original_stdout = sys.stdout

    def __enter__(self):
        sys.stdout = _CapturingStream(self._original_stdout, self.captured_chunks)
        return self

    def __exit__(self, *args):
        sys.stdout = self._original_stdout

    @property
    def get_output(self) -> str:
        return self.captured_chunks.pop()

    def reset(self):
        self.captured_chunks.clear()


_used_time: Optional[float] = None

output_monitor = _OutputMonitor(20)

# 工具函数：该打印不被监视
def iprint(arg: Any = '') -> None:
    output_monitor.__exit__()
    print(arg)
    output_monitor.__enter__()

def get_used_time() -> Optional[float]:
    return _used_time

__all__ = [
    'iprint',
    'monitor_print',
    'timer',
    'get_used_time',
    'output_monitor',
]