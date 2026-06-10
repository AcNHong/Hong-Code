import math
import os


def get_file_modification_time(file_path:str) -> int:
    """
     获取文件的标准化修改时间（毫秒单位）。
     使用 math.floor 确保跨文件操作的时间戳比较一致性，
     减少来自子毫秒精度变化（例如 IDE 文件监视器在不改变内容的情况下触摸文件）的误报。

     Args:
         file_path: 文件路径

     Returns:
         标准化后的修改时间戳（毫秒），如果文件不存在返回 0
     """
    try:
        # 获取文件状态
        stat_result = os.stat(file_path)

        # st_mtime 是浮点数，单位是秒
        # 转换为毫秒并向下取整
        mtime_ms = stat_result.st_mtime * 1000
        return math.floor(mtime_ms)
    except FileNotFoundError:
        return 0
    except OSError as e:
        # 处理其他操作系统错误
        print(f"Error accessing file {file_path}: {e}")
        return 0

