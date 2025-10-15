import subprocess
from pathlib import Path

from rushclis import print_red
from rushlib.system import SystemConsole


def run_executable(exe_path: Path) -> None:
    try:
        if not exe_path.exists():
            print_red(f"❌ 可执行文件不存在: {exe_path}")
            return

        print(f"🚀 启动程序: {exe_path}")
        if SystemConsole.windows():
            subprocess.Popen([str(f"{exe_path}")], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([str(exe_path)])
    except Exception as e:
        print_red(f"运行程序失败: {str(e)}")