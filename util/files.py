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

# 编码检测
def detect_file_encoding(resolved_path:str) -> str:
    with open(resolved_path, 'rb') as f:
        head = f.read(4096)

    if len(head) == 0:
        return 'utf-8'

    if head[:2] == b'\xff\xfe':
        return 'utf-16-le'
    if head[:3] == b'\xef\xbb\xbf':
        return 'utf-8'

    return 'utf-8'

def detect_line_endings_for_string(content:str) -> str:
    crlf_count = 0
    lf = 0
    for i,c in enumerate(content):
        if c == "\n":
            if i > 0 and content[i-1] == "\r":
                crlf_count+=1
            else:
                lf+=1
    # 默认LF
    line_encoding = "CRLF" if crlf_count > lf else "LF"

    return line_encoding

# 写入文件
def write_text_content(file_path:str,content:str,encoding:str,ending:str):
    if ending == "CRLF":
        # 为了防止大模型给的文本包含\r\n的文本
        "\r\n".join(content.replace("\r\n","\n").split("\n"))

    with open(file_path,mode="w+",encoding=encoding) as f:
        f.write(content)

# 读取文件
def read_text(file_path:str,encoding = "utf-8"):
    # open默认会将换行符处理为\n 这里先不处理
    with open(file_path,mode="r",encoding=encoding,newline="") as f:
        content = f.read()
    return content

def read_meta_data_with_sync(file_path:str) -> dict:
    encoding = detect_file_encoding(file_path)
    raw = read_text(file_path,encoding = encoding)
    line_encoding = detect_line_endings_for_string(raw[0:4096])
    return {
        "content":raw.replace("\r\n","\n"), # 统一归一为unix默认换行符
        "encoding":encoding,
        "line_encoding":line_encoding
    }

if __name__ == "__main__":
    pass
