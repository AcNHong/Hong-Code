import subprocess
import os
import json
import shutil
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
from datetime import datetime


class FileManager:
    """Windows文件系统操作管理器"""

    def __init__(self, encoding=None):
        # 自动检测Windows系统编码
        if encoding is None:
            # Windows默认使用GBK编码
            self.encoding = 'gbk' if os.name == 'nt' else 'utf-8'
        else:
            self.encoding = encoding

        # 备用编码列表
        self.fallback_encodings = ['gbk', 'gb2312', 'gb18030', 'utf-8', 'latin-1']

    def _decode_output(self, data: bytes) -> str:
        """尝试多种编码解码输出"""
        if not data:
            return ''

        # 先尝试默认编码
        try:
            return data.decode(self.encoding)
        except (UnicodeDecodeError, LookupError):
            pass

        # 尝试备用编码
        for enc in self.fallback_encodings:
            try:
                return data.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue

        # 最后使用忽略错误的模式
        return data.decode(self.encoding, errors='ignore')


    def run_cmd(self, cmd: str, capture_output: bool = True) -> tuple:
        """
        执行命令的内部方法（修复编码问题）

        Args:
            cmd: 要执行的命令
            capture_output: 是否捕获输出

        Returns:
            (success, output) 元组
        """
        try:
            # 方式1：使用Popen手动处理编码
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=False,  # 获取bytes而非str
            )

            try:
                stdout, stderr = process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return False, "命令执行超时"

            if process.returncode == 0:
                # 解码输出
                output = self._decode_output(stdout)
                return True, output.strip() if output else ''
            else:
                # 错误输出
                error_msg = self._decode_output(stderr)
                if not error_msg and stdout:
                    error_msg = self._decode_output(stdout)
                return False, error_msg or f"命令执行失败，返回码: {process.returncode}"

        except FileNotFoundError:
            return False, "命令未找到"
        except Exception as e:
            return False, f"执行错误: {str(e)}"

    # ==================== 目录操作 ====================

    def create_directory(self, path: str) -> bool:
        """创建目录（支持多级目录）"""
        if os.path.exists(path):
            return True

        cmd = f'mkdir "{path}"'
        success, msg = self.run_cmd(cmd)
        return success

    def create_directories(self, paths: List[str]) -> Dict[str, bool]:
        """批量创建目录"""
        results = {}
        for path in paths:
            results[path] = self.create_directory(path)
        return results

    def create_directory_structure(self, base_path: str, structure: dict) -> bool:
        """
        创建目录结构

        Example:
            structure = {
                'project': {
                    'src': ['main.py', 'utils.py'],
                    'tests': [],
                    'docs': ['readme.md']
                }
            }
        """
        try:
            def _create_structure(current_path, struct):
                for name, content in struct.items():
                    path = os.path.join(current_path, name)
                    if isinstance(content, dict):
                        self.create_directory(path)
                        _create_structure(path, content)
                    elif isinstance(content, list):
                        self.create_directory(path)
                        for file in content:
                            self.create_file(os.path.join(path, file))
                    else:
                        self.create_directory(path)

            self.create_directory(base_path)
            _create_structure(base_path, structure)
            return True
        except Exception as e:
            print(f"创建目录结构失败: {e}")
            return False

    def list_directory(self, path: str = '.', pattern: str = '*') -> List[str]:
        """列出目录内容"""
        cmd = f'dir "{path}\\{pattern}" /B'
        success, output = self.run_cmd(cmd)
        if success and output:
            return output.split('\n')
        return []

    def list_directory_detailed(self, path: str = '.') -> List[Dict]:
        """列出目录详细信息"""
        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                items.append({
                    'name': item,
                    'path': item_path,
                    'type': 'directory' if os.path.isdir(item_path) else 'file',
                    'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    'modified': datetime.fromtimestamp(
                        os.path.getmtime(item_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception as e:
            print(f"列出目录失败: {e}")
        return items

    def delete_directory(self, path: str, force: bool = False) -> bool:
        """删除目录"""
        if not os.path.exists(path):
            return True

        if force:
            cmd = f'rmdir /S /Q "{path}"'
        else:
            cmd = f'rmdir "{path}"'

        success, msg = self.run_cmd(cmd)
        return success

    def copy_directory(self, source: str, destination: str) -> bool:
        """复制目录"""
        cmd = f'xcopy "{source}" "{destination}" /E /I /H /Y'
        success, msg = self.run_cmd(cmd)
        return success

    def move_directory(self, source: str, destination: str) -> bool:
        """移动目录"""
        cmd = f'move "{source}" "{destination}"'
        success, msg = self.run_cmd(cmd)
        return success

    # ==================== 文件创建 ====================

    def create_file(self, path: str, content: str = '') -> bool:
        """创建文件"""
        try:
            # 确保目录存在
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                self.create_directory(dir_path)

            # 使用echo命令创建文件
            if content:
                # 将内容中的特殊字符转义
                safe_content = content.replace('&', '^&').replace('|', '^|')
                cmd = f'echo {safe_content} > "{path}"'
            else:
                cmd = f'type nul > "{path}"'

            success, msg = self.run_cmd(cmd)
            return success
        except Exception as e:
            print(f"创建文件失败: {e}")
            return False

    def create_files_batch(self, file_dict: Dict[str, str]) -> Dict[str, bool]:
        """批量创建文件"""
        results = {}
        for path, content in file_dict.items():
            results[path] = self.create_file(path, content)
        return results

    def create_empty_files(self, paths: List[str]) -> Dict[str, bool]:
        """批量创建空文件"""
        return self.create_files_batch({path: '' for path in paths})

    # ==================== 文件读取 ====================

    def read_file(self, path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            cmd = f'type "{path}"'
            success, output = self.run_cmd(cmd)
            return output if success else None
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None

    def read_file_lines(self, path: str) -> List[str]:
        """读取文件为行列表"""
        content = self.read_file(path)
        return content.split('\n') if content else []

    def read_file_head(self, path: str, lines: int = 10) -> str:
        """读取文件前N行"""
        try:
            cmd = f'powershell -Command "Get-Content \'{path}\' -Head {lines}"'
            success, output = self.run_cmd(cmd)
            return output if success else ''
        except Exception as e:
            print(f"读取文件头部失败: {e}")
            return ''

    def read_file_tail(self, path: str, lines: int = 10) -> str:
        """读取文件后N行"""
        try:
            cmd = f'powershell -Command "Get-Content \'{path}\' -Tail {lines}"'
            success, output = self.run_cmd(cmd)
            return output if success else ''
        except Exception as e:
            print(f"读取文件尾部失败: {e}")
            return ''

    def read_csv(self, path: str) -> List[Dict]:
        """读取CSV文件"""
        import csv
        try:
            with open(path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"读取CSV失败: {e}")
            return []

    def read_json(self, path: str) -> Optional[Any]:
        """读取JSON文件"""
        content = self.read_file(path)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
        return None

    def search_files(self, pattern: str, path: str = '.') -> List[str]:
        """搜索文件"""
        cmd = f'dir "{path}\\{pattern}" /S /B'
        success, output = self.run_cmd(cmd)
        return output.split('\n') if success and output else []

    def grep_files(self, path: str, search_text: str, file_pattern: str = '*.*') -> List[str]:
        """在文件中搜索文本"""
        cmd = f'findstr /S /I /N "{search_text}" "{path}\\{file_pattern}"'
        success, output = self.run_cmd(cmd)
        return output.split('\n') if success and output else []

    # ==================== 文件写入 ====================

    def write_file(self, path: str, content: str, mode: str = 'w') -> bool:
        """写入文件"""
        try:
            # 确保目录存在
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                self.create_directory(dir_path)

            if mode == 'a':
                # 追加模式
                cmd = f'echo {content} >> "{path}"'
            else:
                # 覆盖模式
                cmd = f'echo {content} > "{path}"'

            success, msg = self.run_cmd(cmd)
            return success
        except Exception as e:
            print(f"写入文件失败: {e}")
            return False

    def append_to_file(self, path: str, content: str) -> bool:
        """追加内容到文件"""
        return self.write_file(path, content, mode='a')

    def write_json(self, path: str, data: Any, indent: int = 2) -> bool:
        """写入JSON文件"""
        try:
            json_str = json.dumps(data, indent=indent, ensure_ascii=False)
            return self.write_file(path, json_str)
        except Exception as e:
            print(f"写入JSON失败: {e}")
            return False

    def write_csv(self, path: str, data: List[Dict], headers: Optional[List[str]] = None) -> bool:
        """写入CSV文件"""
        import csv
        try:
            if not data:
                return False

            if headers is None:
                headers = list(data[0].keys())

            with open(path, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"写入CSV失败: {e}")
            return False

    # ==================== 文件操作 ====================

    def copy_file(self, source: str, destination: str) -> bool:
        """复制文件"""
        cmd = f'copy /Y "{source}" "{destination}"'
        success, msg = self.run_cmd(cmd)
        return success

    def move_file(self, source: str, destination: str) -> bool:
        """移动文件"""
        cmd = f'move /Y "{source}" "{destination}"'
        success, msg = self.run_cmd(cmd)
        return success

    def delete_file(self, path: str) -> bool:
        """删除文件"""
        if not os.path.exists(path):
            return True

        cmd = f'del /F /Q "{path}"'
        success, msg = self.run_cmd(cmd)
        return success

    def rename_file(self, old_path: str, new_path: str) -> bool:
        """重命名文件"""
        cmd = f'ren "{old_path}" "{os.path.basename(new_path)}"'
        success, msg = self.run_cmd(cmd)
        return success

    def get_file_info(self, path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            if not os.path.exists(path):
                return {}

            stat = os.stat(path)
            return {
                'name': os.path.basename(path),
                'path': os.path.abspath(path),
                'size': stat.st_size,
                'size_human': self._format_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'is_directory': os.path.isdir(path),
                'extension': os.path.splitext(path)[1]
            }
        except Exception as e:
            print(f"获取文件信息失败: {e}")
            return {}

    def get_file_size(self, path: str) -> int:
        """获取文件大小"""
        try:
            return os.path.getsize(path) if os.path.exists(path) else -1
        except Exception:
            return -1

    def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(path)

    # ==================== 工具方法 ====================

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def get_directory_tree(self, path: str = '.', max_depth: int = 3) -> str:
        """获取目录树"""
        try:
            cmd = f'tree "{path}" /A /F'
            success, output = self.run_cmd(cmd)
            return output if success else ''
        except Exception as e:
            print(f"获取目录树失败: {e}")
            return ''

    def sync_directories(self, source: str, destination: str) -> bool:
        """同步目录（使用robocopy）"""
        cmd = f'robocopy "{source}" "{destination}" /E /Z /MIR'
        success, msg = self.run_cmd(cmd)
        return success


# ==================== 便捷函数（快速使用） ====================
if __name__ == "__main__":
    # 创建全局实例
    fm = FileManager()
    tool_result = fm.run_cmd("dir")
    if tool_result and tool_result[0]:
        print(f"工具执行结果：{tool_result[1]}")

    # def create_dir(path: str) -> bool:
    #     """快速创建目录"""
    #     return fm.create_directory(path)
    #
    #
    # def create_file(path: str, content: str = '') -> bool:
    #     """快速创建文件"""
    #     return fm.create_file(path, content)
    #
    #
    # def read_file(path: str) -> Optional[str]:
    #     """快速读取文件"""
    #     return fm.read_file(path)
    #
    #
    # def write_file(path: str, content: str) -> bool:
    #     """快速写入文件"""
    #     return fm.write_file(path, content)
    #
    #
    # def read_json(path: str) -> Optional[Any]:
    #     """快速读取JSON"""
    #     return fm.read_json(path)
    #
    #
    # def write_json(path: str, data: Any) -> bool:
    #     """快速写入JSON"""
    #     return fm.write_json(path, data)