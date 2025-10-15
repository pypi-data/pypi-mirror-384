from typing import Optional

from ilbuilder.builder.builder import IlBuilder
from ilbuilder_cli.data import PackageData


class IlBuilderTool(IlBuilder):
    def __init__(self, name, script, icon=None):
        super().__init__(name, script, icon)

    @staticmethod
    def from_data(root: str = ".") -> Optional['IlBuilder']:
        package_config = PackageData(root)

        if not package_config.is_file():
            raise FileNotFoundError(f"{package_config.path} dont exist!")
            return None


        name = package_config.get('name', None)
        venv = package_config.get('venv', '.venv')
        script = package_config.get('main', None)
        console = package_config.get('console', False)
        icon = package_config.get('icon', None)
        onefile = package_config.get('onefile', True)
        auto_run = package_config.get('auto_run', True)
        exclude_commands = package_config.get('exclude_commands', [])

        builder = IlBuilderTool(name, script, icon)

        assets_lst = package_config.get('assets', [])
        if assets_lst:
            for asset in assets_lst:
                builder.add_assets(asset.get("from", []), asset.get("to", "."))

        in_assets_lst = package_config.get('in_assets', [])
        if in_assets_lst:
            for asset in in_assets_lst:
                builder.add_in_assets(asset.get("from", []), asset.get("to", "."))

        builder.set_venv(venv)
        builder.set_onefile(onefile)
        builder.set_exclude_commands(exclude_commands)
        builder.set_auto_run(auto_run)
        builder.set_console(console)

        return builder