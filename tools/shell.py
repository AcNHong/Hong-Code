import asyncio
import locale
import os
import shlex
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional, Callable, List
from dataclasses import dataclass
from contextlib import asynccontextmanager
import signal
import subprocess


# ============ 数据结构 ============
@dataclass
class ShellCommand:
    """命令执行结果"""
    pid: int
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    background_task_id: Optional[str] = None


class TaskOutput:
    """任务输出管理（类比 TypeScript 版本）"""

    def __init__(self, task_id: str, on_progress: Optional[Callable] = None):
        self.task_id = task_id
        self.on_progress = on_progress
        self.buffer = []

    def write(self, data: str, is_stderr: bool = False):
        self.buffer.append(data)
        if self.on_progress:
            self.on_progress(data, is_stderr)

    def get_output(self) -> str:
        return ''.join(self.buffer)

    def clear(self):
        self.buffer.clear()


# ============ Shell Provider 策略模式 ============
class ShellProvider:
    """Shell 提供者基类"""

    def get_spawn_args(self, command: str) -> List[str]:
        raise NotImplementedError

    @property
    def shell_path(self) -> str:
        raise NotImplementedError

    @property
    def detached(self) -> bool:
        return False

    async def get_environment_overrides(self, command: str) -> dict:
        return {}

    async def build_exec_command(self, command: str, options: dict) -> tuple[str, str]:
        """构建执行命令，返回 (命令字符串, cwd跟踪文件路径)"""
        # 创建临时文件用于工作目录跟踪
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            cwd_file = f.name

        # 构建命令：执行原始命令后输出当前目录
        wrapped_cmd = f"{command}; pwd >| {cwd_file}"  # ← PowerShell 不支持 >|
        return wrapped_cmd, cwd_file


class BashProvider(ShellProvider):
    @property
    def shell_path(self) -> str:
        return "/bin/bash"

    def get_spawn_args(self, command: str) -> List[str]:
        return ["-c", command]

    async def build_exec_command(self, command: str, options: dict) -> tuple[str, str]:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            cwd_file = f.name

        # bash 使用 >| 强制覆盖
        wrapped_cmd = f"{command}; pwd >| {cwd_file}"
        return wrapped_cmd, cwd_file

class PowerShellProvider(ShellProvider):
    @property
    def shell_path(self) -> str:
        if sys.platform == 'win32':
            # 优先使用 Windows PowerShell（系统自带）
            powershell_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
            if Path(powershell_path).exists():
                return powershell_path
        return "pwsh"  # 回退到 PowerShell Core

    def get_spawn_args(self, command: str) -> List[str]:
        return ["-NoProfile", "-NonInteractive", "-Command", command]

    async def build_exec_command(self, command: str, options: dict) -> tuple[str, str]:
        """PowerShell 版本：使用 Out-File 输出目录"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            cwd_file = f.name

        if sys.platform == 'win32':
            # Windows: 使用 Out-File 或 Set-Content
            wrapped_cmd = f"{command}; Get-Location | Out-File -FilePath {cwd_file} -Encoding utf8"
        else:
            # PowerShell on Unix
            wrapped_cmd = f"{command}; pwd > {cwd_file}"

        return wrapped_cmd, cwd_file

# ============ 简化的沙箱管理 ============
class SandboxManager:
    """简化版沙箱（使用 chroot 或 Docker 会更复杂，这里用临时目录隔离）"""

    @staticmethod
    async def wrap_with_sandbox(command: str, shell_path: str, tmp_dir: Path) -> str:
        """
        简化沙箱：在临时目录中执行命令
        生产环境可以用 bubblewrap、Docker 或 chroot
        """
        # 创建隔离的工作目录
        sandbox_home = tmp_dir / "sandbox_home"
        sandbox_home.mkdir(exist_ok=True)

        # 根据 shell 类型选择连接符：bash 用 &&，PowerShell 用 ;
        is_powershell = "powershell" in shell_path.lower()
        separator = ";" if is_powershell else "&&"

        # 包装命令，限制文件系统访问
        wrapped = f"""
cd {sandbox_home} {separator} {command}
        """
        return wrapped.strip()

    @staticmethod
    def cleanup_after_command():
        """清理沙箱残留文件（实际应用中异步删除）"""
        pass


# ============ 主执行器 ============
class ShellExecutor:
    def __init__(self):
        self._cwd = Path.cwd()
        self._original_cwd = Path.cwd()

    def _get_platform(self) -> str:
        return "windows" if os.name == "nt" else "posix"

    async def _recover_cwd(self) -> Path:
        """工作目录恢复机制（对应 TypeScript 的 realpath 验证）"""
        current = self._cwd

        # 验证当前目录是否存在
        if current.exists():
            return current

        # 目录已消失，回退到原始目录
        print(f"Warning: CWD '{current}' no longer exists, recovering to '{self._original_cwd}'")

        if self._original_cwd.exists():
            self._cwd = self._original_cwd
            return self._original_cwd
        else:
            # 完全失败，使用 /tmp 或用户目录
            fallback = Path(tempfile.gettempdir())
            self._cwd = fallback
            return fallback

    async def exec(
            self,
            command: str,
            abort_signal: asyncio.Event = None,  # 类似 AbortSignal
            shell_type: str = None,
            timeout: int = 30,
            on_stdout: Optional[Callable[[str], None]] = None,
            on_stderr: Optional[Callable[[str], None]] = None,
            should_use_sandbox: bool = False,
            prevent_cwd_changes: bool = False,
    ) -> ShellCommand:
        """
        执行 shell 命令（核心方法）

        Args:
            command: 要执行的命令
            abort_signal: 取消信号（asyncio.Event）
            shell_type: "bash" 或 "powershell"
            timeout: 超时时间（秒）
            on_stdout: 实时 stdout 回调
            on_stderr: 实时 stderr 回调
            should_use_sandbox: 是否使用沙箱隔离
            prevent_cwd_changes: 是否阻止工作目录变更
        """
        shell_type = "powershell" if os.name == "nt" else "bash"
        # 1. 选择 Provider
        provider = BashProvider() if shell_type == "bash" else PowerShellProvider()

        # 2. 工作目录恢复
        cwd = await self._recover_cwd()

        # 3. 构建命令（带工作目录跟踪）
        sandbox_tmp_dir = None
        if should_use_sandbox:
            sandbox_tmp_dir = tempfile.mkdtemp(prefix="sandbox_")
            os.chmod(sandbox_tmp_dir, mode=0o700)
            sandbox_tmp_dir = Path(sandbox_tmp_dir)

        command_str, cwd_file = await provider.build_exec_command(command, {
            "sandbox_tmp_dir": sandbox_tmp_dir,
            "use_sandbox": should_use_sandbox,
        })

        # 4. 沙箱包装
        if should_use_sandbox and sandbox_tmp_dir:
            command_str = await SandboxManager.wrap_with_sandbox(
                command_str, provider.shell_path, sandbox_tmp_dir
            )

        # 5. 环境变量设置
        env_overrides = await provider.get_environment_overrides(command)
        env = os.environ.copy()
        env.update({
            "GIT_EDITOR": "true",
            "CLAUDE_CODE": "1",
            **env_overrides
        })

        # 6. 创建子进程
        process = await asyncio.create_subprocess_exec(
            provider.shell_path,
            *provider.get_spawn_args(command_str),
            cwd=str(cwd),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        shell_cmd = ShellCommand(pid=process.pid)

        # 7. 处理输出（实时流式 + 完整收集）
        # 使用系统 locale 编码，解决 Windows 中文系统 GBK 编码乱码问题
        system_encoding = locale.getpreferredencoding() or 'utf-8'

        async def read_stream(stream, callback):
            """读取流：始终收集完整输出，有回调时实时通知"""
            output = []
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode(system_encoding, errors='replace')
                output.append(decoded)
                if callback:
                    callback(decoded.rstrip())
            return ''.join(output)

        # 始终创建 reader 任务，确保管道被消费不阻塞
        stdout_task = asyncio.create_task(read_stream(process.stdout, on_stdout))
        stderr_task = asyncio.create_task(read_stream(process.stderr, on_stderr))

        try:
            # 等待进程结束（带超时）
            try:
                returncode = await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                # 超时处理：终止进程树
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
                raise TimeoutError(f"Command timed out after {timeout}s")

            # 等待 reader 任务完成，收集完整输出
            shell_cmd.stdout = await stdout_task
            shell_cmd.stderr = await stderr_task
            shell_cmd.returncode = returncode

        except asyncio.CancelledError:
            # 类似 abort_signal 的处理
            process.terminate()
            raise
        finally:
            # 清理资源：确保 reader 任务和进程都结束
            for task in [stdout_task, stderr_task]:
                if not task.done():
                    task.cancel()
            if process.returncode is None:
                process.kill()

        # 8. 工作目录更新（读取跟踪文件）
        if not prevent_cwd_changes and Path(cwd_file).exists():
            try:
                with open(cwd_file, 'r') as f:
                    new_cwd = f.read().strip()
                if new_cwd and Path(new_cwd).exists():
                    self._cwd = Path(new_cwd)
            except Exception:
                pass
            finally:
                # 清理临时文件
                try:
                    os.unlink(cwd_file)
                except:
                    pass

        # 9. 沙箱清理
        if should_use_sandbox and sandbox_tmp_dir:
            import shutil
            shutil.rmtree(sandbox_tmp_dir, ignore_errors=True)
            SandboxManager.cleanup_after_command()

        return shell_cmd


# ============ 异步生成器合并器（all 函数） ============
async def all_generators(
        generators: List[AsyncGenerator],
        concurrency_cap: int = 10,
):
    """
    并发执行多个异步生成器，按完成顺序产出结果
    对应 TypeScript 的 all 函数
    """
    from asyncio import Queue

    queue = Queue()
    running = set()

    async def run_generator(gen, index):
        """运行单个生成器"""
        try:
            async for value in gen:
                await queue.put((index, value))
        except Exception as e:
            await queue.put((index, e))
        finally:
            running.remove(asyncio.current_task())
            # 当所有生成器完成时，发送结束信号
            if not running:
                await queue.put(None)

    # 启动初始批次
    for i, gen in enumerate(generators[:concurrency_cap]):
        task = asyncio.create_task(run_generator(gen, i))
        running.add(task)

    # 待启动的生成器队列
    waiting = list(generators[concurrency_cap:])

    # 消费结果
    while running:
        result = await queue.get()
        if result is None:  # 结束信号
            break

        index, value = result
        yield value

        # 如果还有等待的生成器，启动一个
        if waiting:
            gen = waiting.pop(0)
            task = asyncio.create_task(run_generator(gen, index))
            running.add(task)


# ============ 使用示例 ============
async def example_usage():
    """演示如何使用"""
    executor = ShellExecutor()
    shell = "powershell" if os.name == "nt" else "bash"
    # 示例1：简单执行（自动检测平台选择 shell）
    # print("=== 示例1: 执行 echo 命令 ===")

    print(f"使用 shell: {shell}")
    try:
        result = await executor.exec(
            "",
            shell_type=shell,
            timeout=5,
            should_use_sandbox=True,
            on_stdout=lambda x: print(f"[实时] {x}"),
        )
        print(f"返回码: {result.returncode}")
        print(f"stdout: {result.stdout!r}")
        print(f"stderr: {result.stderr!r}")
    except FileNotFoundError as e:
        print(f"错误: shell 不存在 - {e}")
    except Exception as e:
        print(f"执行失败: {type(e).__name__}: {e}")
    #
    # # 示例2：目录列表（跨平台命令）
    # print("\n=== 示例2: 目录列表 ===")
    # # PowerShell: ls 是 Get-ChildItem 的别名，但参数语法不同
    # # bash: ls -la    PowerShell: ls  (不带 -al，因为 -al 是 bash 特有语法)
    # ls_cmd = "ls" if os.name == "nt" else "ls -la"
    # print(f"命令: {ls_cmd}")
    # try:
    #     result = await executor.exec(
    #         ls_cmd,
    #         shell_type=shell,
    #         timeout=5,
    #         on_stdout=lambda x: print(f"[实时] {x}"),
    #     )
    #     print(f"返回码: {result.returncode}")
    #     if result.stdout:
    #         print(f"stdout 行数: {len(result.stdout.splitlines())}")
    #     if result.stderr:
    #         print(f"stderr: {result.stderr[:200]!r}")
    # except FileNotFoundError as e:
    #     print(f"错误: shell 不存在 - {e}")
    # except Exception as e:
    #     print(f"执行失败: {type(e).__name__}: {e}")
    #
    # 示例3：带超时的命令
    # print("\n=== 示例3: 超时控制 ===")
    # try:
    #     await executor.exec("sleep 10",shell_type=shell,timeout=2, on_stdout=lambda x: print(f"[实时] {x}"),)
    # except TimeoutError as e:
    #     print(f"超时: {e}")

    # # 示例4：异步生成器合并
    # print("\n=== 示例4: 并发执行多个异步任务 ===")
    #
    # async def slow_gen(cmd,delay, name):
    #     for i in range(3):
    #         await asyncio.sleep(delay)
    #         result = await executor.exec(
    #                 cmd,
    #                 shell_type=shell,
    #                 timeout=5,
    #                 on_stdout=lambda x,n=name: print(f"[实时] {x}"),
    #             )
    #         yield f"{name},{i}: {result}"
    #
    # gen1 = slow_gen("ls",0.5, "A")
    # gen2 = slow_gen("ipconfig",0.3, "B")
    # gen3 = slow_gen("echo 666",0.7, "C")
    #
    # async for value in all_generators([gen1, gen2, gen3], concurrency_cap=2):
    #     print(f"收到: {value}")


# 运行示例
if __name__ == "__main__":
    # import asyncio
    # import subprocess
    # 创建有名字的临时文件（手动控制删除）
    asyncio.run(example_usage())