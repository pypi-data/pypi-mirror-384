import sys
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
        # 让原有打印生效
        self.original_stdout.write(text)
        # 添加捕获信息
        self.capture_chunks.push(text) if text != '\n' else None
            # recyclable = self.capture_chunks.push(text)

        return len(text)  # 符合sys.stdout.write的接口约定（返回写入字符数）

    def flush(self) -> None:
        """转发flush请求，确保及时输出（如print(..., flush=True)）"""
        self.original_stdout.flush()


def monitor_print(capture_length: Optional[int] = None) -> Callable:
    """
    单函数打印监测装饰器：
    - 仅捕获被装饰函数的打印输出，不影响其他函数。
    - 支持设置捕获内容的最大长度（满员后自动移除最早元素）。
    - 可获取捕获的内容，或重置捕获状态。

    :param capture_length: 捕获内容的最大元素个数（None表示无限制）
    :return: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        # 用wraps保留被装饰函数的元数据（如函数名、文档）
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            global _captured_chunks

            restart_monitoring()

            # ------------------- 执行函数并捕获打印 -------------------
            try:
                # 替换当前线程的stdout为自定义流
                sys.stdout = _CapturingStream(_original_stdout, _captured_chunks)
                # 执行被装饰的函数
                result = func(*args, **kwargs)
            finally:
                # 无论函数是否异常，都恢复原始stdout（关键：避免影响其他函数）
                sys.stdout = _original_stdout

            # ------------------- 存储捕获内容 -------------------
            wrapper._captured_output = _captured_chunks.peek()  # 拼接为字符串存储
            return result

        def reset_capture() -> None:
            """重置捕获内容（清空已存储的打印）"""
            wrapper._captured_output = ""

        # 将工具方法绑定到包装函数（方便调用）
        wrapper.get_captured_output = get_captured_output
        wrapper.reset_capture = reset_capture

        return wrapper

    return decorator


# 保存系统默认的标准输出（用于恢复和转发）
_original_stdout = sys.__stdout__

# 存储捕获的输出内容（字符块列表，避免字符串拼接性能问题）
_captured_chunks: Stack[str] = Stack(max_len=20)

# 替换全局标准输出为自定义捕获流（关键：转发到原始stdout）
sys.stdout = _CapturingStream(_original_stdout, _captured_chunks)

def restart_monitoring() -> None:
    """重新开始监测打印输出（重置捕获内容 + 重新绑定stdout）"""
    global _captured_chunks
    # 重新创建捕获流（依然转发到原始stdout）
    sys.stdout = _CapturingStream(_original_stdout, _captured_chunks)

# 工具函数：获取捕获的完整输出（拼接成字符串）
def get_captured_output() -> str:
    """
    返回当前捕获的所有打印内容的拼接字符串
    :return:
    """
    return _captured_chunks.pop()

# 工具函数：恢复原始标准输出（停止捕获）
def restore_stdout() -> None:
    """恢复系统默认的标准输出（后续打印不再被捕获）"""
    sys.stdout = _original_stdout

# 工具函数：该打印不被监视
def iprint(arg: Any = '') -> None:
    restore_stdout()
    print(arg)
    restart_monitoring()

__all__ = [
    'iprint',
    'restore_stdout',
    'restart_monitoring',
    'get_captured_output',
    'monitor_print'
]