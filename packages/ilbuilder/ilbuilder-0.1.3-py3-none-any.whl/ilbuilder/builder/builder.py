import subprocess
from abc import abstractmethod
from pathlib import Path
from typing import Optional, Union

from rushclis import print_red
from rushlib.file import FolderStream, FileStream
from rushlib.path import MPath
from rushlib.system import SystemConsole
from rushlib.venvs.path import venv_path

from ilbuilder.builder import Builder
from ilbuilder.utils import run_executable


class IlBuilder(Builder):
    def __init__(self, name: Optional[str] = None, script_path: Optional[Union[str, Path]] = None,
                 icon: Optional[str] = None) -> None:
        super().__init__(name)
        self._icon = MPath.to_path(icon) if icon else None
        self._script_path = MPath.to_path(script_path)
        self._console = False
        self._onefile = True
        self._assets: dict[str, list[Path]] = {}
        self._in_assets: dict[str, list[Path]] = {}
        self._exclude_commands = []

        self._auto_run = True

    @property
    def icon(self) -> Path:
        return self._icon

    @property
    def script_path(self) -> Optional[Union[str, Path]]:
        return self._script_path

    @property
    def console(self) -> bool:
        return self._console

    @property
    def onefile(self) -> bool:
        return self._onefile

    @property
    def assets(self) -> dict[str, list[Path]]:
        return self._assets

    @property
    def in_assets(self) -> dict[str, list[Path]]:
        return self._in_assets

    @property
    def auto_run(self) -> bool:
        return self._auto_run

    @staticmethod
    @abstractmethod
    def from_data(root: str) -> Optional['IlBuilder']:
        pass

    def set_script_path(self, path: Union[str, Path]) -> "IlBuilder":
        if not path == self.script_path:
            self._script_path = path
        return self

    def set_console(self, console) -> "IlBuilder":
        if not console == self.console:
            self._console = console
        return self

    def set_onefile(self, onefile) -> "IlBuilder":
        if not onefile == self.onefile:
            self._onefile = onefile
        return self

    def set_exclude_commands(self, exclude_commands: list[str]) -> "IlBuilder":
        self._exclude_commands = exclude_commands
        return self

    def add_assets(self, sources: list[Union[str, Path]], target_relative_path: str = "") -> "Builder":
        if not sources:
            return self

        source_paths = [Path(source) for source in sources]

        self.assets.setdefault(target_relative_path, [])

        for source in source_paths:
            if not source.exists():
                print_red(f"警告: 资源源不存在: {source}")
            else:
                self.assets[target_relative_path].append(source)

        return self

    def add_in_assets(self, sources: list[Union[str, Path]], target_relative_path: str = "") -> "Builder":
        if not sources:
            return self

        source_paths = [Path(source) for source in sources]

        self.in_assets.setdefault(target_relative_path, [])

        for source in source_paths:
            if not source.exists():
                print_red(f"警告: 内部资源源不存在: {source}")
            else:
                self.in_assets[target_relative_path].append(source)

        return self

    def set_auto_run(self, auto_run: bool) -> "IlBuilder":
        if not auto_run == self._auto_run:
            self._auto_run = auto_run

        return self

    def _validate(self) -> bool:
        if not self.script_path or not self.script_path.is_file():
            raise ValueError(f"脚本文件不存在: {self.script_path}")

        if self.icon and not self.icon.is_file():
            raise ValueError(f"图标文件不存在: {self.icon}")

        return True

    def _get_add_data_args(self) -> list[str]:
        add_data_args = []
        separator = ";" if SystemConsole.windows() else ":"

        for target_relative, sources in self.in_assets.items():
            for source in sources:
                abs_source = source.resolve()

                out = Path(target_relative)

                if source.is_dir():
                    out /= source

                arg = f"{abs_source}{separator}{out}"
                add_data_args.extend(["--add-data", arg])

        return add_data_args

    def _copy_assets(self) -> bool:
        if not self._assets:
            return True

        print("\n📦 复制外部资源...")
        success = True

        for target_relative, sources in self.assets.items():
            target_path = self.project_dir / target_relative

            for source in sources:
                target_folder = FolderStream(str(target_path / source))
                FolderStream(source).copy(target_folder)

        return success

    def _cmd(self, python_path) -> list[str]:
        cmd = [str(python_path).strip(), '-m', 'PyInstaller', '--noconfirm']

        if self.onefile:
            cmd.append('--onefile')
        else:
            cmd.append('--onedir')

        if not self.console:
            cmd.append('--noconsole')

        if self.icon:
            cmd.extend(['--icon', str(self.icon.resolve())])

        cmd.extend(self._get_add_data_args())
        cmd.extend(['--name', self.name, str(self.script_path.resolve())])
        cmd.extend(self._exclude_commands)

        return cmd

    def _tip_start(self):
        print(f"\n🔨 开始打包项目: {self.name}")
        print(f"📜 脚本路径: {self.script_path}")
        self._tip()

    def _tip_end(self, target_path):
        print(f"\n🎉 项目构建成功!")
        print(f"📂 输出目录: {self.project_dir}")
        print(f"📦 输出文件: {target_path}")
        self._tip()

    def _tip(self):
        print(f"📦 单文件打包: {'✅' if self.onefile else '❌'}")
        print(f"🖥️ 显示控制台: {'✅' if self.console else '❌'}")
        print(f"🚀 自动运行: {'✅' if self.auto_run else '❌'}")

    def _tip_assets(self):
        if self.in_assets:
            print("📦 要嵌入的内部资源:")
            for target_relative, sources in self.in_assets.items():
                for source in sources:
                    print(f"  ➡️ {source} -> {target_relative}")

    def _start_build(self, cmd):
        self._tip_start()
        self._tip_assets()
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            check=True
        )

    def build(self):
        python_path = venv_path(self.venv)

        FolderStream(self.project_dir).create()

        try:
            vali = self._validate()
            self._start_build(self._cmd(python_path))

            if self.onefile:
                source_path = Path('dist') / f"{SystemConsole.exe(self.name)}"
            else:
                source_path = Path('dist') / self.name

            copy = FileStream(source_path).copy(self.project_dir)

            target_path = self.project_dir / f"{SystemConsole.exe(self.name)}"

            self._tip_end(target_path)
            assets = self._copy_assets()

            if self._auto_run:
                print(f"\n🚀 正在启动应用程序...")
                run_executable(target_path)

            print("✅ 打包成功")

            return vali and copy and assets

        except subprocess.CalledProcessError as e:
            print("\n❌ ", end="")
            print_red(f"打包失败! 错误代码: {e.returncode}")
            return False
        except Exception as e:
            print("\n❌ ", end="")
            print_red(f"{str(e)}")
            return False
